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

    // Clear pinsList to start with a clean slate
    pinsList.value = [];

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
    
    console.log('Map cursor reset');
  } else {
    console.warn('Map not available when trying to disable pin placement mode');
  }
  
  // Reset state
  isPlacingCameraPin.value = false;
  placementCallback.value = null;
  selectedCameraForPin.value = null;
  
  console.log('Pin placement mode disabled - all state cleared');
}

// Handle map click during pin placement mode
function handleMapClick(e) {
  console.log('Map clicked at coordinates:', e.lngLat, 'Placement mode active:', isPlacingCameraPin.value, 'Callback registered:', !!placementCallback.value);
  
  if (isPlacingCameraPin.value && placementCallback.value) {
    console.log('✅ Pin placement mode is active and callback is registered');
    
    const coordinates = [e.lngLat.lng, e.lngLat.lat];
    console.log('Calling pin placement callback with coordinates:', coordinates);
    
    try {
      // Call the callback with the clicked coordinates
      placementCallback.value(coordinates);
    } catch (error) {
      console.error('Error in pin placement callback:', error);
      // Reset placement mode if there's an error
      isPlacingCameraPin.value = false;
      placementCallback.value = null;
      
      if (map.value) {
        map.value.getCanvas().style.cursor = '';
      }
    }
  } else if (isPlacingCameraPin.value && !placementCallback.value) {
    console.error('⚠️ Pin placement mode is active but no callback is registered');
    // Reset placement mode
    isPlacingCameraPin.value = false;
    
    if (map.value) {
      map.value.getCanvas().style.cursor = '';
    }
  }
}

// Fetch pins from the backend
async function fetchPins() {
  try {
    console.log('Fetching pins from the server...');
    const response = await axios.get('/pins');
    const pins = response.data;
    console.log('Fetched pins:', pins);

    // Clear existing pins
    pinsList.value = [];
    console.log('Cleared existing pins list');

    if (!pins || pins.length === 0) {
      console.log('No pins received from server');
      return;
    }

    console.log(`Processing ${pins.length} pins from server...`);

    // Process and add each pin
    for (const pin of pins) {
      try {
        // Verify coordinates
        if (!pin.coordinates) {
          console.warn('Pin has no coordinates, skipping:', pin);
          continue;
        }

        // Convert coordinates to proper format
        if (typeof pin.coordinates === 'string') {
          try {
            pin.coordinates = JSON.parse(pin.coordinates);
            console.log('Parsed string coordinates:', pin.coordinates);
          } catch (parseError) {
            console.error('Failed to parse coordinates string:', pin.coordinates, parseError);
            continue;
          }
        }

        // Determine if this is a camera pin
        const isCamera = pin.is_camera === true || pin.type === 'camera' || pin.type === 'Camera';
        
        // For camera pins, ensure all attributes are properly loaded
        if (isCamera) {
          // Normalize camera data format
          const cameraPin = {
            coordinates: pin.coordinates,
            id: pin.camera_id || pin.id,
            cameraId: pin.camera_id || pin.id,
            rtmp_key: pin.rtmp_key || pin.camera_id || pin.id,
            camera_id: pin.camera_id || pin.id,
            name: pin.camera_name || pin.name || 'Camera',
            cameraName: pin.camera_name || pin.name || 'Camera',
            camera_name: pin.camera_name || pin.name || 'Camera',
            location: pin.location || 'Unknown Location',
            hls_url: pin.hls_url || '',
            isCamera: true,
            type: 'Camera',
            // Load directional and perception properties
            perceptionRange: parseFloat(pin.perception_range || pin.perceptionRange || 30),
            viewingDirection: parseFloat(pin.viewing_direction || pin.viewingDirection || 0),
            viewingAngle: parseFloat(pin.viewing_angle || pin.viewingAngle || 60),
            conicalView: pin.conical_view === true || pin.conicalView === true,
            status: pin.status || 'active'
          };
          
          console.log('Creating camera pin from database:', cameraPin);
          
          // Save to pinsList before creating marker, so the marker can find it in the list
          pinsList.value.push(cameraPin);
          
          // Create marker after adding to pinsList
          const marker = createMarker(cameraPin);
          if (marker) {
            console.log('Created camera marker successfully');
          } else {
            console.error('Failed to create marker for camera pin');
          }
        } else {
          // Regular animal pin
          console.log('Creating animal pin from database:', pin);
          const animalPin = {
            coordinates: pin.coordinates,
            id: pin.id,
            type: pin.animal_type,
            animal_type: pin.animal_type,
            animalType: pin.animal_type,
            description: pin.description || `${pin.animal_type} sighting`,
            image_url: pin.image_url,
            detection_timestamp: pin.detection_timestamp,
            camera_id: pin.camera_id,
            isCamera: false,
            status: pin.status || 'active'
          };
          
          // Save to pinsList before creating marker
          pinsList.value.push(animalPin);
          
          // Create marker after adding to pinsList
          const marker = createMarker(animalPin);
          if (marker) {
            console.log(`Created ${animalPin.animal_type} marker successfully`);
          } else {
            console.error(`Failed to create marker for ${animalPin.animal_type} pin`);
          }
        }
      } catch (pinError) {
        console.error('Error processing pin:', pin, pinError);
      }
    }
    
    console.log('Finished loading pins:', pinsList.value.length, 'pins loaded');
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
          pinData.id || pinData.cameraId || Date.now().toString()
        );
      } else if (pinData.perceptionRange) {
        // Use circular perception range as fallback
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
    
    // Create popup content
    const popupHTML = createPopupHTML(pinData, pinType, isCamera);
    
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
    
    // Extract camera ID - use rtmp_key if available, otherwise use id
    const cameraId = cameraInfo.rtmp_key || cameraInfo.id || '';
    console.log('Using camera ID:', cameraId);
    
    // Create camera pin data object with all available information
    const pinData = {
      coordinates: coordinates,
      id: cameraId, // Set ID directly to rtmp_key/id
      cameraId: cameraId, // Also set cameraId for backwards compatibility
      camera_id: cameraId, // Also set camera_id for API format compatibility
      rtmp_key: cameraInfo.rtmp_key || cameraInfo.id, // Store rtmp_key explicitly
      cameraName: cameraInfo.name || '',
      camera_name: cameraInfo.name || '',
      name: cameraInfo.name || '',
      location: cameraInfo.location || '',
      hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : '',
      type: 'Camera',
      isCamera: true,
      perceptionRange: parseFloat(cameraInfo.perceptionRange || 30),
      // Store directional properties
      viewingDirection: cameraInfo.viewingDirection !== undefined ? parseFloat(cameraInfo.viewingDirection) : 0,
      viewingAngle: cameraInfo.viewingAngle !== undefined ? parseFloat(cameraInfo.viewingAngle) : 60,
      conicalView: cameraInfo.conicalView !== undefined ? !!cameraInfo.conicalView : false,
      // Add additional properties for persistence
      originalId: cameraInfo.originalId || cameraInfo.original_id || cameraInfo.id,
      original_id: cameraInfo.originalId || cameraInfo.original_id || cameraInfo.id,
      status: cameraInfo.status || 'active'
    };
    
    // First save to pinsList for local tracking
    pinsList.value.push(pinData);
    console.log('Added camera pin to pinsList:', pinData);
    
    // Then create the marker after adding to pinsList
    markerInstance = createMarker(pinData);
    console.log('Created camera marker:', markerInstance);
    
    // Try to save to backend API
    try {
      console.log('Sending API request to save camera pin...');
      
      const payload = {
        coordinates: coordinates,
        camera_id: cameraId,
        rtmp_key: cameraInfo.rtmp_key || cameraInfo.id,
        camera_name: cameraInfo.name || '',
        location: cameraInfo.location || '',
        hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : '',
        // Include directional and perception properties
        viewing_direction: pinData.viewingDirection,
        viewing_angle: pinData.viewingAngle,
        conical_view: pinData.conicalView,
        perception_range: pinData.perceptionRange,
        original_id: pinData.original_id,
        type: 'Camera',
        is_camera: true
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
      
      // If API gives us a new ID, update our local reference
      if (response.data.id) {
        const pinIndex = pinsList.value.findIndex(pin => pin.id === cameraId || pin.cameraId === cameraId);
        if (pinIndex !== -1) {
          pinsList.value[pinIndex].id = response.data.id;
          console.log("Updated pin with API-provided ID:", response.data.id);
        }
      }
      
      // If API response has additional camera data, update our local reference
      if (response.data.pin && Object.keys(response.data.pin).length > 0) {
        const pinIndex = pinsList.value.findIndex(pin => pin.id === cameraId || pin.cameraId === cameraId);
        if (pinIndex !== -1) {
          // Merge any new data from the API response with our local pin data
          pinsList.value[pinIndex] = { ...pinsList.value[pinIndex], ...response.data.pin };
          console.log("Updated pin with API data:", pinsList.value[pinIndex]);
        }
      }
      
      return response.data;
    } catch (apiError) {
      console.error('API Error when adding camera pin:', apiError);
      
      // Find the pin in pinsList
      const pinIndex = pinsList.value.findIndex(pin => pin.id === cameraId || pin.cameraId === cameraId);
      if (pinIndex !== -1) {
        pinsList.value[pinIndex].isSyncPending = true;
        console.log("Marked pin as pending sync:", pinsList.value[pinIndex]);
      }
      
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
    console.log('Current pinsList contains:', pinsList.value.length, 'pins');
    
    if (!map.value) {
      console.error('Map is not initialized, cannot get camera pins');
      return [];
    }
    
    const cameraPins = [];
    
    // Loop through pinsList to find camera pins
    pinsList.value.forEach((pin, index) => {
      // More inclusive check for camera pins
      const isCamera = pin.isCamera === true || 
                       pin.type === 'camera' || 
                       pin.type === 'Camera' || 
                       pin.cameraId || 
                       pin.camera_id ||
                       pin.rtmp_key;
      
      if (isCamera) {
        console.log(`Found camera pin #${index}:`, pin);
        
        // Extract camera ID
        let cameraId = '';
        if (pin.rtmp_key) {
          cameraId = pin.rtmp_key;
          console.log('Using rtmp_key as camera ID:', cameraId);
        } else if (pin.cameraId) {
          cameraId = pin.cameraId;
          console.log('Using cameraId as camera ID:', cameraId);
        } else if (pin.camera_id) {
          cameraId = pin.camera_id;
          console.log('Using camera_id as camera ID:', cameraId);
        } else if (pin.id) {
          cameraId = pin.id;
          console.log('Using id as camera ID:', cameraId);
        } else {
          console.warn('No ID found for camera pin, generating temporary ID');
          cameraId = `camera-${Date.now()}-${index}`;
        }
        
        // Get coordinates in consistent format
        let coordinates = null;
        
        // Handle different coordinate formats - ensuring we parse string values to numbers
        if (Array.isArray(pin.coordinates)) {
          coordinates = { 
            lat: parseFloat(pin.coordinates[1]), 
            lng: parseFloat(pin.coordinates[0]) 
          };
        } else if (pin.coordinates && typeof pin.coordinates === 'object') {
          coordinates = {
            lat: parseFloat(pin.coordinates.lat || 0),
            lng: parseFloat(pin.coordinates.lng || 0)
          };
        } else if (pin.lat !== undefined && pin.lng !== undefined) {
          coordinates = { 
            lat: parseFloat(pin.lat), 
            lng: parseFloat(pin.lng) 
          };
        }
        
        // Verify that the parsed coordinates are valid numbers
        if (coordinates && !isNaN(coordinates.lat) && !isNaN(coordinates.lng)) {
          // Ensure IDs are strings
          const cameraPin = {
            id: String(cameraId), // This is the key ID used for matching with API counters
            name: pin.cameraName || pin.camera_name || pin.name || 'Unnamed Camera',
            rtmp_key: pin.rtmp_key ? String(pin.rtmp_key) : undefined, // Include rtmp_key explicitly for matching
            original_id: pin.original_id || pin.originalId,
            coordinates: coordinates,
            perceptionRange: parseFloat(pin.perceptionRange || pin.perception_range || 30),
            viewingDirection: parseFloat(pin.viewingDirection || pin.viewing_direction || 0),
            viewingAngle: parseFloat(pin.viewingAngle || pin.viewing_angle || 60),
            conicalView: pin.conicalView === true || pin.conical_view === true
          };
          
          console.log('Added camera pin to result:', cameraPin);
          cameraPins.push(cameraPin);
        } else {
          console.warn('Invalid coordinates for camera pin:', pin);
        }
      }
    });
    
    console.log('Final camera pins result:', cameraPins);
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

// Create popup content based on pin type
function createPopupHTML(pinData, pinType, isCamera) {
  let popupHTML = '';
  
  if (isCamera) {
    // Camera pin popup
    popupHTML = `
      <div class="camera-popup">
        <h3>${pinData.cameraName || pinData.name || 'Camera'}</h3>
        <p>${pinData.location || 'Location not specified'}</p>
        <p><small>Status: ${pinData.status || 'Unknown'}</small></p>
        ${pinData.id || pinData.cameraId ? `<p><small>Camera ID: ${pinData.id || pinData.cameraId}</small></p>` : ''}
        ${pinData.rtmp_key ? `<p><small>RTMP Key: ${pinData.rtmp_key}</small></p>` : ''}
        ${pinData.perceptionRange ? `<p><small>Perception Range: ${pinData.perceptionRange}m</small></p>` : ''}
        ${pinData.viewingDirection !== undefined ? `<p><small>Direction: ${pinData.viewingDirection}°</small></p>` : ''}
        ${pinData.viewingAngle !== undefined ? `<p><small>Field of View: ${pinData.viewingAngle}°</small></p>` : ''}
        ${pinData.conicalView ? `<p><small>Viewing Mode: Directional</small></p>` : ''}
        ${!pinData.conicalView && pinData.viewingAngle ? `<p><small>Viewing Mode: 360°</small></p>` : ''}
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
        ${pinData.camera_id ? `<p><small>Camera: ${pinData.camera_id}</small></p>` : ''}
        ${pinData.id ? `<button class="delete-pin-btn" data-pin-id="${pinData.id}">Delete Pin</button>` : ''}
      </div>
    `;
  }
  
  return popupHTML;
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
  margin: 0 20px 100px 20px;
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
