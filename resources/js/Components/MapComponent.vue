<script setup>
import { onMounted, ref, inject, defineExpose, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import axios from 'axios';

// Get the global dark mode state
const isDarkMode = inject('isDarkMode', ref(false));

// Map container and instance
const mapContainer = ref(null);
const map = ref(null);
const pinsList = ref([]); // Stores the list of pins
const mapLoadError = ref(false);
const mapLoadTimeout = ref(null);

// Mapbox token
const mapboxToken = 'pk.eyJ1IjoiMS1heWFub24iLCJhIjoiY20ycnAzZW5pMWZpZTJpcThpeTJjdDU1NCJ9.7AVb_LJf6sOtb-QAxwR-hg';

// Get the CSRF token from the meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

// Set the CSRF token as a common header for all Axios requests
axios.defaults.headers.common['X-CSRF-TOKEN'] = csrfToken;

// Initialize the map
async function initializeMap() {
  try {
    console.log('Starting map initialization...', { container: mapContainer.value, isDarkMode: isDarkMode.value });
    
    if (!mapContainer.value) {
      console.error('Map container element not found!');
      mapLoadError.value = true;
      return;
    }

    // Set a timeout to detect if map fails to load
    mapLoadTimeout.value = setTimeout(() => {
      if (!map.value || !map.value.loaded()) {
        console.error('Map failed to load after timeout');
        mapLoadError.value = true;
        if (mapContainer.value) {
          mapContainer.value.classList.add('error');
        }
      }
    }, 10000); // 10 seconds timeout

    mapboxgl.accessToken = mapboxToken;
    console.log('Using Mapbox token:', mapboxToken);

    // Initialize Mapbox map
    console.log('Creating map instance with options:', {
      container: 'mapContainer',
      style: isDarkMode.value ? 'mapbox://styles/mapbox/dark-v10' : 'mapbox://styles/1-ayanon/cm2rp9idm00as01qwcq9ihoyr',
      center: [121.039295, 14.631141],
      zoom: 15.5
    });
    
    map.value = new mapboxgl.Map({
      container: mapContainer.value,
      style: isDarkMode.value ? 'mapbox://styles/mapbox/dark-v10' : 'mapbox://styles/1-ayanon/cm2rp9idm00as01qwcq9ihoyr',
      center: [121.039295, 14.631141],
      zoom: 15.5,
      attributionControl: false,
    });

    console.log('Map instance created:', map.value);

    // Add navigation control
    map.value.addControl(new mapboxgl.NavigationControl(), 'top-right');
    console.log('Navigation control added');

    // Add scale control
    map.value.addControl(new mapboxgl.ScaleControl(), 'bottom-left');
    console.log('Scale control added');

    // Set up map click handler for pin placement
    map.value.on('click', handleMapClick);
    console.log('Map click handler set up');

    // Wait for map to load
    map.value.on('load', async () => {
      console.log('Map loaded successfully!');
      // Clear timeout since map loaded successfully
      if (mapLoadTimeout.value) {
        clearTimeout(mapLoadTimeout.value);
        mapLoadTimeout.value = null;
      }
      // Fetch initial pins
      await fetchPins();
    });
    
    // Add error handling for map load
    map.value.on('error', (e) => {
      console.error('Mapbox error:', e);
      mapLoadError.value = true;
      if (mapContainer.value) {
        mapContainer.value.classList.add('error');
      }
    });
    
  } catch (error) {
    console.error('Error initializing map:', error);
    mapLoadError.value = true;
    if (mapContainer.value) {
      mapContainer.value.classList.add('error');
    }
  }
}

// Call initializeMap when component is mounted
onMounted(() => {
  console.log('MapComponent mounted, initializing map...');
  
  // Check if mapboxgl is available
  if (typeof mapboxgl === 'undefined') {
    console.error('Mapbox GL library is not loaded!');
    return;
  } else {
    console.log('Mapbox GL library is available:', mapboxgl);
  }
  
  try {
    // Check if container exists and is visible
    setTimeout(() => {
      if (!mapContainer.value) {
        console.error('Map container ref is null after timeout!');
        return;
      }
      
      // Check container dimensions
      const rect = mapContainer.value.getBoundingClientRect();
      console.log('Map container dimensions:', {
        width: rect.width,
        height: rect.height,
        visible: rect.width > 0 && rect.height > 0
      });
      
      if (rect.width === 0 || rect.height === 0) {
        console.error('Map container has zero width or height! The map cannot be displayed.');
        // Force height if needed
        mapContainer.value.style.height = '500px';
        mapContainer.value.style.width = '100%';
        console.log('Applied forced dimensions to map container');
      }
      
      console.log('Attempting to initialize map after delay');
      initializeMap();
    }, 1000);
  } catch (error) {
    console.error('Error during map initialization:', error);
  }
});

// Clean up on unmount
onUnmounted(() => {
  if (mapLoadTimeout.value) {
    clearTimeout(mapLoadTimeout.value);
    mapLoadTimeout.value = null;
  }
  
  if (map.value) {
    map.value.remove();
    map.value = null;
  }
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
    console.log('Fetching pins from backend...');
    
    // Clear existing pinsList
    pinsList.value = [];
    
    const response = await axios.get('/pins');
    const pins = response.data.data; 
    
    console.log('Received pins from backend:', pins);
    
    if (!pins || pins.length === 0) {
      console.log('No pins received from backend');
      return;
    }

    pins.forEach(pin => {
      try {
        // Ensure coordinates are valid
        let coordinates;
        
        // Handle potential string coordinates stored as JSON
        if (pin.coordinates) {
          if (typeof pin.coordinates === 'string') {
            try {
              // Try to parse as JSON if it's a string
              pin.coordinates = JSON.parse(pin.coordinates);
              console.log('Parsed pin coordinates from JSON string:', pin.coordinates);
            } catch (e) {
              console.warn('Failed to parse coordinates from JSON string:', pin.coordinates);
            }
          }
          
          if (Array.isArray(pin.coordinates)) {
            coordinates = [parseFloat(pin.coordinates[0]), parseFloat(pin.coordinates[1])];
          } else if (pin.coordinates.lat !== undefined && pin.coordinates.lng !== undefined) {
            coordinates = [parseFloat(pin.coordinates.lng), parseFloat(pin.coordinates.lat)];
          }
        }
        
        if (!coordinates && pin.latitude !== undefined && pin.longitude !== undefined) {
          coordinates = [parseFloat(pin.longitude), parseFloat(pin.latitude)];
        }
        
        if (!coordinates) {
          console.warn('Pin has invalid coordinates format:', pin);
          return; // Skip this pin
        }
        
        // Determine if this is a camera pin
        const isCamera = pin.is_camera === true || pin.animal_type === 'Camera';
        console.log(`Processing pin ID ${pin.id}, type: ${isCamera ? 'Camera' : pin.animal_type}`);
        
        // Convert string "true"/"false" to boolean if needed
        let conicalView = false;
        if (typeof pin.conical_view === 'boolean') {
          conicalView = pin.conical_view;
        } else if (pin.conical_view === 'true' || pin.conical_view === '1' || pin.conical_view === 1) {
          conicalView = true;
        }
        
        console.log(`Pin ${pin.id} conical view:`, {
          original: pin.conical_view,
          converted: conicalView
        });
        
        // Create a full pin object with all available properties
        const pinData = {
          id: pin.id,
          coordinates: coordinates,
          type: isCamera ? 'camera' : pin.animal_type,
          animal_type: pin.animal_type,
          isCamera: isCamera,
          
          // Add all properties with appropriate defaults
          camera_id: pin.camera_id || pin.id,
          cameraId: pin.camera_id || pin.id,
          rtmp_key: pin.rtmp_key || pin.camera_id || pin.id,
          original_id: pin.original_id || pin.camera_id || pin.id,
          cameraName: pin.camera_name || 'Unknown Camera',
          name: pin.camera_name || 'Unknown Camera',
          location: pin.location || 'Unknown Location',
          description: pin.description || '',
          status: pin.stray_status || 'active',
          
          // Camera specific properties
          perceptionRange: parseFloat(pin.perception_range || 30),
          viewingDirection: parseFloat(pin.viewing_direction || 0),
          viewingAngle: parseFloat(pin.viewing_angle || 60),
          conicalView: conicalView,
          
          // Additional properties
          detection_timestamp: pin.detection_timestamp,
          image_url: pin.image_url,
          snapshot_path: pin.snapshot_path,
          hls_url: pin.hls_url
        };
        
        console.log(`Created pin data object:`, pinData);
        
        // Create the marker using this pin data
        const marker = createMarker(pinData);
        
        if (marker) {
          // Add to pins list 
          pinData.marker = marker;
          pinsList.value.push(pinData);
          console.log(`Added pin ID ${pin.id} to pinsList`);
          
          // Ensure the perception range is visible
          // If this failed during marker creation, try again directly
          if (isCamera && pinData.perceptionRange) {
            if (pinData.conicalView && 
                pinData.viewingDirection !== undefined && 
                pinData.viewingAngle !== undefined) {
              // Re-add the conical perception range if not already visible
              const coneId = `cone-${pinData.id}`;
              if (!map.value.getLayer(coneId)) {
                console.log(`Ensuring conical view is visible for camera ${pinData.id}`);
                addConicalPerceptionRange(
                  coordinates,
                  pinData.perceptionRange,
                  pinData.viewingDirection,
                  pinData.viewingAngle,
                  pinData.id
                );
              }
            } else {
              // Re-add the circular perception range if not already visible
              const circleId = `perception-circle-${pinData.id}`;
              if (!map.value.getLayer(circleId)) {
                console.log(`Ensuring perception circle is visible for camera ${pinData.id}`);
                addPerceptionRangeCircle(
                  coordinates,
                  pinData.perceptionRange,
                  pinData.id
                );
              }
            }
          }
        } else {
          console.error(`Failed to create marker for pin ID ${pin.id}`);
        }
      } catch (pinError) {
        console.error('Error processing pin:', pin, pinError);
      }
    });
    
    console.log(`Loaded ${pinsList.value.length} pins into pinsList`);
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
    
    // Log input data for debugging
    console.log('Creating marker with data:', pinData);
    
    // Get coordinates in the format mapbox expects [lng, lat]
    let mapboxCoords;
    
    if (Array.isArray(pinData.coordinates) && pinData.coordinates.length >= 2) {
      // Already in [lng, lat] format, but ensure they're numbers
      mapboxCoords = [parseFloat(pinData.coordinates[0]), parseFloat(pinData.coordinates[1])];
      console.log('Using array coordinates (converted to numbers):', mapboxCoords);
    } else if (pinData.lat !== undefined && pinData.lng !== undefined) {
      // Object with lat/lng properties, ensure they're numbers
      mapboxCoords = [parseFloat(pinData.lng), parseFloat(pinData.lat)];
      console.log('Using lat/lng properties (converted to numbers):', mapboxCoords);
    } else if (pinData.coordinates && typeof pinData.coordinates === 'object') {
      // Object with lat/lng in coordinates, ensure they're numbers
      if ('lat' in pinData.coordinates && 'lng' in pinData.coordinates) {
        mapboxCoords = [parseFloat(pinData.coordinates.lng), parseFloat(pinData.coordinates.lat)];
        console.log('Using coordinates object (converted to numbers):', mapboxCoords);
      }
    } else {
      console.error('Invalid coordinates format for marker:', pinData);
      return null;
    }
    
    // Final check to ensure coordinates are valid
    if (!mapboxCoords || mapboxCoords.length < 2 || 
        isNaN(mapboxCoords[0]) || isNaN(mapboxCoords[1])) {
      console.error('Invalid or missing coordinates after parsing:', mapboxCoords);
      return null;
    }
    
    // Create element based on pin type
    const marker = document.createElement('div');
    marker.className = 'custom-marker';
    
    // Determine pin type - normalize to lowercase for consistent comparison
    let pinType = '';
    if (pinData.type) {
      pinType = String(pinData.type).toLowerCase();
    } else if (pinData.animalType) {
      pinType = String(pinData.animalType).toLowerCase();
    } else if (pinData.animal_type) {
      pinType = String(pinData.animal_type).toLowerCase();
    } else {
      pinType = 'default';
    }
    
    console.log('Determined pin type:', pinType);
    
    // Check if it's a camera pin
    const isCamera = pinData.isCamera === true || pinType === 'camera';
    
    // Apply specific styles based on type
    if (isCamera) {
      marker.className = 'custom-marker camera-marker';
      marker.innerHTML = '<i class="fas fa-video"></i>';
      
      console.log(`Camera pin settings for ${pinData.id}:`, {
        conicalView: pinData.conicalView,
        viewingDirection: pinData.viewingDirection,
        viewingAngle: pinData.viewingAngle
      });
      
      // Add direction indicator if this is a directional camera
      if (pinData.conicalView === true && pinData.viewingDirection !== undefined) {
        console.log(`Adding direction indicator for camera ${pinData.id} pointing at ${pinData.viewingDirection}°`);
        const directionIndicator = document.createElement('div');
        directionIndicator.className = 'camera-direction-indicator';
        directionIndicator.style.transform = `rotate(${pinData.viewingDirection}deg)`;
        marker.appendChild(directionIndicator);
      }
      
      // Add perception range visualization
      if (pinData.conicalView === true && 
          pinData.viewingDirection !== undefined && 
          pinData.viewingAngle !== undefined) {
        // Use conical perception range
        console.log(`Adding conical perception range for camera ${pinData.id} with direction ${pinData.viewingDirection}° and angle ${pinData.viewingAngle}°`);
        addConicalPerceptionRange(
          mapboxCoords, 
          pinData.perceptionRange || 30, 
          pinData.viewingDirection, 
          pinData.viewingAngle, 
          pinData.id || pinData.cameraId || Date.now().toString()
        );
      } else if (pinData.perceptionRange) {
        // Use circular perception range as fallback
        console.log(`Adding circular perception range for camera ${pinData.id}`);
        addPerceptionRangeCircle(
          mapboxCoords, 
          pinData.perceptionRange, 
          pinData.id || pinData.cameraId || Date.now().toString()
        );
      }
    } else if (pinType === 'dog') {
      marker.style.backgroundColor = '#38a3a5'; // Dog color
      marker.innerHTML = '<i class="fas fa-dog"></i>';
    } else if (pinType === 'cat') {
      marker.style.backgroundColor = '#57cc99'; // Cat color
      marker.innerHTML = '<i class="fas fa-cat"></i>';
    } else {
      marker.style.backgroundColor = '#4f6642'; // Default color
      marker.innerHTML = '<i class="fas fa-map-marker-alt"></i>';
    }
    
    // Create marker instance
    console.log('Creating marker at coordinates:', mapboxCoords);
    const markerInstance = new mapboxgl.Marker(marker).setLngLat(mapboxCoords);
    
    // Create popup content based on pin type
    let popupHTML = '';
    
    if (isCamera) {
      // Camera pin popup
      popupHTML = `
        <div class="camera-popup">
          <h3>${pinData.cameraName || pinData.name || 'Camera'}</h3>
          <p>${pinData.location || 'Location not specified'}</p>
          <p><small>Status: ${pinData.status || 'Unknown'}</small></p>
          ${pinData.perceptionRange ? `<p><small>Perception Range: ${pinData.perceptionRange}m</small></p>` : ''}
          ${pinData.viewingDirection !== undefined ? `<p><small>Direction: ${pinData.viewingDirection}°</small></p>` : ''}
          ${pinData.viewingAngle !== undefined ? `<p><small>Field of View: ${pinData.viewingAngle}°</small></p>` : ''}
          ${pinData.id || pinData.cameraId ? `<button class="delete-pin-btn" data-pin-id="${pinData.id || pinData.cameraId}">Delete Pin</button>` : ''}
        </div>
      `;
    } else {
      // Animal pin popup
      const displayType = pinType.charAt(0).toUpperCase() + pinType.slice(1); // Capitalize first letter
      popupHTML = `
        <div class="pin-popup">
          <h3>${displayType}</h3>
          ${pinData.description ? `<p>${pinData.description}</p>` : ''}
          ${pinData.detection_timestamp ? `<p><small>Detected: ${new Date(pinData.detection_timestamp).toLocaleString()}</small></p>` : ''}
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
        const pinId = pinData.id || pinData.cameraId;
        const deleteBtn = document.querySelector(`.delete-pin-btn[data-pin-id="${pinId}"]`);
        if (deleteBtn) {
          deleteBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this pin?')) {
              deletePin(pinId, markerInstance);
            }
          });
        }
      }, 100);
    });
    
    // Add marker to map
    markerInstance.addTo(map.value);
    console.log('Marker added to map successfully');
    
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

    // Create a detailed camera object for the marker
    const cameraData = {
      coordinates: coordinates,
      camera_id: cameraInfo.id || '',
      rtmp_key: cameraInfo.rtmp_key || cameraInfo.id || '',
      camera_name: cameraInfo.name || '',
      location: cameraInfo.location || 'Unknown Location',
      hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : '',
      isCamera: true,
      viewingDirection: cameraInfo.viewingDirection !== undefined ? cameraInfo.viewingDirection : 0,
      viewingAngle: cameraInfo.viewingAngle !== undefined ? cameraInfo.viewingAngle : 60,
      conicalView: cameraInfo.conicalView === true,
      perceptionRange: cameraInfo.perceptionRange || 30,
      original_id: cameraInfo.original_id || cameraInfo.id || ''
    };
    
    console.log('Creating camera marker with data:', cameraData);
    
    // First add to pins list so it's available for retrieval
    pinsList.value.push(cameraData);
    
    // Then create the marker
    markerInstance = createMarker(cameraData);
    console.log('Marker instance created:', markerInstance);
    
    try {
      console.log('Sending API request to save camera pin...');
      
      // Create payload for the API
      const payload = {
        coordinates: coordinates,
        camera_id: cameraInfo.id || '',
        rtmp_key: cameraInfo.rtmp_key || cameraInfo.id || '',
        camera_name: cameraInfo.name || '',
        location: cameraInfo.location || 'Unknown Location',
        hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : '',
        viewing_direction: cameraInfo.viewingDirection !== undefined ? cameraInfo.viewingDirection : 0,
        viewing_angle: cameraInfo.viewingAngle !== undefined ? cameraInfo.viewingAngle : 60,
        conical_view: cameraInfo.conicalView === true,
        perception_range: cameraInfo.perceptionRange || 30,
        original_id: cameraInfo.original_id || cameraInfo.id || ''
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
      
      // Update the pin in pinsList with any new data from the server
      if (response.data.pin && response.data.pin.id) {
        const pinIndex = pinsList.value.findIndex(p => 
          (p.coordinates && p.coordinates[0] === coordinates[0] && p.coordinates[1] === coordinates[1]) ||
          (p.camera_id === cameraData.camera_id)
        );
        
        if (pinIndex !== -1) {
          pinsList.value[pinIndex].id = response.data.pin.id;
          console.log("Updated pin in pinsList with server ID:", response.data.pin.id);
        }
      }
      
      console.log("Camera pin added successfully:", response.data);
      return response.data;
    } catch (apiError) {
      console.error('API Error when adding camera pin:', apiError);
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
async function addAnimalPin(pinData) {
  let markerInstance = null;
  
  try {
    console.log('Adding animal pin with data:', pinData);
    
    // Validate required fields
    if (!pinData || !pinData.lat || !pinData.lng || !pinData.animal_type) {
      throw new Error('Invalid pin data. Required fields: lat, lng, animal_type');
    }
    
    // Create a new pin object with all necessary properties
    const pin = {
      coordinates: [pinData.lng, pinData.lat],
      type: pinData.animal_type,
      animal_type: pinData.animal_type,
      description: pinData.description || `${pinData.animal_type} sighting`,
      image_url: pinData.image_url,
      isCamera: false,
      status: pinData.status || 'active',
      id: pinData.id || `animal-${Date.now()}`
    };
    
    // Add to pins list
    pinsList.value.push(pin);
    
    // Create marker on map
    markerInstance = createMarker(pin);
    
    // If this is not from automated detection, try to save to backend
    if (!pinData.is_automated) {
      try {
        console.log('Saving animal pin to backend:', pin);
        
        // Create payload for backend
        const payload = {
          lat: pinData.lat,
          lng: pinData.lng,
          animal_type: pinData.animal_type,
          description: pinData.description,
          image_url: pinData.image_url
        };
        
        // Send to backend
        const response = await axios.post('/pin', payload);
        
        console.log("Animal pin saved to backend:", response.data);
        return { success: true, data: response.data };
      } catch (apiError) {
        console.error('API Error when saving animal pin:', apiError);
        
        // We keep the pin on the map even if backend save fails
        return { 
          success: false, 
          message: 'Pin added to map but failed to save to server',
          error: apiError.message
        };
      }
    } else {
      // Automated detection doesn't need to be saved to backend
      return { success: true, automated: true };
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

// Get camera pin locations - used by parent components for detection monitoring
async function getCameraPinLocations() {
  try {
    console.log('Getting camera pin locations from map');
    
    if (!map.value) {
      console.error('Map is not initialized, cannot get camera pins');
      return [];
    }
    
    const cameraPins = [];
    
    // Loop through pinsList to find camera pins
    pinsList.value.forEach(pin => {
      if (pin.isCamera || pin.cameraId) {
        let coordinates;
        
        // Handle different coordinate formats - ensuring we parse string values to numbers
        if (Array.isArray(pin.coordinates)) {
          coordinates = { 
            lat: parseFloat(pin.coordinates[1]), 
            lng: parseFloat(pin.coordinates[0]) 
          };
          console.log('Camera pin with array coordinates:', coordinates);
        } else if (pin.coordinates && typeof pin.coordinates === 'object') {
          coordinates = {
            lat: parseFloat(pin.coordinates.lat || 0),
            lng: parseFloat(pin.coordinates.lng || 0)
          };
          console.log('Camera pin with object coordinates:', coordinates);
        } else if (pin.lat !== undefined && pin.lng !== undefined) {
          coordinates = { 
            lat: parseFloat(pin.lat), 
            lng: parseFloat(pin.lng) 
          };
          console.log('Camera pin with lat/lng properties:', coordinates);
        }
        
        // Verify that the parsed coordinates are valid numbers
        if (coordinates && !isNaN(coordinates.lat) && !isNaN(coordinates.lng)) {
          // Preserve the original rtmp_key if it exists
          const rtmpKey = pin.rtmp_key || pin.cameraId || pin.id;
          console.log(`Camera pin ${pin.id} rtmp_key:`, rtmpKey);
          
          cameraPins.push({
            id: pin.cameraId || pin.id,
            cameraId: pin.cameraId || pin.id,
            rtmp_key: rtmpKey,
            original_id: pin.original_id || pin.cameraId || pin.id,
            name: pin.cameraName || pin.name || 'Unknown Camera',
            location: pin.location || 'Unknown Location',
            coordinates: coordinates,
            perceptionRange: parseFloat(pin.perceptionRange || 30),
            viewingDirection: parseFloat(pin.viewingDirection || 0),
            viewingAngle: parseFloat(pin.viewingAngle || 60),
            conicalView: !!pin.conicalView
          });
        } else {
          console.warn('Invalid coordinates for camera pin:', pin);
        }
      }
    });
    
    console.log('Found camera pins:', cameraPins);
    return cameraPins;
  } catch (error) {
    console.error('Error getting camera pin locations:', error);
    return [];
  }
}

// Add perception range circle to the map
function addPerceptionRangeCircle(coordinates, rangeInMeters, cameraId) {
  // Generate unique IDs for this circle
  const circleId = `perception-circle-${cameraId || Date.now()}`;
  const sourceId = `perception-source-${cameraId || Date.now()}`;
  
  try {
    if (!map.value) {
      console.error('Map not initialized, cannot add perception range');
      return;
    }
    
    console.log(`Adding perception range of ${rangeInMeters}m for camera at`, coordinates);
    
    // Check if map is already loaded
    if (!map.value.isStyleLoaded()) {
      console.log('Map style not yet loaded, waiting...');
      map.value.once('style.load', () => {
        addPerceptionRangeCircle(coordinates, rangeInMeters, cameraId);
      });
      return;
    }
    
    // Remove any existing layers and sources for this camera
    if (map.value.getLayer(circleId)) {
      map.value.removeLayer(circleId);
    }
    
    if (map.value.getSource(sourceId)) {
      map.value.removeSource(sourceId);
    }
    
    // Convert meters to approximate degrees (rough calculation)
    // 1 degree is about 111km at equator, so 1m is roughly 0.000009 degrees
    const radiusInDegrees = rangeInMeters * 0.000009;
    
    // Create a GeoJSON circle for the perception range
    const circlePolygon = {
      type: 'Feature',
      properties: {
        camera_id: cameraId,
        range_meters: rangeInMeters
      },
      geometry: {
        type: 'Point',
        coordinates: Array.isArray(coordinates) ? coordinates : [coordinates.lng, coordinates.lat]
      }
    };
    
    // Add the source for the circle
    map.value.addSource(sourceId, {
      type: 'geojson',
      data: circlePolygon
    });
    
    // Add a circle layer
    map.value.addLayer({
      id: circleId,
      type: 'circle',
      source: sourceId,
      paint: {
        'circle-radius': {
          stops: [
            [10, radiusInDegrees * 1000000], // Approximate scaling at zoom level 10
            [15, radiusInDegrees * 3000000], // Approximate scaling at zoom level 15
            [20, radiusInDegrees * 10000000] // Approximate scaling at zoom level 20
          ],
          base: 2
        },
        'circle-color': 'rgba(66, 133, 244, 0.2)',
        'circle-stroke-width': 1,
        'circle-stroke-color': 'rgba(66, 133, 244, 0.8)'
      }
    });
    
    return {
      circleId: circleId,
      sourceId: sourceId,
      cameraId: cameraId
    };
  } catch (error) {
    console.error('Error adding perception range:', error);
    return null;
  }
}

// Function to retry loading the map
function retryMapLoad() {
  console.log('Retrying map load...');
  
  // Reset error state
  mapLoadError.value = false;
  
  if (mapContainer.value) {
    mapContainer.value.classList.remove('error');
  }
  
  // Small delay before retry
  setTimeout(() => {
    if (map.value) {
      // Try to remove existing map instance first
      try {
        map.value.remove();
      } catch (e) {
        console.error('Error removing map:', e);
      }
      map.value = null;
    }
    
    // Reinitialize map
    initializeMap();
  }, 500);
}
</script>

<template>
  <div class="map-container-wrapper">
    <div class="map-container" :class="{ 'error': mapLoadError }" ref="mapContainer">
      <div v-if="mapLoadError" class="map-error-message">
        <div class="error-content">
          <i class="fas fa-exclamation-triangle error-icon"></i>
          <h3>Map failed to load</h3>
          <p>Please check your internet connection or try refreshing the page.</p>
          <button @click="retryMapLoad" class="retry-button">
            <i class="fas fa-sync-alt"></i> Retry
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.map-container-wrapper {
  width: 100%;
  height: 600px;
  margin: 0 20px 0px 0px;
  position: relative;
}

.map-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  position: relative;
  display: block;
}

/* Error message if map fails to load */
.map-container::after {
  content: "";
  display: none;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 16px;
  text-align: center;
  padding-top: 200px;
}

.map-container.error::after {
  content: "Map failed to load. Please check your internet connection or try refreshing the page.";
  display: block;
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

.map-error-message {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  border-radius: 12px;
}

.error-content {
  text-align: center;
  color: white;
  padding: 20px;
  max-width: 80%;
}

.error-icon {
  font-size: 48px;
  color: #f44336;
  margin-bottom: 15px;
}

.retry-button {
  background-color: #2196f3;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  margin-top: 15px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.retry-button:hover {
  background-color: #0d8bf2;
}
</style>
