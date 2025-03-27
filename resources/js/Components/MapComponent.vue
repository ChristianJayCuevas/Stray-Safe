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
    
    // Create coordinates object in the format expected by our functions
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

// Allow adding a camera pin to the map - exposed for parent components
async function addCameraPin(coordinates, cameraInfo) {
  try {
    console.log('Adding camera pin at coordinates:', coordinates, 'Camera info:', cameraInfo);
    
    // Create a pin object with camera data
    const pin = {
      lat: coordinates.lat,
      lng: coordinates.lng,
      isCamera: true,
      cameraId: cameraInfo.id,
      name: cameraInfo.name || 'Unnamed Camera',
      location: cameraInfo.location || 'Unknown Location',
      status: 'active',
      cameraData: cameraInfo // Store the full camera data
    };
    
    // Add to pins list
    pinsList.value.push(pin);
    
    // Create the marker on the map
    createMarker(pin);
    
    // Try to save to the backend
    try {
      const response = await axios.post('/camera-pin', {
        lat: coordinates.lat,
        lng: coordinates.lng,
        name: cameraInfo.name,
        location: cameraInfo.location,
        camera_id: cameraInfo.id,
        is_camera: true
      });
      
      console.log('Camera pin saved to backend:', response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to save camera pin to backend:', error);
      // Return partial success - marker is visible but not saved
      return {
        success: false,
        error: error.message || 'Failed to save camera pin to server',
        visual_success: true
      };
    }
  } catch (error) {
    console.error('Error in addCameraPin:', error);
    throw error;
  }
}

// Function to add an animal pin to the map
async function addAnimalPin(pinData) {
  try {
    console.log('Adding animal pin:', pinData);
    
    // Validate required fields
    if (!pinData || !pinData.lat || !pinData.lng || !pinData.animal_type) {
      throw new Error('Missing required pin data (lat, lng, animal_type)');
    }
    
    // Create pin object
    const pin = {
      ...pinData,
      isCamera: false,
      status: 'active',
    };
    
    // Add to pins list
    pinsList.value.push(pin);
    
    // Create marker on map
    createMarker(pin);
    
    // Save to backend if not an automated detection
    if (!pinData.is_automated) {
      try {
        const response = await axios.post('/pin', {
          lat: pinData.lat,
          lng: pinData.lng,
          animal_type: pinData.animal_type,
          description: pinData.description || `${pinData.animal_type} sighting`,
          image_url: pinData.image_url,
          // Include other fields as needed
        });
        
        console.log('Animal pin saved to backend:', response.data);
        return response.data;
      } catch (error) {
        console.error('Failed to save animal pin to backend:', error);
        return {
          success: false,
          error: error.message || 'Failed to save animal pin to server',
          visual_success: true
        };
      }
    } else {
      // For automated detections, just return success
      return {
        success: true,
        visual_success: true,
        automated: true
      };
    }
  } catch (error) {
    console.error('Error in addAnimalPin:', error);
    throw error;
  }
}

// Add this method to the component to retrieve camera pin locations
async function getCameraPinLocations() {
  console.log('Getting camera pin locations');
  const cameraPins = [];
  
  // Check if map is initialized
  if (!map.value) {
    console.warn('Map is not initialized yet');
    return cameraPins;
  }
  
  try {
    // Loop through all markers on the map to find camera markers
    // Since Mapbox doesn't provide a direct way to get all markers,
    // we'll use our pinsList to find all camera pins
    pinsList.value.forEach(pin => {
      if (pin.animalType === 'Camera' || pin.isCamera) {
        let cameraId = null;
        let name = 'Unknown Camera';
        let location = 'Unknown Location';
        
        // Extract camera info from various possible structures
        if (pin.cameraId) {
          cameraId = pin.cameraId;
        } else if (pin.details && pin.details.id) {
          cameraId = pin.details.id;
        }
        
        if (pin.name) {
          name = pin.name;
        } else if (pin.cameraName) {
          name = pin.cameraName;
        } else if (pin.details && pin.details.cameraName) {
          name = pin.details.cameraName;
        }
        
        if (pin.location) {
          location = pin.location;
        } else if (pin.details && pin.details.location) {
          location = pin.details.location;
        }
        
        // Get coordinates depending on how they're stored
        let coordinates;
        if (pin.coordinates) {
          // Handle array format [lng, lat]
          if (Array.isArray(pin.coordinates)) {
            coordinates = {
              lat: pin.coordinates[1],
              lng: pin.coordinates[0]
            };
          } else {
            // Handle object format { lat, lng }
            coordinates = pin.coordinates;
          }
        } else if (pin.lat !== undefined && pin.lng !== undefined) {
          coordinates = {
            lat: pin.lat,
            lng: pin.lng
          };
        } else if (pin.marker && typeof pin.marker.getLngLat === 'function') {
          const lngLat = pin.marker.getLngLat();
          coordinates = {
            lat: lngLat.lat,
            lng: lngLat.lng
          };
        }
        
        if (coordinates) {
          cameraPins.push({
            id: cameraId,
            coordinates: coordinates,
            name: name,
            location: location
          });
        }
      }
    });
    
    console.log('Found camera pins:', cameraPins);
    return cameraPins;
  } catch (error) {
    console.error('Error retrieving camera pin locations:', error);
    return [];
  }
}

// Helper function to create a marker on the map
function createMarker(pin) {
  if (!map.value) {
    console.error('Map not initialized');
    return null;
  }
  
  try {
    // Determine marker style based on pin type
    let markerElement = document.createElement('div');
    
    if (pin.isCamera) {
      // Camera marker
      markerElement.className = 'camera-marker';
      markerElement.innerHTML = '<i class="fas fa-video"></i>';
      markerElement.style.color = 'white';
      markerElement.style.fontSize = '12px';
      markerElement.style.textAlign = 'center';
      markerElement.style.width = '30px';
      markerElement.style.height = '30px';
      markerElement.style.borderRadius = '50%';
      markerElement.style.backgroundColor = 'rgba(0, 120, 255, 0.9)';
      markerElement.style.display = 'flex';
      markerElement.style.justifyContent = 'center';
      markerElement.style.alignItems = 'center';
      markerElement.style.border = '2px solid white';
      markerElement.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
    } else if (pin.animal_type === 'dog') {
      // Dog marker
      markerElement.className = 'dog-marker';
      markerElement.innerHTML = '<i class="fas fa-dog"></i>';
      markerElement.style.color = 'white';
      markerElement.style.fontSize = '12px';
      markerElement.style.textAlign = 'center';
      markerElement.style.width = '30px';
      markerElement.style.height = '30px';
      markerElement.style.borderRadius = '50%';
      markerElement.style.backgroundColor = 'rgba(220, 53, 69, 0.9)';
      markerElement.style.display = 'flex';
      markerElement.style.justifyContent = 'center';
      markerElement.style.alignItems = 'center';
      markerElement.style.border = '2px solid white';
      markerElement.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
    } else if (pin.animal_type === 'cat') {
      // Cat marker
      markerElement.className = 'cat-marker';
      markerElement.innerHTML = '<i class="fas fa-cat"></i>';
      markerElement.style.color = 'white';
      markerElement.style.fontSize = '12px';
      markerElement.style.textAlign = 'center';
      markerElement.style.width = '30px';
      markerElement.style.height = '30px';
      markerElement.style.borderRadius = '50%';
      markerElement.style.backgroundColor = 'rgba(255, 193, 7, 0.9)';
      markerElement.style.display = 'flex';
      markerElement.style.justifyContent = 'center';
      markerElement.style.alignItems = 'center';
      markerElement.style.border = '2px solid white';
      markerElement.style.boxShadow = '0 2px 4px rgba(0,0,0,0.3)';
    } else {
      // Default marker
      markerElement.className = 'default-marker';
      markerElement.style.backgroundColor = 'rgba(0, 180, 120, 0.9)';
      markerElement.style.width = '20px';
      markerElement.style.height = '20px';
      markerElement.style.borderRadius = '50%';
      markerElement.style.border = '2px solid white';
    }
    
    // Create marker
    const marker = new mapboxgl.Marker({
      element: markerElement,
      anchor: 'center',
      cameraData: pin.isCamera ? { 
        id: pin.cameraId,
        name: pin.name,
        location: pin.location
      } : null
    })
      .setLngLat([pin.lng, pin.lat])
      .addTo(map.value);
    
    // Create popup for marker
    let popupContent = '';
    
    if (pin.isCamera) {
      popupContent = `
        <div class="marker-popup camera-popup">
          <h3>${pin.name || 'Unnamed Camera'}</h3>
          <p>${pin.location || 'Unknown Location'}</p>
          <p class="status ${pin.status === 'active' ? 'status-active' : 'status-inactive'}">
            Status: ${pin.status || 'Unknown'}
          </p>
        </div>
      `;
    } else if (pin.animal_type) {
      popupContent = `
        <div class="marker-popup animal-popup">
          <h3>${pin.animal_type.charAt(0).toUpperCase() + pin.animal_type.slice(1)} Sighting</h3>
          <p>${pin.description || 'No description'}</p>
          <p class="timestamp">
            ${new Date(pin.detection_timestamp || new Date()).toLocaleString()}
          </p>
        </div>
      `;
    }
    
    if (popupContent) {
      const popup = new mapboxgl.Popup({
        closeButton: true,
        closeOnClick: true,
        maxWidth: '300px',
        offset: 25
      }).setHTML(popupContent);
      
      marker.setPopup(popup);
    }
    
    // Save marker reference
    pin.marker = marker;
    
    return marker;
  } catch (error) {
    console.error('Error creating marker:', error);
    return null;
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
  refreshMap: () => {
    if (map.value) {
      map.value.resize();
    }
  },
  getCurrentMapCenter: () => map.value ? map.value.getCenter() : null,
  getCameraPinLocations
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
