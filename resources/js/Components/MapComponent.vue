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
    
    const coordinates = [e.lngLat.lng, e.lngLat.lat];
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
    
    // Find the pin in the local list
    const pinIndex = pinsList.value.findIndex(pin => pin.id === pinId);
    const pin = pinIndex !== -1 ? pinsList.value[pinIndex] : null;
    
    // If it's a camera pin, remove its perception range circle and label
    if (pin && (pin.isCamera || pin.type === 'Camera')) {
      // Remove perception range circle and label if they exist
      const circleId = `perception-circle-${pinId}`;
      const sourceId = `perception-source-${pinId}`;
      const labelId = `${circleId}-label`;
      
      if (map.value.getLayer(labelId)) {
        map.value.removeLayer(labelId);
      }
      
      if (map.value.getLayer(circleId)) {
        map.value.removeLayer(circleId);
      }
      
      if (map.value.getSource(sourceId)) {
        map.value.removeSource(sourceId);
      }
      
      console.log(`Removed perception range circle and label for camera pin ${pinId}`);
    }
    
    // Remove from local list
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
    
    // Extract perception range if provided
    const perceptionRange = cameraInfo.perceptionRange || 30; // default to 30m
    
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
      perceptionRange: perceptionRange,
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
        hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : '',
        perception_range: perceptionRange
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
        
        // Update perception range circle ID if needed
        if (map.value.getLayer(`perception-circle-${pin.id}`)) {
          // Original circle was created with a temporary ID, need to recreate with new ID
          addPerceptionRangeCircle(validCoords, perceptionRange, pin.id);
        }
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
async function addAnimalPin(coordinates, animalType, details = {}) {
  let markerInstance = null;
  
  try {
    console.log('Adding animal pin at coordinates:', coordinates, 'with type:', animalType);
    
    // Add the marker visually to the map
    markerInstance = addMarker(coordinates, animalType, details);
    
    // Create data to send to the backend
    const formData = new FormData();
    formData.append('coordinates[0]', coordinates[0]);
    formData.append('coordinates[1]', coordinates[1]);
    formData.append('animal_type', animalType);
    
    if (details.description) {
      formData.append('description', details.description);
    }
    
    if (details.image) {
      formData.append('image', details.image);
    }
    
    // Send the data to the backend
    try {
      const response = await axios.post('/api/animal-pin', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': 'Bearer StraySafeTeam3' // Static token for API authentication
        }
      });
      
      // Add to local pins list
      pinsList.value.push({
        coordinates: coordinates,
        animalType: animalType,
        description: details.description,
        imageUrl: details.imageUrl
      });
      
      console.log("Animal pin added successfully:", response.data);
      return response.data;
    } catch (apiError) {
      console.error('API Error when adding animal pin:', apiError);
      
      // Still add the pin to the local list to maintain visual state
      pinsList.value.push({
        coordinates: coordinates,
        animalType: animalType,
        description: details.description,
        imageUrl: details.imageUrl,
        isSyncPending: true // Mark as pending sync with backend
      });
      
      return { 
        success: false, 
        message: 'Pin added visually but failed to save to server',
        error: apiError.message
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
      
      // Add perception range visualization if specified
      if (pinData.perceptionRange) {
        addPerceptionRangeCircle(mapboxCoords, pinData.perceptionRange, pinData.id);
      }
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
          ${pinData.perceptionRange ? `<p><small>Perception Range: ${pinData.perceptionRange}m</small></p>` : ''}
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

// Add a perception range circle to the map for a camera
function addPerceptionRangeCircle(coordinates, rangeInMeters, cameraId) {
  // Generate a unique ID for this range circle
  const circleId = `perception-circle-${cameraId || Date.now()}`;
  const sourceId = `perception-source-${cameraId || Date.now()}`;
  
  try {
    if (!map.value) {
      console.error('Map not initialized, cannot add perception range');
      return;
    }
    
    console.log(`Adding perception range circle of ${rangeInMeters}m for camera at`, coordinates);
    
    // Check if map is already loaded
    if (!map.value.isStyleLoaded()) {
      console.log('Map style not yet loaded, waiting...');
      map.value.once('style.load', () => {
        addPerceptionRangeCircle(coordinates, rangeInMeters, cameraId);
      });
      return;
    }
    
    // Remove any existing circles for this camera
    if (map.value.getLayer(circleId)) {
      map.value.removeLayer(circleId);
    }
    
    if (map.value.getSource(sourceId)) {
      map.value.removeSource(sourceId);
    }
    
    // Convert meters to approximate degrees (rough calculation)
    // 1 degree is about 111km at equator, so 1m is roughly 0.000009 degrees
    const radiusInDegrees = rangeInMeters * 0.000009;
    
    // Add a new source for this circle
    map.value.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: coordinates
        },
        properties: {
          camera_id: cameraId
        }
      }
    });
    
    // Add a circle layer using the source
    map.value.addLayer({
      id: circleId,
      type: 'circle',
      source: sourceId,
      paint: {
        'circle-radius': {
          stops: [
            [10, 10], // At zoom level
            [20, radiusInDegrees * 10000] // Use a multiplier to make it visible
          ],
          base: 2
        },
        'circle-color': 'rgba(66, 133, 244, 0.2)',
        'circle-stroke-width': 1,
        'circle-stroke-color': 'rgba(66, 133, 244, 0.6)'
      }
    });
    
    // Store the circle information for later removal if needed
    const circleInfo = {
      circleId: circleId,
      sourceId: sourceId,
      cameraId: cameraId,
      coordinates: coordinates,
      radius: rangeInMeters
    };
    
    return circleInfo;
  } catch (error) {
    console.error('Error adding perception range circle:', error);
    return null;
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
          location: pin.location || 'Unknown Location',
          perceptionRange: pin.perceptionRange || 30 // Include perception range, default to 30m
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
            coordinates: coordinates,
            perceptionRange: cameraInfo.perceptionRange
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
