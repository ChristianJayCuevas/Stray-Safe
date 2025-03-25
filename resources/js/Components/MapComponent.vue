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
      addMarker(pin.coordinates, pin.animal_type);
      pinsList.value.push({
        coordinates: pin.coordinates,
        animalType: pin.animal_type
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
      </div>
    `);
    
    markerInstance.setPopup(popup);
    
    // Add click event to open camera feed
    marker.addEventListener('click', () => {
      if (details.hlsUrl) {
        window.open(details.hlsUrl, '_blank');
      }
    });
  }
  
  // Add the marker to the map
  markerInstance.addTo(map.value);
  
  return markerInstance;
}

// Allow adding a camera pin to the map - exposed for parent components
async function addCameraPin(coordinates, cameraInfo) {
  let markerInstance = null;
  
  try {
    if (!coordinates || !Array.isArray(coordinates) || coordinates.length !== 2 ||
        isNaN(coordinates[0]) || isNaN(coordinates[1])) {
      throw new Error('Invalid coordinates format. Expected [longitude, latitude] array');
    }
    
    console.log('Adding camera pin at coordinates:', coordinates, 'with camera info:', cameraInfo);
    
    markerInstance = addMarker(coordinates, 'Camera', cameraInfo);
    console.log('Marker instance created:', markerInstance);
    
    try {
      console.log('Sending API request to save camera pin...');
      
      const payload = {
        coordinates: coordinates,
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
      
      pinsList.value.push({
        coordinates: coordinates,
        cameraId: cameraInfo.id,
        cameraName: cameraInfo.name,
        hlsUrl: cameraInfo.videoSrc[0],
        isCamera: true
      });
      
      console.log("Camera pin added successfully:", response.data);
      return response.data;
    } catch (apiError) {
      console.error('API Error when adding camera pin:', apiError);
      
      pinsList.value.push({
        coordinates: coordinates,
        cameraId: cameraInfo.id,
        cameraName: cameraInfo.name,
        hlsUrl: cameraInfo.videoSrc[0],
        isCamera: true,
        isSyncPending: true
      });
      
      console.log("Camera pin added visually but failed to save to backend");
      return { 
        success: false, 
        message: 'Pin added visually but failed to save to server',
        error: apiError.message
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
  enablePinPlacementMode,
  disablePinPlacementMode,
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
/* Map container styles */
.map-container-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  margin-bottom: 0px;
  height: 80vh;
  position: relative;
}

.map-container {
  width: 100%;
  height: 100%;
  border-radius: 12px;
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
</style>
