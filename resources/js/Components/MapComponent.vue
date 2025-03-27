<script setup>
import { onMounted, ref, inject, defineExpose } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import axios from 'axios';

// Get the global dark mode state
const isDarkMode = inject('isDarkMode', ref(false));

// Map container and instance
const mapContainer = ref(null);
const map = ref(null);
const pinsList = ref([]); // Stores the list of pins

// Mapbox token
const mapboxToken = 'pk.eyJ1IjoiMS1heWFub24iLCJhIjoiY20ycnAzZW5pMWZpZTJpcThpeTJjdDU1NCJ9.7AVb_LJf6sOtb-QAxwR-hg';

// Get the CSRF token from the meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

// Set the CSRF token as a common header for all Axios requests
axios.defaults.headers.common['X-CSRF-TOKEN'] = csrfToken;

// Initialize the map
async function initializeMap() {
  if (!mapContainer.value) return;

  mapboxgl.accessToken = mapboxToken;

  // Initialize Mapbox map
  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: isDarkMode.value ? 'mapbox://styles/mapbox/dark-v10' : 'mapbox://styles/1-ayanon/cm2rp9idm00as01qwcq9ihoyr',
    center: [121.039295, 14.631141],
    zoom: 15.5,
    attributionControl: false,
  });

  // Add navigation control
  map.value.addControl(new mapboxgl.NavigationControl(), 'top-right');

  // Add scale control
  map.value.addControl(new mapboxgl.ScaleControl(), 'bottom-left');

  // Set up map click handler for pin placement
  map.value.on('click', handleMapClick);

  // Wait for map to load
  map.value.on('load', async () => {
    // Fetch initial pins
    await fetchPins();
  });
}

// Call initializeMap when component is mounted
onMounted(() => {
  console.log('MapComponent mounted, initializing map...');
  initializeMap();
});

// State for pin placement mode
const isPlacingCameraPin = ref(false);
const selectedCameraForPin = ref(null);
const placementCallback = ref(null);

// Enter camera pin placement mode
function startCameraPinPlacement(cameraInfo) {
  if (!map.value) return;
  
  selectedCameraForPin.value = cameraInfo;
  isPlacingCameraPin.value = true;
  
  // Change cursor style to indicate placement mode
  map.value.getCanvas().style.cursor = 'crosshair';
  
  // Show instruction message to the user
  console.log('Click on the map to place the camera pin');
}

// Exit camera pin placement mode
function cancelCameraPinPlacement() {
  if (!map.value) return;
  
  selectedCameraForPin.value = null;
  isPlacingCameraPin.value = false;
  
  // Reset cursor style
  map.value.getCanvas().style.cursor = '';
}

// Setup click handler for the map
let mapClickHandler = null;

// Function to enable camera pin placement mode
function enablePinPlacementMode(callback) {
  console.log('Entering pin placement mode...');
  
  if (!map.value) {
    console.error('Map instance not available, cannot enter pin placement mode');
    throw new Error('Map not initialized');
  }
  
  // Set cursor to crosshair to indicate placement mode
  map.value.getCanvas().style.cursor = 'crosshair';
  
  // Store current state
  isPlacingCameraPin.value = true;
  placementCallback.value = callback;
  
  console.log('Pin placement mode enabled, waiting for user click...');
}

// Disable pin placement mode
function disablePinPlacementMode() {
  console.log('Exiting pin placement mode...');
  
  if (map.value) {
    // Reset cursor
    map.value.getCanvas().style.cursor = '';
  }
  
  // Reset state
  isPlacingCameraPin.value = false;
  placementCallback.value = null;
  
  console.log('Pin placement mode disabled');
}

// Handle map click during pin placement mode
function handleMapClick(e) {
  console.log('Map clicked at coordinates:', e.lngLat, 'Placement mode active:', isPlacingCameraPin.value, 'Callback registered:', !!placementCallback.value);
  
  if (isPlacingCameraPin.value && placementCallback.value) {
    console.log('✅ Pin placement mode is active and callback is registered');
    
    // Format coordinates in both object and array formats
    const coordinates = {
      lat: e.lngLat.lat,
      lng: e.lngLat.lng
    };
    
    console.log('Calling pin placement callback with coordinates:', coordinates);
    
    // Call the callback with the clicked coordinates
    placementCallback.value(coordinates);
  } else if (isPlacingCameraPin.value && !placementCallback.value) {
    console.error('⚠️ Pin placement mode is active but no callback is registered');
  }
}

// Fetch pins from the backend
async function fetchPins() {
  try {
    const response = await axios.get('/pins');
    const pins = response.data;

    pins.forEach((pin) => {
      const marker = addMarker(pin.coordinates, pin.animal_type, { id: pin.id });
      pinsList.value.push({
        id: pin.id,
        coordinates: pin.coordinates,
        animalType: pin.animal_type,
        marker: marker
      });
    });
  } catch (error) {
    console.error('Error fetching pins:', error);
  }
}

// Create a marker based on pin type and data
function createMarker(pinData) {
  try {
    if (!map.value) {
      console.error('Map is not initialized, cannot create marker');
      return null;
    }
    
    // Get coordinates in the format mapbox expects [lng, lat]
    let mapboxCoords;
    
    if (Array.isArray(pinData.coordinates) && pinData.coordinates.length >= 2) {
      // Already in [lng, lat] format
      mapboxCoords = pinData.coordinates;
    } else if (pinData.lat !== undefined && pinData.lng !== undefined) {
      // Object with lat/lng properties
      mapboxCoords = [pinData.lng, pinData.lat];
    } else {
      console.error('Invalid coordinates format for marker:', pinData.coordinates);
      return null;
    }
    
    // Create element based on pin type
    const marker = document.createElement('div');
    marker.className = 'custom-marker';
    
    // Apply specific styles based on type
    const pinType = pinData.type || pinData.animalType || 'Default';
    
    if (pinType === 'Camera' || pinData.isCamera) {
      marker.className = 'custom-marker camera-marker';
      marker.innerHTML = '<i class="fas fa-video"></i>';
    } else if (pinType === 'Dog') {
      marker.style.backgroundColor = '#38a3a5'; // Dog color
    } else if (pinType === 'Cat') {
      marker.style.backgroundColor = '#57cc99'; // Cat color
    } else {
      marker.style.backgroundColor = '#4f6642'; // Default color
    }
    
    // Create marker instance
    const markerInstance = new mapboxgl.Marker(marker).setLngLat(mapboxCoords);
    
    // Create popup content based on pin type
    let popupHTML = '';
    
    if (pinType === 'Camera' || pinData.isCamera) {
      // Camera pin popup
      popupHTML = `
        <div class="camera-popup">
          <h3>${pinData.cameraName || pinData.name || 'Camera'}</h3>
          <p>${pinData.location || 'Location not specified'}</p>
          <p><small>Status: ${pinData.status || 'Unknown'}</small></p>
          ${pinData.id ? `<button class="delete-pin-btn" data-pin-id="${pinData.id}">Delete Pin</button>` : ''}
        </div>
      `;
    } else {
      // Animal pin popup
      popupHTML = `
        <div class="pin-popup">
          <h3>${pinType}</h3>
          ${pinData.description ? `<p>${pinData.description}</p>` : ''}
          ${pinData.id ? `<button class="delete-pin-btn" data-pin-id="${pinData.id}">Delete Pin</button>` : ''}
        </div>
      `;
    }
    
    // Create and attach popup
    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(popupHTML);
    markerInstance.setPopup(popup);
    
    // Add click handler for delete button
    popup.on('open', () => {
      setTimeout(() => {
        const deleteBtn = document.querySelector(`.delete-pin-btn[data-pin-id="${pinData.id}"]`);
        if (deleteBtn) {
          deleteBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this pin?')) {
              deletePin(pinData.id, markerInstance);
            }
          });
        }
      }, 100);
    });
    
    // Add marker to map
    markerInstance.addTo(map.value);
    
    return markerInstance;
  } catch (error) {
    console.error('Error creating marker:', error);
    return null;
  }
}

// Add markers to the map
function addMarker(coordinates, animalType, details = {}) {
  // Create a custom marker element
  const marker = document.createElement('div');
  marker.className = 'custom-marker';
  
  // Set different colors based on type
  if (animalType === 'Camera') {
    marker.className = 'custom-marker camera-marker';
    marker.innerHTML = '<i class="fas fa-video"></i>';
  } else if (animalType === 'Dog') {
    marker.style.backgroundColor = '#38a3a5'; // Dog color
  } else if (animalType === 'Cat') {
    marker.style.backgroundColor = '#57cc99'; // Cat color
  } else {
    marker.style.backgroundColor = '#4f6642'; // Default color
  }

  // Create the marker instance
  const markerInstance = new mapboxgl.Marker(marker).setLngLat(coordinates);
  
  // Add popup for camera markers
  if (animalType === 'Camera' && details.cameraName) {
    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
      <div class="camera-popup">
        <h3>${details.cameraName}</h3>
        <p>${details.location || 'Location not specified'}</p>
        <p><small>Click to view camera feed</small></p>
        ${details.id ? `<button class="delete-pin-btn" data-pin-id="${details.id}">Delete Pin</button>` : ''}
      </div>
    `);
    
    markerInstance.setPopup(popup);
    
    // Add click event to open camera feed or delete
    marker.addEventListener('click', (e) => {
      if (e.target.closest('.delete-pin-btn')) {
        // Handle delete button click
        const pinId = e.target.closest('.delete-pin-btn').dataset.pinId;
        if (confirm('Are you sure you want to delete this pin?')) {
          deletePin(pinId, markerInstance);
        }
      } else if (details.hlsUrl) {
        // Open camera feed
        window.open(details.hlsUrl, '_blank');
      }
    });
  } else {
    // For non-camera markers, add a simpler popup with delete option
    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
      <div class="pin-popup">
        <h3>${animalType}</h3>
        ${details.id ? `<button class="delete-pin-btn" data-pin-id="${details.id}">Delete Pin</button>` : ''}
      </div>
    `);
    
    markerInstance.setPopup(popup);
    
    // Add click event for delete button
    popup.on('open', () => {
      setTimeout(() => {
        const deleteBtn = document.querySelector(`.delete-pin-btn[data-pin-id="${details.id}"]`);
        if (deleteBtn) {
          deleteBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this pin?')) {
              deletePin(details.id, markerInstance);
            }
          });
        }
      }, 100);
    });
  }
  
  // Add the marker to the map
  markerInstance.addTo(map.value);
  
  return markerInstance;
}

// Delete a pin from the map and database
async function deletePin(pinId, markerInstance) {
  try {
    console.log('Deleting pin with ID:', pinId);
    
    // Remove from map
    if (markerInstance) {
      markerInstance.remove();
    }
    
    // Remove from local list
    const pinIndex = pinsList.value.findIndex(pin => pin.id === pinId);
    if (pinIndex !== -1) {
      pinsList.value.splice(pinIndex, 1);
    }
    
    // Remove from database
    const response = await axios.delete(`/pins/${pinId}`);
    
    if (response.data.success) {
      console.log('Pin deleted successfully');
    } else {
      console.error('Failed to delete pin:', response.data.message);
    }
  } catch (error) {
    console.error('Error deleting pin:', error);
  }
}

// Get all camera pin locations from the map
async function getCameraPinLocations() {
  try {
    console.log('Retrieving camera pin locations...');
    
    if (!map.value) {
      console.error('Map not initialized, cannot retrieve camera pins');
      return [];
    }
    
    // We'll collect all camera pins from our pinsList
    const cameraPins = [];
    
    // Iterate through the pinsList to find camera pins
    for (const pin of pinsList.value) {
      if (pin.isCamera || pin.animalType === 'Camera') {
        console.log('Found camera pin:', pin);
        
        // Extract camera information
        const cameraInfo = {
          id: pin.cameraId || pin.id,
          name: pin.cameraName || pin.name || 'Unknown Camera',
          location: pin.location || 'Unknown Location'
        };
        
        // Handle coordinates in different formats
        let coordinates = null;
        
        // Check if coordinates exist as an object with lat/lng
        if (pin.coordinates && typeof pin.coordinates === 'object') {
          if ('lat' in pin.coordinates && 'lng' in pin.coordinates) {
            coordinates = {
              lat: pin.coordinates.lat,
              lng: pin.coordinates.lng
            };
          } 
          // Check if coordinates exist as an array [lng, lat]
          else if (Array.isArray(pin.coordinates) && pin.coordinates.length >= 2) {
            coordinates = {
              lat: pin.coordinates[1],
              lng: pin.coordinates[0]
            };
          }
        }
        // Check if lat and lng exist as direct properties
        else if (pin.lat !== undefined && pin.lng !== undefined) {
          coordinates = {
            lat: pin.lat,
            lng: pin.lng
          };
        }
        
        // Only add if we have valid coordinates
        if (coordinates) {
          cameraPins.push({
            id: cameraInfo.id,
            name: cameraInfo.name,
            location: cameraInfo.location,
            coordinates: coordinates
          });
        } else {
          console.warn(`No valid coordinates found for camera: ${cameraInfo.name}`);
        }
      }
    }
    
    console.log('Retrieved camera pin locations:', cameraPins);
    return cameraPins;
  } catch (error) {
    console.error('Error retrieving camera pin locations:', error);
    return [];
  }
}

// Allow adding a camera pin to the map - exposed for parent components
async function addCameraPin(coordinates, cameraInfo) {
  let markerInstance = null;
  
  try {
    console.log('Adding camera pin at coordinates:', coordinates, 'with camera info:', cameraInfo);
    
    // Validate coordinates
    let validCoords;
    
    // Handle different coordinate formats
    if (Array.isArray(coordinates) && coordinates.length === 2) {
      // Array format [lng, lat]
      validCoords = coordinates;
    } else if (coordinates && typeof coordinates === 'object') {
      // Object format {lat, lng}
      if ('lat' in coordinates && 'lng' in coordinates) {
        validCoords = [coordinates.lng, coordinates.lat];
      } else {
        throw new Error('Invalid coordinates object. Expected {lat, lng} format');
      }
    } else {
      throw new Error('Invalid coordinates format. Expected [longitude, latitude] array or {lat, lng} object');
    }
    
    // Create pin object with all camera data
    const pin = {
      id: cameraInfo.id || `camera-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      coordinates: validCoords,
      lat: Array.isArray(validCoords) ? validCoords[1] : validCoords.lat,
      lng: Array.isArray(validCoords) ? validCoords[0] : validCoords.lng,
      cameraId: cameraInfo.id || '',
      name: cameraInfo.name || 'Unnamed Camera',
      cameraName: cameraInfo.name || 'Unnamed Camera',
      location: cameraInfo.location || 'Unknown Location',
      videoSrc: cameraInfo.videoSrc || [],
      type: 'Camera',
      isCamera: true,
      status: 'active',
      cameraData: { ...cameraInfo }
    };
    
    // Create marker using our helper function
    markerInstance = createMarker(pin);
    console.log('Marker instance created:', markerInstance);
    
    try {
      console.log('Sending API request to save camera pin...');
      
      const payload = {
        coordinates: validCoords,
        camera_id: cameraInfo.id || '',
        camera_name: cameraInfo.name || '',
        hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : ''
      };
      
      console.log('Sending formatted payload to API:', payload);
      
      const response = await axios.post('/camera-pin', payload, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });
      
      if (!response.data || response.data.success === false) {
        throw new Error(response.data?.message || 'Unknown API error');
      }
      
      console.log("Camera pin API response:", response.data);
      
      // Update pin with backend ID if provided
      if (response.data && response.data.id) {
        pin.id = response.data.id;
      }
      
      // Add to local pins list with all data
      pinsList.value.push(pin);
      
      console.log("Camera pin added successfully:", response.data);
      return {
        success: true,
        message: 'Camera pin added successfully',
        pin: pin,
        response: response.data
      };
    } catch (apiError) {
      console.error('API Error when adding camera pin:', apiError);
      
      // Still add to pins list to maintain visual state
      pinsList.value.push(pin);
      
      console.log("Camera pin added visually but failed to save to backend");
      return { 
        success: false, 
        message: 'Pin added visually but failed to save to server',
        error: apiError.message,
        pin: pin
      };
    }
  } catch (error) {
    console.error('Error in addCameraPin function:', error);
    
    if (markerInstance) {
      console.log('Keeping marker instance despite error to maintain visual state');
    }
    
    throw error;
  }
}

// Add an animal pin to the map - exposed for parent components
async function addAnimalPin(pinData) {
  let markerInstance = null;
  
  try {
    console.log('Adding animal pin with data:', pinData);
    
    if (!map.value) {
      throw new Error('Map not initialized');
    }
    
    // Validate required fields
    if (!pinData.lat || !pinData.lng || !pinData.animal_type) {
      throw new Error('Missing required pin data (lat, lng, animal_type)');
    }
    
    // Create a standardized pin object
    const pin = {
      id: pinData.id || `pin-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      coordinates: [pinData.lng, pinData.lat],
      lat: pinData.lat,
      lng: pinData.lng,
      animalType: pinData.animal_type,
      description: pinData.description || '',
      imageUrl: pinData.image_url || null,
      isCamera: false,
      status: 'active',
      isAutomated: !!pinData.is_automated
    };
    
    // Add marker to the map using our helper
    markerInstance = createMarker(pin);
    
    // Add pin to local list
    pinsList.value.push(pin);
    
    // If this is from automated detection, don't try to save to backend
    if (pinData.is_automated) {
      console.log('Animal pin added (automated detection - not saving to backend)');
      return { 
        success: true, 
        message: 'Automated detection pin added (visual only)',
        pin: pin
      };
    }
    
    // Try to save to backend
    try {
      // Create data to send to the backend
      const formData = new FormData();
      formData.append('coordinates[0]', pin.lng);
      formData.append('coordinates[1]', pin.lat);
      formData.append('animal_type', pin.animalType);
      
      if (pin.description) {
        formData.append('description', pin.description);
      }
      
      if (pinData.image) {
        formData.append('image', pinData.image);
      }
      
      // Send the data to the backend
      const response = await axios.post('/pin', formData);
      
      console.log("Animal pin saved to backend:", response.data);
      
      // Update pin ID if returned from backend
      if (response.data && response.data.id) {
        const pinIndex = pinsList.value.findIndex(p => p.id === pin.id);
        if (pinIndex !== -1) {
          pinsList.value[pinIndex].id = response.data.id;
        }
      }
      
      return {
        success: true,
        message: 'Pin added successfully',
        pin: pin,
        response: response.data
      };
    } catch (apiError) {
      console.error('API Error when saving animal pin:', apiError);
      
      return { 
        success: false, 
        message: 'Pin added visually but failed to save to server',
        error: apiError.message,
        pin: pin
      };
    }
  } catch (error) {
    console.error('Error in addAnimalPin function:', error);
    
    // Don't remove the marker if it was created
    if (markerInstance) {
      console.log('Keeping animal marker despite error');
    }
    
    throw error;
  }
}

// Expose these methods to parent components
defineExpose({
  addMarker,
  addAnimalPin,
  addCameraPin,
  deletePin,
  enablePinPlacementMode,
  disablePinPlacementMode,
  getCameraPinLocations,
  refreshMap: () => {
    if (map.value) {
      map.value.resize();
    }
  },
  getCurrentMapCenter: () => map.value ? map.value.getCenter() : null,
});
</script>

<template>
  <div class="map-container-wrapper">
    <div class="map-container" ref="mapContainer"></div>
  </div>
</template>

<style>
.map-container {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  margin-bottom: 100px;
  overflow: hidden;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

/* Marker styles */
.custom-marker {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
  border: 2px solid white;
  transition: transform 0.2s ease;
}

.custom-marker:hover {
  transform: scale(1.2);
  cursor: pointer;
}

/* Popup styles */
.mapboxgl-popup-content {
  padding: 12px;
  border-radius: 8px;
}

.camera-popup h3,
.pin-popup h3 {
  color:black;
  font-size: 16px;
  font-weight: 600;
}

.delete-pin-btn {
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 5px 10px;
  margin-top: 10px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.2s;
}

.delete-pin-btn:hover {
  background-color: #d32f2f;
}
</style>
