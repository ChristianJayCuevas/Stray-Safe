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
      const marker = createMarker(pin);
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
      
      // Add direction indicator if this is a directional camera
      if (pinData.conicalView && pinData.viewingDirection !== undefined) {
        const directionIndicator = document.createElement('div');
        directionIndicator.className = 'camera-direction-indicator';
        directionIndicator.style.transform = `rotate(${pinData.viewingDirection}deg)`;
        marker.appendChild(directionIndicator);
      }
      
      // Add perception range visualization
      if (pinData.conicalView && pinData.viewingDirection !== undefined && pinData.viewingAngle !== undefined) {
        // Use conical perception range
        addConicalPerceptionRange(
          mapboxCoords, 
          pinData.perceptionRange || 30, 
          pinData.viewingDirection, 
          pinData.viewingAngle, 
          pinData.id
        );
      } else if (pinData.perceptionRange) {
        // Use circular perception range as fallback
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
          ${pinData.viewingDirection ? `<p><small>Direction: ${pinData.viewingDirection}°</small></p>` : ''}
          ${pinData.viewingAngle ? `<p><small>Field of View: ${pinData.viewingAngle}°</small></p>` : ''}
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
    
    // If it's a camera pin, remove its perception range (circular or conical)
    if (pin && (pin.isCamera || pin.type === 'Camera')) {
      // Remove perception range circle if it exists
      const circleId = `perception-circle-${pinId}`;
      const circleSourceId = `perception-source-${pinId}`;
      const labelId = `${circleId}-label`;
      
      // Remove conical range if it exists
      const coneId = `cone-${pinId}`;
      const coneSourceId = `cone-source-${pinId}`;
      
      // Remove all possible layers and sources
      const layersToRemove = [circleId, labelId, coneId];
      const sourcesToRemove = [circleSourceId, coneSourceId];
      
      // Remove layers first
      layersToRemove.forEach(layerId => {
        if (map.value.getLayer(layerId)) {
          map.value.removeLayer(layerId);
        }
      });
      
      // Then remove sources
      sourcesToRemove.forEach(sourceId => {
        if (map.value.getSource(sourceId)) {
          map.value.removeSource(sourceId);
        }
      });
      
      console.log(`Removed perception range visualizations for camera pin ${pinId}`);
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
    if (!coordinates || !Array.isArray(coordinates) || coordinates.length !== 2 ||
        isNaN(coordinates[0]) || isNaN(coordinates[1])) {
      throw new Error('Invalid coordinates format. Expected [longitude, latitude] array');
    }
    
    console.log('Adding camera pin at coordinates:', coordinates, 'with camera info:', cameraInfo);
    
    markerInstance = createMarker({
      coordinates: coordinates,
      camera_id: cameraInfo.id || '',
      camera_name: cameraInfo.name || '',
      hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : '',
      isCamera: true
    });
    console.log('Marker instance created:', markerInstance);
    
    try {
      console.log('Sending API request to save camera pin...');
      
      const payload = {
        coordinates: coordinates,
        camera_id: cameraInfo.id || '',
        camera_name: cameraInfo.name || '',
        hls_url: cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : ''
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
    markerInstance = createMarker({
      coordinates: coordinates,
      animal_type: animalType,
      description: details.description,
      imageUrl: details.imageUrl,
      isSyncPending: true // Mark as pending sync with backend
    });
    
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
        imageUrl: details.imageUrl,
        isSyncPending: true // Mark as pending sync with backend
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
  createMarker,
  addAnimalPin,
  addCameraPin,
  deletePin,
  enablePinPlacementMode,
  disablePinPlacementMode,
  getCameraPinLocations,
  addConicalPerceptionRange,
  refreshMap: () => {
    if (map.value) {
      map.value.resize();
    }
  },
  getCurrentMapCenter: () => map.value ? map.value.getCenter() : null,
});

// Add a conical perception range to the map for a camera
function addConicalPerceptionRange(coordinates, rangeInMeters, direction, angle, cameraId) {
  // Generate unique IDs for this conical range
  const coneId = `cone-${cameraId || Date.now()}`;
  const sourceId = `cone-source-${cameraId || Date.now()}`;
  
  try {
    if (!map.value) {
      console.error('Map not initialized, cannot add conical perception range');
      return;
    }
    
    console.log(`Adding conical perception range of ${rangeInMeters}m for camera at`, coordinates);
    console.log(`Direction: ${direction}°, Angle: ${angle}°`);
    
    // Check if map is already loaded
    if (!map.value.isStyleLoaded()) {
      console.log('Map style not yet loaded, waiting...');
      map.value.once('style.load', () => {
        addConicalPerceptionRange(coordinates, rangeInMeters, direction, angle, cameraId);
      });
      return;
    }
    
    // Remove any existing layers and sources for this camera
    if (map.value.getLayer(coneId)) {
      map.value.removeLayer(coneId);
    }
    
    if (map.value.getSource(sourceId)) {
      map.value.removeSource(sourceId);
    }
    
    // Convert meters to approximate degrees (rough calculation)
    // 1 degree is about 111km at equator, so 1m is roughly 0.000009 degrees
    const radiusInDegrees = rangeInMeters * 0.000009;
    
    // Calculate the coordinates for the cone based on direction and angle
    // We need to create a polygon that represents the conical field of view
    const coordinates_lng = Array.isArray(coordinates) ? coordinates[0] : coordinates.lng;
    const coordinates_lat = Array.isArray(coordinates) ? coordinates[1] : coordinates.lat;
    
    // Convert direction and angle to radians
    const directionRad = (direction * Math.PI) / 180;
    const halfAngleRad = (angle / 2 * Math.PI) / 180;
    
    // Calculate the points that make up the cone
    const conePoints = [];
    
    // Add the camera position as the first point (cone apex)
    conePoints.push([coordinates_lng, coordinates_lat]);
    
    // Add points along the arc of the cone
    const numPoints = 20; // Number of points to create a smooth arc
    const startAngle = directionRad - halfAngleRad;
    const endAngle = directionRad + halfAngleRad;
    
    for (let i = 0; i <= numPoints; i++) {
      const currentAngle = startAngle + (i / numPoints) * (endAngle - startAngle);
      const x = coordinates_lng + radiusInDegrees * Math.sin(currentAngle);
      const y = coordinates_lat + radiusInDegrees * Math.cos(currentAngle);
      conePoints.push([x, y]);
    }
    
    // Add the camera position again to close the polygon
    conePoints.push([coordinates_lng, coordinates_lat]);
    
    // Create a GeoJSON polygon for the cone
    const conePolygon = {
      type: 'Feature',
      properties: {
        camera_id: cameraId,
        range_meters: rangeInMeters,
        direction: direction,
        angle: angle
      },
      geometry: {
        type: 'Polygon',
        coordinates: [conePoints]
      }
    };
    
    // Add the source for the cone
    map.value.addSource(sourceId, {
      type: 'geojson',
      data: conePolygon
    });
    
    // Add a fill layer for the cone
    map.value.addLayer({
      id: coneId,
      type: 'fill',
      source: sourceId,
      layout: {},
      paint: {
        'fill-color': 'rgba(66, 133, 244, 0.2)',
        'fill-outline-color': 'rgba(66, 133, 244, 0.8)'
      }
    });
    
    // Store the cone information for later use
    const coneInfo = {
      coneId: coneId,
      sourceId: sourceId,
      cameraId: cameraId,
      coordinates: coordinates,
      radius: rangeInMeters,
      direction: direction,
      angle: angle
    };
    
    return coneInfo;
  } catch (error) {
    console.error('Error adding conical perception range:', error);
    return null;
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
  position: relative;
}

.custom-marker:hover {
  transform: scale(1.2);
  cursor: pointer;
}

/* Camera direction indicator */
.camera-direction-indicator {
  position: absolute;
  top: -8px;
  left: 50%;
  transform-origin: bottom center;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-bottom: 10px solid #d32f2f;
  z-index: 5;
}

/* Camera marker specific style */
.camera-marker {
  background-color: #2c3e50;
  color: white;
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
