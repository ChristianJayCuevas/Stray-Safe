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

// Store cone definitions globally
const coneMap = ref({});

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
const placementCallback = ref(null);


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

// Function to process each pin and add it to the map
async function processPins(pins) {
  console.log(`Processing ${pins.length} pins from API...`);
  
  // Clear existing pins and their visualizations
  pinsList.value.forEach(pin => {
    if (pin.marker) {
      pin.marker.remove();
    }
    
    // Remove any associated perception circles or cones
    if (pin.id) {
      removeCone(pin.id);
    }
  });
  
  // Clear pins list
  pinsList.value = [];
  
  // Process each pin
  pins.forEach(pin => {
    try {
      console.log('Processing pin:', pin);
      
      // Determine if this is a camera pin
      const isCamera = pin.is_camera === true || 
                     pin.isCamera === true || 
                     pin.animal_type === 'Camera' || 
                     pin.animalType === 'Camera';
      
      // Process conical view data if available
      let conicalView = false;
      
      if (isCamera) {
        // Check all possible ways conical_view might be stored
        if (pin.conical_view !== undefined) {
          conicalView = Boolean(pin.conical_view);
        } else if (pin.conicalView !== undefined) {
          conicalView = Boolean(pin.conicalView);
        }
        
        console.log(`Camera pin ${pin.id} conical view status:`, conicalView);
      }
      
      // Extract coordinates in a format we can use
      let coordinates;
      if (Array.isArray(pin.coordinates) && pin.coordinates.length >= 2) {
        coordinates = pin.coordinates;
      } else if (pin.latitude !== undefined && pin.longitude !== undefined) {
        coordinates = [parseFloat(pin.longitude), parseFloat(pin.latitude)];
      } else {
        console.error('Cannot determine coordinates for pin:', pin);
          return;
        }

      console.log(`Pin coordinates:`, coordinates);
      
      // Create a consistent pin data object
      const pinData = {
        id: pin.id || pin.camera_id || `pin-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        lat: parseFloat(pin.latitude || coordinates[1]),
        lng: parseFloat(pin.longitude || coordinates[0]),
        coordinates: coordinates,
        animal_type: pin.animal_type || pin.animalType || 'Unknown',
        status: pin.status || pin.stray_status || 'active',
        isCamera: isCamera,
        cameraId: pin.camera_id || pin.id,
        cameraName: pin.camera_name || pin.name || 'Camera',
        name: pin.name || pin.camera_name,
        
        // Camera specific properties
        perceptionRange: parseFloat(pin.perception_range || 30),
        viewingDirection: parseFloat(pin.viewing_direction || 0),
        viewingAngle: parseFloat(pin.viewing_angle || 60),
        conicalView: conicalView,

        // Add cone data if available
        coneData: pin.cone_coordinates ? {
          coordinates: pin.cone_coordinates,
          center: pin.cone_center || coordinates, // Use coordinates as fallback for center
          radius: parseFloat(pin.cone_radius || pin.perception_range || 30),
          direction: parseFloat(pin.cone_direction || pin.viewing_direction || 0),
          angle: parseFloat(pin.cone_angle || pin.viewing_angle || 60)
        } : null,

        detection_timestamp: pin.detection_timestamp,
        image_url: pin.image_url,
        snapshot_path: pin.snapshot_path,
        hls_url: pin.hls_url
      };

      console.log(`Created pin data object:`, pinData);

      const marker = createMarker(pinData);

      if (marker) {
        pinData.marker = marker;
        pinsList.value.push(pinData);
        console.log(`Added pin ID ${pin.id} to pinsList`);

        if (isCamera && pinData.perceptionRange) {
          if (pinData.conicalView === true && 
              pinData.viewingDirection !== undefined &&
              pinData.viewingAngle !== undefined) {
              console.log(`Adding conical view for camera ${pinData.id}`);
            
            // Use a short timeout to ensure the map is ready
            setTimeout(() => {
              // If we have cone data from the server, use it
              if (pinData.coneData) {
                console.log('Using stored cone data:', pinData.coneData);
                addConicalPerceptionRange(
                  pinData.coneData.center,
                  pinData.coneData.radius,
                  pinData.coneData.direction,
                  pinData.coneData.angle,
                  pinData.id
                );
              } else {
                // Calculate the cone center based on camera position and direction
                const radiusInDegrees = pinData.perceptionRange * 0.000009;
                const directionRad = (pinData.viewingDirection * Math.PI) / 180;
                const centerLng = pinData.lng + (radiusInDegrees * Math.sin(directionRad));
                const centerLat = pinData.lat + (radiusInDegrees * Math.cos(directionRad));
                
                console.log('Calculating new cone data:', {
                  center: [centerLng, centerLat],
                  radius: pinData.perceptionRange,
                  direction: pinData.viewingDirection,
                  angle: pinData.viewingAngle
                });
                
                addConicalPerceptionRange(
                  [centerLng, centerLat],
                  pinData.perceptionRange,
                  pinData.viewingDirection,
                  pinData.viewingAngle,
                  pinData.id
                );
              }
            }, 100);
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
}

// Fetch pins from the server and add them to the map
async function fetchPins() {
  try {
    console.log('Fetching pins from API...');
    const response = await axios.get('/pins');
    const pins = response.data.data;
    
    console.log(`Received ${pins.length} pins from API`);
    
    // Process the pins
    await processPins(pins);
    
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
    const pinId = pinData.id || pinData.cameraId;
    
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
          <button class="delete-pin-btn" data-pin-id="${pinId}">Delete Pin</button>
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
          <button class="delete-pin-btn" data-pin-id="${pinId}">Delete Pin</button>
        </div>
      `;
    }
    
    // Create and attach popup
    const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(popupHTML);
    markerInstance.setPopup(popup);
    
    // Add the delete button event listener immediately after popup is created
    popup.on('open', () => {
      const deleteBtn = popup.getElement().querySelector(`.delete-pin-btn[data-pin-id="${pinId}"]`);
      if (deleteBtn) {
        deleteBtn.addEventListener('click', async (e) => {
          e.preventDefault();
          e.stopPropagation();
          
          if (confirm('Are you sure you want to delete this pin?')) {
            console.log(`Delete button clicked for pin ID: ${pinId}`);
            try {
              const result = await deletePin(pinId, markerInstance);
              if (result.success) {
                console.log('Pin successfully deleted');
                popup.remove();
              } else {
                console.error('Error deleting pin:', result.error);
                alert('Error deleting pin: ' + (result.message || result.error || 'Unknown error'));
              }
            } catch (err) {
              console.error('Error in delete operation:', err);
              alert('Failed to delete pin. Please try again.');
            }
          }
        });
      } else {
        console.warn(`Delete button not found for pin ID: ${pinId}`);
      }
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
    
    // Remove marker from map if provided
    if (markerInstance) {
      markerInstance.remove();
    }
    
    // Find the pin in the pinsList by ID
    const pinIndex = pinsList.value.findIndex(pin => 
      pin.id === pinId || 
      pin.cameraId === pinId ||
      pin.camera_id === pinId
    );
    
    if (pinIndex === -1) {
      console.warn(`Pin with ID ${pinId} not found in pinsList`);
    } else {
      console.log(`Found pin at index ${pinIndex}:`, pinsList.value[pinIndex]);
      const pin = pinsList.value[pinIndex];
      
      // If it's a camera pin, remove its cone and perception range
      if (pin.isCamera || pin.animal_type === 'Camera') {
        // Remove the cone using our dedicated function
        removeCone(pinId);
        
        // Also check for perception circle
        const circleId = `perception-circle-${pinId}`;
        if (map.value.getLayer(circleId)) {
          map.value.removeLayer(circleId);
        }
        const circleSourceId = `perception-source-${pinId}`;
        if (map.value.getSource(circleSourceId)) {
          map.value.removeSource(circleSourceId);
        }
      }
      
      // Remove the pin's marker if not done already
      if (!markerInstance && pin.marker) {
        pin.marker.remove();
      }
      
      // Remove from local list
      pinsList.value.splice(pinIndex, 1);
      console.log(`Removed pin at index ${pinIndex} from pinsList`);
    }
    
    // Send delete request to server
    try {
      const response = await axios.delete(`/pins/${pinId}`);
      
      if (response.data.success) {
        console.log('Pin deleted successfully on server');
      } else {
        console.warn('Server response indicates pin deletion may have failed:', response.data.message);
      }
      
      return { success: true };
    } catch (apiError) {
      console.error('API Error when deleting pin:', apiError);
      // Pin was removed from UI but server delete failed
      return { 
        success: false, 
        message: 'Pin was removed from map but could not be deleted from server',
        error: apiError.message
      };
    }
  } catch (error) {
    console.error('Error in deletePin function:', error);
    return { success: false, error: error.message };
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

    // Generate a unique ID for this camera pin
    const cameraId = `camera-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;

    // The camera position is exactly where the user clicked
    const cameraPosition = coordinates;
    let coneData = null;

    if (cameraInfo.conicalView === true && 
        cameraInfo.viewingDirection !== undefined && 
        cameraInfo.viewingAngle !== undefined) {
      
      const perceptionRange = parseFloat(cameraInfo.perceptionRange || 30);
      const radiusInDegrees = perceptionRange * 0.000009;
      const directionRad = (cameraInfo.viewingDirection * Math.PI) / 180;
      
      // Calculate the cone center based on camera position and direction
      const centerLng = coordinates[0] + (radiusInDegrees * Math.sin(directionRad));
      const centerLat = coordinates[1] + (radiusInDegrees * Math.cos(directionRad));
      
      // Create cone data with the calculated center
      coneData = addConicalPerceptionRange(
        [centerLng, centerLat], // Center of the cone
        perceptionRange,
        cameraInfo.viewingDirection,
        cameraInfo.viewingAngle,
        cameraId
      );
    }

    // Create a detailed camera object for the marker
    const cameraData = {
      id: cameraId, // Use our generated ID
      coordinates: cameraPosition, // Use the exact click position
      camera_id: cameraInfo.id || '',
      rtmp_key: cameraInfo.rtmp_key || cameraInfo.id || '',
      camera_name: cameraInfo.name || '',
      location: cameraInfo.location || 'Unknown Location',
      hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : '',
      isCamera: true,
      animal_type: 'Camera', // Ensure this is set
      viewingDirection: cameraInfo.viewingDirection !== undefined ? parseFloat(cameraInfo.viewingDirection) : 0,
      viewingAngle: cameraInfo.viewingAngle !== undefined ? parseFloat(cameraInfo.viewingAngle) : 60,
      conicalView: cameraInfo.conicalView === true,
      perceptionRange: parseFloat(cameraInfo.perceptionRange || 30),
      original_id: cameraInfo.original_id || cameraInfo.id || '',
      coneData: coneData // Store the cone data
    };
    
    console.log('Creating camera marker with data:', cameraData);
    
    // First add to pins list so it's available for retrieval
    pinsList.value.push(cameraData);
    
    // Create the marker
    markerInstance = createMarker(cameraData);
    console.log('Marker instance created:', markerInstance);
    
    try {
      console.log('Sending API request to save camera pin...');
      
      // Create payload for the API
      const payload = {
        coordinates: cameraPosition, // Use the exact click position
        camera_id: cameraInfo.id || '',
        rtmp_key: cameraInfo.rtmp_key || cameraInfo.id || '',
        camera_name: cameraInfo.name || '',
        location: cameraInfo.location || 'Unknown Location',
        hls_url: cameraInfo.videoSrc && cameraInfo.videoSrc[0] ? cameraInfo.videoSrc[0] : '',
        viewing_direction: cameraInfo.viewingDirection !== undefined ? parseFloat(cameraInfo.viewingDirection) : 0,
        viewing_angle: cameraInfo.viewingAngle !== undefined ? parseFloat(cameraInfo.viewingAngle) : 60,
        conical_view: cameraInfo.conicalView === true,
        perception_range: parseFloat(cameraInfo.perceptionRange || 30),
        original_id: cameraInfo.original_id || cameraInfo.id || '',
        temp_id: cameraId, // Include our temporary ID
        // Add complete cone data as JSON strings
        cone_coordinates: coneData ? JSON.stringify(coneData.coordinates) : null,
        cone_center: coneData ? JSON.stringify(coneData.center) : null,
        cone_radius: coneData ? coneData.radius : null,
        cone_direction: coneData ? coneData.direction : null,
        cone_angle: coneData ? coneData.angle : null
      };
      
      console.log('Sending formatted payload to API:', payload);
      
      const response = await axios.post('/camera-pin', payload, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      });
      
      if (!response.data) {
        throw new Error('No response data received from server');
      }
      
      console.log("Camera pin API response:", response.data);
      
      // Update the pin in pinsList with any new data from the server
      if (response.data.pin && response.data.pin.id) {
        // Find the pin using temp ID
        const pinIndex = pinsList.value.findIndex(p => p.id === cameraId);
        
        if (pinIndex !== -1) {
          // Store old ID for reference to update visualization IDs
          const oldId = pinsList.value[pinIndex].id;
          
          // Update pin with server data including the new permanent ID and cone data
          pinsList.value[pinIndex] = {
            ...pinsList.value[pinIndex],
            id: response.data.pin.id,
            conicalView: Boolean(response.data.pin.conical_view),
            viewingDirection: parseFloat(response.data.pin.viewing_direction || 0),
            viewingAngle: parseFloat(response.data.pin.viewing_angle || 60),
            perceptionRange: parseFloat(response.data.pin.perception_range || 30),
            coneData: {
              coordinates: response.data.pin.cone_coordinates || coneData.coordinates,
              center: response.data.pin.cone_center || coneData.center,
              radius: parseFloat(response.data.pin.cone_radius || coneData.radius),
              direction: parseFloat(response.data.pin.cone_direction || coneData.direction),
              angle: parseFloat(response.data.pin.cone_angle || coneData.angle)
            }
          };
          
          console.log("Updated pin in pinsList with server data:", pinsList.value[pinIndex]);
          
          // If ID changed, update the visualization
          if (oldId !== response.data.pin.id) {
            console.log(`Pin ID changed from ${oldId} to ${response.data.pin.id}, updating visualizations`);
            
            // Remove the old visualization
            removeCone(oldId);
            
            // Add new visualization with correct ID
            if (pinsList.value[pinIndex].conicalView) {
              coneData = addConicalPerceptionRange(
                coordinates, // Original click point remains the center
                pinsList.value[pinIndex].perceptionRange,
                pinsList.value[pinIndex].viewingDirection,
                pinsList.value[pinIndex].viewingAngle,
                response.data.pin.id
              );
            }
            
            // Update the popup to reflect the new ID
            if (markerInstance && markerInstance.getPopup) {
              try {
                const popup = markerInstance.getPopup();
                if (popup && popup.getElement) {
                  const popupElement = popup.getElement();
                  if (popupElement) {
                    const deleteButton = popupElement.querySelector(`.delete-pin-btn[data-pin-id="${oldId}"]`);
                    if (deleteButton) {
                      deleteButton.setAttribute('data-pin-id', response.data.pin.id);
                    }
                  }
                }
              } catch (popupError) {
                console.warn('Error updating popup content:', popupError);
                // Continue execution even if popup update fails
              }
            }
          }
        }
      }
      
      // Return success with the cone data if available
      return { 
        success: true, 
        data: response.data,
        coneData: coneData 
      };
    } catch (apiError) {
      console.error('API Error when adding camera pin:', apiError);
      // Keep the pin on the map but indicate the save failed
      return { 
        success: false, 
        message: 'Pin added visually but failed to save to server',
        error: apiError.message,
        coneData: coneData // Still return the cone data if it was created
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
    if (!pinData || !pinData.animal_type) {
      throw new Error('Invalid pin data. Required fields: animal_type');
    }
    
    // If no coordinates are provided but we have camera info, place within the camera's cone
    if ((!pinData.lat || !pinData.lng) && (pinData.camera_id || pinData.cameraId || pinData.cameraInfo)) {
      // Get camera info either from pinData or from the coneMap
      const cameraInfo = pinData.cameraInfo || null;
      const cameraId = pinData.camera_id || pinData.cameraId;
      
      // Try to find the camera in our cone map
      let cameraFound = false;
      
      if (cameraInfo) {
        console.log(`Using provided camera info for pin placement:`, cameraInfo);
        
        // Extract camera coordinates
        let cameraCoords = null;
        if (cameraInfo.coordinates) {
          if (typeof cameraInfo.coordinates === 'object') {
            if ('lat' in cameraInfo.coordinates && 'lng' in cameraInfo.coordinates) {
              cameraCoords = {
                lat: parseFloat(cameraInfo.coordinates.lat),
                lng: parseFloat(cameraInfo.coordinates.lng)
              };
            }
          }
        }
        
        if (!cameraCoords) {
          console.warn('Invalid camera coordinates, cannot place pin');
          return null;
        }
        
        // Generate a position within the camera's cone or perception range
        const isConical = cameraInfo.conicalView === true;
        const perceptionRange = parseFloat(cameraInfo.perceptionRange || 30);
        
        // Convert perception range from meters to approximate degrees
        // 1 degree is about 111km at equator, so 1m is roughly 0.000009 degrees
        const baseRadius = perceptionRange * 0.000009;
        
        let offsetLat, offsetLng;
        
        if (isConical && cameraInfo.viewingDirection !== undefined && cameraInfo.viewingAngle !== undefined) {
          // Place within the conical view
          console.log(`Placing animal in conical view (direction: ${cameraInfo.viewingDirection}°, angle: ${cameraInfo.viewingAngle}°)`);
          
          const viewingDirection = parseFloat(cameraInfo.viewingDirection);
          const viewingAngle = parseFloat(cameraInfo.viewingAngle);
          
          // Calculate a position within the cone
          // Use a bell curve distribution for more natural placement
          const halfAngle = viewingAngle / 2;
          
          // Generate a normal random angle biased toward the center of the viewing cone
          const normalRandom = () => {
            // Box-Muller transform for normal distribution
            const u1 = Math.random();
            const u2 = Math.random();
            const z = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
            // Scale to portion of viewing angle and center on viewing direction
            return viewingDirection + (z * (viewingAngle / 5));
          };
          
          // Get angle biased toward center of cone
          let angle = normalRandom();
          
          // Ensure angle stays within cone boundaries
          const coneStart = viewingDirection - halfAngle;
          const coneEnd = viewingDirection + halfAngle;
          if (angle < coneStart) angle = coneStart + Math.random() * 5;
          if (angle > coneEnd) angle = coneEnd - Math.random() * 5;
          
          // Convert to radians
          const radian = angle * (Math.PI / 180);
          
          // Calculate distance from camera (denser in middle range)
          const minDistance = 0.2; // 20% of max range
          const maxDistance = 0.8; // 80% of max range
          
          // Bias toward middle distances (more animals in sweet spot of camera range)
          // You can adjust these parameters for different distributions
          const distanceFactor = minDistance + Math.pow(Math.random(), 0.7) * (maxDistance - minDistance);
          
          // Calculate offsets using trig
          offsetLng = baseRadius * distanceFactor * Math.sin(radian);
          offsetLat = baseRadius * distanceFactor * Math.cos(radian);
          
          // Add a little jitter for natural appearance
          const jitter = baseRadius * 0.03;
          offsetLat += jitter * (Math.random() * 2 - 1);
          offsetLng += jitter * (Math.random() * 2 - 1);
        } else {
          // Fallback to circular distribution around camera
          console.log('Placing animal in circular perception range');
          
          // Random angle
          const angle = Math.random() * 2 * Math.PI;
          
          // Random distance (more animals toward edges)
          const distanceFactor = 0.3 + Math.sqrt(Math.random()) * 0.6;
          
          // Calculate offsets
          offsetLng = baseRadius * distanceFactor * Math.sin(angle);
          offsetLat = baseRadius * distanceFactor * Math.cos(angle);
        }
        
        // Apply offsets to camera position
        pinData.lat = cameraCoords.lat + offsetLat;
        pinData.lng = cameraCoords.lng + offsetLng;
        
        cameraFound = true;
      } else if (cameraId && coneMap.value[cameraId]) {
        // Use stored cone data for this camera
        const cone = coneMap.value[cameraId];
        console.log(`Found cone data for camera ${cameraId}:`, cone);
        
        // Generate a random point within the cone
        const randomPoint = getRandomPointInCone(cone);
        pinData.lng = randomPoint[0];
        pinData.lat = randomPoint[1];
        
        cameraFound = true;
      }
      
      if (!cameraFound) {
        console.warn(`No camera found for ID ${cameraId}, cannot place pin within cone`);
        // Set default coordinates if we couldn't find camera info
        if (!pinData.lat || !pinData.lng) {
          pinData.lat = 14.631141;
          pinData.lng = 121.039295;
        }
      }
    }
    
    // Ensure coordinates are valid
    if (!pinData.lat || !pinData.lng || isNaN(pinData.lat) || isNaN(pinData.lng)) {
      throw new Error('Invalid coordinates for animal pin');
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
      id: pinData.id || `animal-${Date.now()}`,
      camera_id: pinData.camera_id || pinData.cameraId,
      detection_timestamp: pinData.detection_timestamp || new Date().toISOString(),
      is_automated: pinData.is_automated === true,
      stream_id: pinData.stream_id
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

// Function to add a conical perception range to the map for a camera
function addConicalPerceptionRange(coordinates, rangeInMeters, direction, angle, cameraId) {
  const coneId = `cone-${cameraId}`;
  const sourceId = `cone-source-${cameraId}`;

  try {
    if (!map.value) {
      console.error('Map not initialized, cannot add conical perception range');
      return;
    }

    console.log(`Adding conical perception for camera ${cameraId}`, {
      coordinates,
      rangeInMeters,
      direction,
      angle
    });

    // Wait for map style to load if needed
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

    const radiusInDegrees = rangeInMeters * 0.000009;
    const [lng, lat] = Array.isArray(coordinates) ? coordinates : [coordinates.lng, coordinates.lat];
    const directionRad = (direction * Math.PI) / 180;
    const halfAngleRad = (angle / 2 * Math.PI) / 180;

    // Generate cone points
    const conePoints = [[lng, lat]];
    const numPoints = 30;
    const startAngle = directionRad - halfAngleRad;
    const endAngle = directionRad + halfAngleRad;

    for (let i = 0; i <= numPoints; i++) {
      const currentAngle = startAngle + (i / numPoints) * (endAngle - startAngle);
      const x = lng + radiusInDegrees * Math.sin(currentAngle);
      const y = lat + radiusInDegrees * Math.cos(currentAngle);
      conePoints.push([x, y]);
    }

    conePoints.push([lng, lat]);

    // Create GeoJSON feature for the cone
    const conePolygon = {
      type: 'Feature',
      properties: { 
        camera_id: cameraId, 
        range_meters: rangeInMeters, 
        direction, 
        angle 
      },
      geometry: { 
        type: 'Polygon', 
        coordinates: [conePoints] 
      }
    };

    // Add the source
    map.value.addSource(sourceId, {
      type: 'geojson',
      data: conePolygon
    });

    // Add the layer
    map.value.addLayer({
      id: coneId,
      type: 'fill',
      source: sourceId,
      layout: {},
      paint: {
        'fill-color': '#4285F4',
        'fill-opacity': 0.25,
        'fill-outline-color': '#4285F4',
        'fill-translate': [0, 0] // Ensure no translation
      }
    });

    // Store the cone definition
    coneMap.value[cameraId] = {
      center: [lng, lat],
      radius: rangeInMeters,
      direction,
      angle,
      polygon: conePolygon.geometry.coordinates[0],
      sourceId,
      layerId: coneId
    };

    return {
      coneId,
      sourceId,
      cameraId,
      coordinates,
      radius: rangeInMeters,
      direction,
      angle
    };
  } catch (error) {
    console.error('Error adding conical perception range:', error);
    return null;
  }
}

// Function to redraw all cones
function redrawAllCones() {
  console.log('Redrawing all cones...');
  
  if (!map.value) {
    console.error('Map not initialized, cannot redraw cones');
    return;
  }

  // Remove all existing cone layers and sources
  Object.values(coneMap.value).forEach(cone => {
    if (map.value.getLayer(cone.layerId)) {
      map.value.removeLayer(cone.layerId);
    }
    if (map.value.getSource(cone.sourceId)) {
      map.value.removeSource(cone.sourceId);
    }
  });

  // Redraw all cones
  Object.entries(coneMap.value).forEach(([cameraId, cone]) => {
    addConicalPerceptionRange(
      cone.center,
      cone.radius,
      cone.direction,
      cone.angle,
      cameraId
    );
  });
}

// Function to remove a specific cone
function removeCone(cameraId) {
  if (!map.value) return;

  const cone = coneMap.value[cameraId];
  if (!cone) return;

  if (map.value.getLayer(cone.layerId)) {
    map.value.removeLayer(cone.layerId);
  }
  if (map.value.getSource(cone.sourceId)) {
    map.value.removeSource(cone.sourceId);
  }

  delete coneMap.value[cameraId];
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
    
    // Add a circle layer with more accurate scaling
    map.value.addLayer({
      id: circleId,
      type: 'circle',
      source: sourceId,
      paint: {
        'circle-radius': {
          stops: [
            [10, radiusInDegrees * 100000], // Reduced scaling factor
            [15, radiusInDegrees * 300000], // Reduced scaling factor
            [20, radiusInDegrees * 1000000] // Reduced scaling factor
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

function getRandomPointInCone(cone) {
  const { center, radius, direction, angle } = cone;

  const randomRadius = Math.random() * radius * 0.9; // stay within the cone
  const randomAngleOffset = (Math.random() - 0.5) * angle; // centered at direction

  const finalAngle = direction + randomAngleOffset;
  const rad = finalAngle * (Math.PI / 180);

  const dx = randomRadius * 0.000009 * Math.sin(rad);
  const dy = randomRadius * 0.000009 * Math.cos(rad);

  const [lng, lat] = center;
  return [lng + dx, lat + dy];
}

async function checkForDetectedAnimals() {
  try {
    console.log('Checking for new animal detections from API...');
    lastApiCheckTime.value = new Date();
    
    // Fetch the detections from the API
    const response = await axios.get('https://straysafe.me/api2/detected');
    const data = response.data;
    
    console.log('Received animal detections:', data);
    
    if (!data || !data.detected_animals || data.detected_animals.length === 0) {
      console.log('No animal detections found');
      return;
    }
    
    // Get camera pins to map stream_id to camera positions
    const cameraPins = await getCameraPinLocations();
    console.log('Available camera pins for mapping:', cameraPins);
    
    // Create a map of stream IDs to camera pins
    const streamToCameraMap = {};
    cameraPins.forEach(pin => {
      // Match cameras using various IDs
      const possibleIds = [
        pin.id, 
        pin.cameraId, 
        pin.rtmp_key, 
        pin.original_id,
        `cam-${pin.id}`,
        `cam-${pin.cameraId}`,
        `cam-${pin.rtmp_key}`,
        pin.rtmp_key?.replace('cam-', '') || '',
        pin.original_id?.replace('cam-', '') || ''
      ].filter(id => id); // Filter out undefined/null values
      
      possibleIds.forEach(id => {
        streamToCameraMap[id] = pin;
      });
    });
    
    console.log('Stream to camera mapping:', streamToCameraMap);
    
    // Process each detected animal
    for (const animal of data.detected_animals) {
      // Skip if this detection has already been processed
      if (processedDetections.value.has(animal.id)) {
        console.log(`Skipping already processed detection: ${animal.id}`);
        continue;
      }
      
      // Find the corresponding camera pin for this detection's stream_id
      const cameraPin = streamToCameraMap[animal.stream_id] || 
                       streamToCameraMap[animal.stream_id.replace('cam-', '')] ||
                       streamToCameraMap[`cam-${animal.stream_id}`];
      
      if (!cameraPin) {
        console.log(`No camera pin found for stream_id: ${animal.stream_id}`);
        continue;
      }
      
      console.log(`Creating pin for ${animal.animal_type} detected on ${animal.stream_id} (matched to camera ${cameraPin.id})`);
      
      // Create a description based on the detection data
      let description = `${animal.animal_type} detected by ${cameraPin.name || 'Camera'}`;
      if (animal.classification) {
        description += ` (${animal.classification})`;
      }
      if (animal.owner_id) {
        description += ` - Owner: ${animal.owner_id}`;
      }
      
      // Create the pin data
      const pinData = {
        id: animal.id, // Use the detection ID for deduplication
        animal_type: animal.animal_type,
        description: description,
        image_url: animal.image_url || null,
        detection_timestamp: animal.timestamp,
        status: animal.classification || 'active',
        is_automated: true,
        is_camera: false,
        camera_id: cameraPin.id,
        cameraId: cameraPin.id,
        stream_id: animal.stream_id,
        // Pass camera info for proper placement within cone
        cameraInfo: {
          ...cameraPin,
          conicalView: cameraPin.conicalView,
          viewingDirection: cameraPin.viewingDirection,
          viewingAngle: cameraPin.viewingAngle,
          perceptionRange: cameraPin.perceptionRange,
          coordinates: cameraPin.coordinates
        }
      };
      
      // Add the animal pin - it will be automatically placed within the camera's cone
      try {
        const result = await addAnimalPin(pinData);
        if (result && result.success !== false) {
          // Mark this detection as processed
          processedDetections.value.add(animal.id);
          console.log(`Successfully added animal pin for detection ${animal.id}`);
          
          // Update stats
          mapStats.value.totalSightings++;
          if (animal.animal_type.toLowerCase() === 'dog') {
            mapStats.value.dogSightings++;
          } else if (animal.animal_type.toLowerCase() === 'cat') {
            mapStats.value.catSightings++;
          }
        }
      } catch (error) {
        console.error(`Failed to add animal pin for detection ${animal.id}:`, error);
      }
    }
  } catch (error) {
    console.error('Error checking for detected animals:', error);
  }
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
