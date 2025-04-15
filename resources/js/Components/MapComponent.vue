<script setup>
import { onMounted, ref, inject, defineExpose, onUnmounted, watch, computed } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import axios from 'axios';
// Import MapboxDraw for drawing polygons
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';

// Define props
const props = defineProps({
  userAreas: {
    type: Array,
    default: () => []
  },
  isMapOwner: {
    type: Boolean,
    default: false
  },
  userMapId: {
    type: [String, Number],
    default: null
  },
  mapName: {
    type: [String, Number],
    default: null
  },
  mapAccessCode: {
    type: [String, Number],
    default: null
  },
  authUser: {
    type: Object,
    default: null
  }
});

// Define emits
const emit = defineEmits(['map-ready', 'draw-complete', 'map-accessed', 'map-created']);

// Get the global dark mode state
const isDarkMode = inject('isDarkMode', ref(false));

// Map container and instance
const mapContainer = ref(null);
const map = ref(null);
const pinsList = ref([]); // Stores the list of pins
const mapLoadError = ref(false);
const mapLoadTimeout = ref(null);
// Add draw control reference
const draw = ref(null);
// Store user-created areas
const userAreas = ref([]);

// User areas panel state
const isUserAreasPanelExpanded = ref(false);
const isFocusedOnArea = ref(false);
const focusedAreaId = ref(null);
const activeAreaRestore = ref(null);

// User map state
const showMapSelector = ref(false);
const accessCode = ref('');
const accessCodeError = ref('');
const isCreatingMap = ref(false);
const newMapName = ref('');
const newMapDescription = ref('');
const isProcessingMapOperation = ref(false);

// Manual animal pin state
const isAddingAnimalPin = ref(false);
const animalPinType = ref('dog'); // Default to dog
const animalPinDialogOpen = ref(false);
const animalPinForm = ref({
  animal_type: 'dog',
  description: 'Stray dog sighting',
  status: 'active',
  image_url: ''
});

// Add these variables to the setup script section, near the other map-related refs
const currentZoom = ref(0);
const minPinZoomLevel = ref(11); // Minimum zoom level to show pins
const showAreaLabels = ref(true);
const areaEditMode = ref(false);
const areaBeingEdited = ref(null);
const areaNameEdit = ref('');

// Watch for changes in the isDarkMode state
watch(isDarkMode, () => {
  // Update area labels with the new theme
  updateAreaLabels();

  // If we need to restyle other elements based on dark mode, do it here
});

// Toggle the user areas panel
function toggleUserAreasPanel() {
  isUserAreasPanelExpanded.value = !isUserAreasPanelExpanded.value;
}

// Focus on a specific area
function focusOnArea(featureId) {
  // If we're already focused on this area, return
  if (focusedAreaId.value === featureId) return;

  // If we have an active restore function, call it to restore all areas
  if (activeAreaRestore.value) {
    activeAreaRestore.value();
    activeAreaRestore.value = null;
  }

  // Focus on the new area
  const result = focusOnUserArea(featureId);

  if (result) {
    focusedAreaId.value = featureId;
    isFocusedOnArea.value = true;

    // Store a function to restore all areas when needed
    activeAreaRestore.value = () => {
      // Show all areas
      showAllUserAreas();
      return true;
    };
  }
}

// Show all areas
function showAllAreas() {
  // If we have an active restore function, call it
  if (activeAreaRestore.value) {
    activeAreaRestore.value();
    activeAreaRestore.value = null;
  }

  // Reset the state
  focusedAreaId.value = null;
  isFocusedOnArea.value = false;

  // Make sure all areas are shown
  displayUserAreas();
}

// Watch for changes in the props.userAreas
watch(() => props.userAreas, (newAreas) => {
  if (newAreas && newAreas.length > 0) {
    console.log('Received updated user areas from parent:', newAreas);
    userAreas.value = newAreas;
    if (map.value && map.value.loaded()) {
      displayUserAreas();
    }
  }
}, { deep: true });

// Watch for changes in the props.userMapId to reload areas when map changes
watch(() => props.userMapId, (newMapId, oldMapId) => {
  if (newMapId !== oldMapId) {
    console.log('User map ID changed, reloading areas for map ID:', newMapId);
    if (map.value && map.value.loaded()) {
      // Clear existing areas
      if (draw.value) {
        draw.value.deleteAll();
      }
      // Fetch areas for the new map
      fetchUserAreas();
    }
  }
});

// Mapbox token
const mapboxToken = 'pk.eyJ1IjoiMS1heWFub24iLCJhIjoiY20ycnAzZW5pMWZpZTJpcThpeTJjdDU1NCJ9.7AVb_LJf6sOtb-QAxwR-hg';

// Get the CSRF token from the meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

// Set the CSRF token as a common header for all Axios requests
if (csrfToken) {
  axios.defaults.headers.common['X-CSRF-TOKEN'] = csrfToken;
}

// Store cone definitions globally
const coneMap = ref({});

// Set up states for detection monitoring
const processedDetections = ref(new Set());
const lastApiCheckTime = ref(null);
const mapStats = ref({
  totalSightings: 0,
  dogSightings: 0,
  catSightings: 0
});

// Initialize map when component mounts
onMounted(() => {
  console.log('MapComponent mounted, initializing map...');
  initializeMap();
});

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
      center: [120.9842, 14.5995], // Manila, Philippines coordinates
      zoom: 12,
      attributionControl: false,
    });

    map.value = new mapboxgl.Map({
      container: mapContainer.value,
      style: isDarkMode.value ? 'mapbox://styles/mapbox/dark-v10' : 'mapbox://styles/1-ayanon/cm2rp9idm00as01qwcq9ihoyr',
      center: [120.9842, 14.5995], // Manila, Philippines coordinates
      zoom: 12,
      attributionControl: false,
    });

    console.log('Map instance created:', map.value);

    // Add navigation control
    map.value.addControl(new mapboxgl.NavigationControl(), 'top-right');
    console.log('Navigation control added');

    // Add scale control
    map.value.addControl(new mapboxgl.ScaleControl(), 'bottom-left');
    console.log('Scale control added');

    // Initialize and add the draw control
    draw.value = new MapboxDraw({
      displayControlsDefault: false,
      controls: {
        polygon: true,
        trash: true
      },
      // Custom styling for the drawn polygons
      styles: [
        {
          'id': 'gl-draw-polygon-fill-inactive',
          'type': 'fill',
          'filter': ['all', ['==', 'active', 'false'], ['==', '$type', 'Polygon']],
          'paint': {
            'fill-color': isDarkMode.value ? '#5a3fc0' : '#3f51b5',
            'fill-outline-color': isDarkMode.value ? '#8e72dd' : '#7986cb',
            'fill-opacity': 0.4
          }
        },
        {
          'id': 'gl-draw-polygon-fill-active',
          'type': 'fill',
          'filter': ['all', ['==', 'active', 'true'], ['==', '$type', 'Polygon']],
          'paint': {
            'fill-color': '#3bb2d0',
            'fill-outline-color': '#3bb2d0',
            'fill-opacity': 0.7
          }
        },
        {
          'id': 'gl-draw-polygon-midpoint',
          'type': 'circle',
          'filter': ['all', ['==', '$type', 'Point'], ['==', 'meta', 'midpoint']],
          'paint': {
            'circle-radius': 3,
            'circle-color': '#fbb03b'
          }
        },
        {
          'id': 'gl-draw-polygon-stroke-inactive',
          'type': 'line',
          'filter': ['all', ['==', 'active', 'false'], ['==', '$type', 'Polygon']],
          'layout': {
            'line-cap': 'round',
            'line-join': 'round'
          },
          'paint': {
            'line-color': isDarkMode.value ? '#8e72dd' : '#7986cb',
            'line-width': 2
          }
        },
        {
          'id': 'gl-draw-polygon-stroke-active',
          'type': 'line',
          'filter': ['all', ['==', 'active', 'true'], ['==', '$type', 'Polygon']],
          'layout': {
            'line-cap': 'round',
            'line-join': 'round'
          },
          'paint': {
            'line-color': '#3bb2d0',
            'line-dasharray': [0.2, 2],
            'line-width': 2
          }
        },
        {
          'id': 'gl-draw-line-inactive',
          'type': 'line',
          'filter': ['all', ['==', 'active', 'false'], ['==', '$type', 'LineString']],
          'layout': {
            'line-cap': 'round',
            'line-join': 'round'
          },
          'paint': {
            'line-color': '#7986cb',
            'line-width': 2
          }
        },
        {
          'id': 'gl-draw-polygon-and-line-vertex-stroke-inactive',
          'type': 'circle',
          'filter': ['all', ['==', 'meta', 'vertex'], ['==', '$type', 'Point']],
          'paint': {
            'circle-radius': 5,
            'circle-color': '#fff'
          }
        },
        {
          'id': 'gl-draw-polygon-and-line-vertex-inactive',
          'type': 'circle',
          'filter': ['all', ['==', 'meta', 'vertex'], ['==', '$type', 'Point']],
          'paint': {
            'circle-radius': 3,
            'circle-color': '#7986cb'
          }
        }
      ]
    });

    map.value.addControl(draw.value, 'top-left');
    console.log('Draw control added');

    // Set up map click handler for pin placement
    map.value.on('click', handleMapClick);
    console.log('Map click handler set up');

    // Add draw event listeners
    map.value.on('draw.create', handleDrawCreate);
    map.value.on('draw.update', handleDrawUpdate);
    map.value.on('draw.delete', handleDrawDelete);
    console.log('Draw event listeners added');

    // Wait for map to load
    map.value.on('load', async () => {
      console.log('Map loaded event triggered, applying loading delay...');

      // Fetch initial pins and add all cones before displaying the map
      await fetchPins();

      // Add artificial delay to ensure cones are loaded and visible
      console.log('Adding delay to ensure all cones are loaded...');
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Ensure all camera cones are added to the map
      console.log('Forcing cone rendering...');
      if (map.value && map.value.isStyleLoaded()) {
        // Re-add all cones to ensure they're loaded
        addAllCameraCones();

        // Add another small delay to ensure cones are rendered
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      console.log('Map fully loaded and cones rendered successfully!');

      // Clear timeout since map loaded successfully
      if (mapLoadTimeout.value) {
        clearTimeout(mapLoadTimeout.value);
        mapLoadTimeout.value = null;
      }

      // Fetch user areas if not provided via props
      if (!props.userAreas || props.userAreas.length === 0) {
        await fetchUserAreas();
      } else {
        userAreas.value = props.userAreas;
        displayUserAreas();
      }

      // Set initial zoom level
      currentZoom.value = map.value.getZoom();

      // Add zoom change listener
      map.value.on('zoom', handleMapZoom);

      // Initialize area labels
      updateAreaLabels();

      // Re-add cones on style reload to ensure field of view persists
      map.value.on('styledata', () => {
        console.log('Map styledata event fired, re-adding camera cones');
        addAllCameraCones();
      });

      // Emit map-ready event to parent
      emit('map-ready');
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

// Draw feature handlers
function handleDrawCreate(e) {
  const features = e.features;
  console.log('Created features:', features);

  // Emit the draw-complete event to the parent
  if (features && features.length > 0) {
    emit('draw-complete', features[0]);
  }
}

function handleDrawUpdate(e) {
  const features = e.features;
  console.log('Updated features:', features);
  // Find and update the area
  features.forEach(feature => {
    saveUserArea(feature, true);
  });
}

function handleDrawDelete(e) {
  const features = e.features;
  console.log('Deleted features:', features);
  // Delete the areas from database
  features.forEach(feature => {
    deleteUserArea(feature.id);
  });
}

// Save user-created area to database
async function saveUserArea(feature, isUpdate = false) {
  try {
    console.log(`${isUpdate ? 'Updating' : 'Saving'} user area:`, feature);

    // Format data for API
    const areaData = {
      feature_id: feature.id,
      name: feature.properties.name || `Area ${new Date().toLocaleString()}`,
      description: feature.properties.description || '',
      geometry: JSON.stringify(feature.geometry),
      properties: JSON.stringify(feature.properties || {}),
      user_map_id: props.userMapId // Add the user_map_id from props
    };

    console.log('Area data to send:', areaData);

    // Make API request
    let response;
    if (isUpdate) {
      response = await axios.put(`/api/user-areas/${feature.id}`, areaData);
    } else {
      response = await axios.post('/api/user-areas', areaData);
    }

    console.log(`Area ${isUpdate ? 'updated' : 'saved'} successfully:`, response.data);

    // Update local state
    const areaIndex = userAreas.value.findIndex(area => area.feature_id === feature.id);
    if (areaIndex >= 0) {
      userAreas.value[areaIndex] = response.data;
    } else {
      userAreas.value.push(response.data);
    }

    return response.data;
  } catch (error) {
    console.error(`Error ${isUpdate ? 'updating' : 'saving'} user area:`, error);
    alert(`Failed to ${isUpdate ? 'update' : 'save'} area. Please try again.`);
    return null;
  }
}

// Delete user area from database
async function deleteUserArea(featureId) {
  try {
    console.log('Deleting user area:', featureId);

    // Make API request
    const response = await axios.delete(`/api/user-areas/${featureId}`);

    console.log('Area deleted successfully:', response.data);

    // Update local state
    userAreas.value = userAreas.value.filter(area => area.feature_id !== featureId);

    return true;
  } catch (error) {
    console.error('Error deleting user area:', error);
    alert('Failed to delete area. Please try again.');
    return false;
  }
}

// Fetch user areas from database
async function fetchUserAreas() {
  try {
    console.log('Fetching user areas from database');

    // Prepare URL with query params if we have a user map ID
    let url = '/api/user-areas';
    if (props.userMapId) {
      url += `?user_map_id=${props.userMapId}`;
      console.log('Filtering areas by user map ID:', props.userMapId);
    }

    // Make API request
    const response = await axios.get(url);

    console.log('User areas fetched successfully:', response.data);

    // Update local state
    userAreas.value = response.data;

    // Add areas to map
    displayUserAreas();

    return response.data;
  } catch (error) {
    console.error('Error fetching user areas:', error);
    return [];
  }
}

// Display user areas on the map
function displayUserAreas() {
  if (!map.value || !draw.value) return;

  console.log('Displaying user areas on map:', userAreas.value);

  // Create features to add to draw
  const featuresToAdd = userAreas.value.map(area => {
    return {
      id: area.feature_id,
      type: 'Feature',
      properties: JSON.parse(area.properties || '{}'),
      geometry: JSON.parse(area.geometry)
    };
  });

  // Add all features to draw
  draw.value.add({
    type: 'FeatureCollection',
    features: featuresToAdd
  });

  // Update area labels after areas are added
  updateAreaLabels();
}

// Enable drawing mode
function enableDrawingMode(type = 'polygon', zoom = null) {
  if (!map.value || !draw.value) return false;

  console.log(`Enabling ${type} drawing mode${zoom ? ' with zoom level: ' + zoom : ''}`);

  // Set zoom level if provided
  if (zoom !== null && typeof zoom === 'number') {
    map.value.setZoom(zoom);
  }

  // Change cursor to indicate drawing mode
  map.value.getCanvas().style.cursor = 'crosshair';

  // Activate drawing mode based on type
  if (type === 'polygon') {
    draw.value.changeMode('draw_polygon');
  } else if (type === 'line') {
    draw.value.changeMode('draw_line_string');
  } else if (type === 'point') {
    draw.value.changeMode('draw_point');
  } else {
    // Default to polygon
    draw.value.changeMode('draw_polygon');
  }

  return true;
}

// Disable drawing mode
function disableDrawingMode() {
  if (!map.value || !draw.value) return false;

  console.log('Disabling drawing mode');

  // Reset cursor
  map.value.getCanvas().style.cursor = '';

  // Switch to simple_select mode
  draw.value.changeMode('simple_select');

  return true;
}

// Cancel drawing
function cancelDrawing() {
  if (!map.value || !draw.value) return false;

  console.log('Canceling current drawing');

  // Delete the current feature being drawn
  draw.value.trash();

  // Reset cursor and mode
  map.value.getCanvas().style.cursor = '';
  draw.value.changeMode('simple_select');

  return true;
}

// Set properties for a user area
function setUserAreaProperties(featureId, properties) {
  if (!map.value || !draw.value) return false;

  try {
    // Get the feature
    const feature = draw.value.get(featureId);
    if (!feature) {
      console.warn(`Feature with ID ${featureId} not found`);
      return false;
    }

    // Update properties
    Object.keys(properties).forEach(key => {
      feature.properties[key] = properties[key];
    });

    // Update the feature
    draw.value.add(feature);

    // Save to database
    saveUserArea(feature, true);

    return true;
  } catch (error) {
    console.error('Error setting user area properties:', error);
    return false;
  }
}

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
    console.log('Pin placement mode is active and callback is registered');

    const coordinates = [e.lngLat.lng, e.lngLat.lat];
    console.log('Calling pin placement callback with coordinates:', coordinates);

    // Call the callback with the clicked coordinates
    placementCallback.value(coordinates);
  } else if (isPlacingCameraPin.value && !placementCallback.value) {
    console.error('Pin placement mode is active but no callback is registered');
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

  // First, process all pins to create markers and add to pinsList
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

        // Ensure we have complete cone data from all possible sources
        coneData: pin.cone_coordinates || pin.coneData ? {
          coordinates: pin.cone_coordinates || (pin.coneData ? pin.coneData.coordinates : null),
          center: pin.cone_center || (pin.coneData ? pin.coneData.center : coordinates),
          radius: parseFloat(pin.cone_radius || (pin.coneData ? pin.coneData.radius : pin.perception_range || 30)),
          direction: parseFloat(pin.cone_direction || (pin.coneData ? pin.coneData.direction : pin.viewing_direction || 0)),
          angle: parseFloat(pin.cone_angle || (pin.coneData ? pin.coneData.angle : pin.viewing_angle || 60))
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
      } else {
        console.error(`Failed to create marker for pin ID ${pin.id}`);
      }
    } catch (pinError) {
      console.error('Error processing pin:', pin, pinError);
    }
  });

  console.log(`Loaded ${pinsList.value.length} pins into pinsList`);

  // Ensure the map style is loaded before adding cones
  if (!map.value.isStyleLoaded()) {
    console.log('Map style not yet loaded, waiting...');
    map.value.once('styledata', () => {
      console.log('Map style loaded, re-adding cones.');
      addAllCameraCones();
    });
    return;
  }

  // Add cones immediately if style is already loaded
  console.log('Map style already loaded, adding cones.');
  pinsList.value.forEach(pinData => {
    if (pinData.isCamera && pinData.perceptionRange && pinData.conicalView) {
      console.log(`Adding cone for camera ${pinData.id}`);
      addConicalPerceptionRange(
        pinData.coneData ? pinData.coneData.center : pinData.coordinates,
        pinData.perceptionRange,
        pinData.viewingDirection,
        pinData.viewingAngle,
        pinData.id
      );
    }
  });
}

// Function to add all camera cones for loaded pins
async function addAllCameraCones() {
  console.log('Adding cones for all camera pins...');

  if (!map.value) {
    console.error('Map is not initialized, cannot add cones.');
    return;
  }

  // Make sure the map style is loaded
  if (!map.value.isStyleLoaded()) {
    console.log('Map style not yet loaded, waiting...');
    await new Promise(resolve => {
      map.value.once('styledata', () => {
        console.log('Map style loaded, proceeding to add cones.');
        resolve();
      });
    });
  }

  // Count how many cones we're going to add
  const cameraPins = pinsList.value.filter(pin =>
    pin.isCamera && pin.perceptionRange && pin.conicalView === true &&
    pin.viewingDirection !== undefined && pin.viewingAngle !== undefined
  );

  console.log(`Found ${cameraPins.length} camera pins with cones to add`);

  // Add cones for each camera with a small delay between each
  for (const pinData of cameraPins) {
    console.log(`Adding cone for camera ${pinData.id}`);

    try {
      // If we have cone data from the server, use it
      if (pinData.coneData && pinData.coneData.center) {
        console.log('Using stored cone data for camera', pinData.id, ':', pinData.coneData);
        await addConicalPerceptionRange(
          pinData.coneData.center,
          pinData.coneData.radius,
          pinData.coneData.direction,
          pinData.coneData.angle,
          pinData.id
        );
      } else {
        // Calculate the cone center based on camera position and direction
        const centerCoords = calculateConeCenter(
          pinData.lng,
          pinData.lat,
          pinData.perceptionRange,
          pinData.viewingDirection
        );

        console.log('Calculating new cone data for camera', pinData.id, ':', {
          center: centerCoords,
          radius: pinData.perceptionRange,
          direction: pinData.viewingDirection,
          angle: pinData.viewingAngle
        });

        await addConicalPerceptionRange(
          centerCoords,
          pinData.perceptionRange,
          pinData.viewingDirection,
          pinData.viewingAngle,
          pinData.id
        );
      }

      // Add a small delay between adding cones to avoid race conditions
      await new Promise(resolve => setTimeout(resolve, 100));
    } catch (error) {
      console.error(`Error adding cone for camera ${pinData.id}:`, error);
    }
  }

  console.log('Finished adding all camera cones.');
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
        // Remove existing event listeners to prevent duplicates
        deleteBtn.replaceWith(deleteBtn.cloneNode(true));

        // Get the fresh button reference after replacement
        const freshDeleteBtn = popup.getElement().querySelector(`.delete-pin-btn[data-pin-id="${pinId}"]`);

        // Add the event listener to the fresh button
        freshDeleteBtn.addEventListener('click', async (e) => {
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

// Get locations of all camera pins on the map
function getCameraPinLocations() {
  try {
    console.log('Getting camera pin locations');

    // Filter the pins list to only include camera pins
    const cameraPins = pinsList.value.filter(pin =>
      pin.isCamera === true ||
      pin.animal_type === 'Camera' ||
      pin.animalType === 'Camera'
    );

    console.log(`Found ${cameraPins.length} camera pins`);

    // Map the pins to a simpler format with just the essential information
    return cameraPins.map(pin => {
      return {
        id: pin.id || pin.cameraId,
        cameraId: pin.camera_id || pin.cameraId || pin.id,
        name: pin.cameraName || pin.name || 'Camera',
        coordinates: pin.coordinates || [pin.lng, pin.lat],
        perceptionRange: pin.perceptionRange || 30,
        viewingDirection: pin.viewingDirection,
        viewingAngle: pin.viewingAngle,
        conicalView: pin.conicalView
      };
    });
  } catch (error) {
    console.error('Error getting camera pin locations:', error);
    return [];
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
  getCurrentZoom: () => map.value ? map.value.getZoom() : null,

  // New user area methods
  enableDrawingMode,
  disableDrawingMode,
  cancelDrawing,
  saveUserArea,
  deleteUserArea,
  setUserAreaProperties,
  getUserAreas: () => userAreas.value,
  navigateToLocation,
  focusOnUserArea,
  // Add a method to restore all user areas (useful after focusing on one)
  showAllUserAreas: () => {
    if (!map.value || !draw.value) return false;

    try {
      // Redisplay all areas from our local state
      displayUserAreas();
      return true;
    } catch (error) {
      console.error('Error restoring all user areas:', error);
      return false;
    }
  },
  addStandaloneCone, // Add the new function to the exposed methods
  removeAllStandaloneCones, // Add the new function to the exposed methods

  // Manual animal pin methods
  enableAnimalPinPlacement,
  cancelAnimalPinPlacement
});

// Function to add a conical perception range to the map for a camera
async function addConicalPerceptionRange(coordinates, rangeInMeters, direction, angle, cameraId) {
  const uniqueId = `cone-${cameraId}-${Date.now()}`;
  const coneId = `cone-layer-${cameraId}`;
  const sourceId = `cone-source-${cameraId}`;
  const arrowLayerId = `cone-arrow-layer-${cameraId}`;
  const arrowSourceId = `cone-arrow-source-${cameraId}`;

  try {
    if (!map.value) {
      console.error('Map not initialized, cannot add conical perception range');
      return null;
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
      await new Promise(resolve => {
        map.value.once('styledata', () => {
          console.log('Map style loaded, proceeding with cone addition.');
          resolve();
        });
      });
    }

    // Log existing layers and sources before removal
    console.log(`Before removal - Checking if layer ${coneId} exists:`, map.value.getLayer(coneId) ? 'Yes' : 'No');
    console.log(`Before removal - Checking if source ${sourceId} exists:`, map.value.getSource(sourceId) ? 'Yes' : 'No');

    // Remove any existing layers BEFORE removing sources
    try {
      // Always remove layers first, in correct order
      if (map.value.getLayer(arrowLayerId)) {
        console.log(`Removing existing arrow layer: ${arrowLayerId}`);
        map.value.removeLayer(arrowLayerId);
      }

      if (map.value.getLayer(`${coneId}-line`)) {
        console.log(`Removing existing line layer: ${coneId}-line`);
        map.value.removeLayer(`${coneId}-line`);
      }

      if (map.value.getLayer(coneId)) {
        console.log(`Removing existing layer: ${coneId}`);
        map.value.removeLayer(coneId);
      }

      // Now safe to remove sources
      if (map.value.getSource(arrowSourceId)) {
        console.log(`Removing existing arrow source: ${arrowSourceId}`);
        map.value.removeSource(arrowSourceId);
      }

      if (map.value.getSource(sourceId)) {
        console.log(`Removing existing source: ${sourceId}`);
        map.value.removeSource(sourceId);
      }
    } catch (removalError) {
      console.error('Error removing existing layers/sources:', removalError);
      // Continue execution - we'll try to add new layers anyway
    }

    // Use our standardized calculation method for consistent results
    // Fixed conversion factor for converting meters to degrees (approximately at the equator)
    const METERS_TO_DEGREES = 0.000009;
    const radiusInDegrees = rangeInMeters * METERS_TO_DEGREES;

    const [lng, lat] = Array.isArray(coordinates) ? coordinates : [coordinates.lng, coordinates.lat];

    // Add debug logs for coordinate calculation
    console.log(`Calculating cone center for camera ${cameraId}:`);
    console.log(`Initial coordinates: [${lng}, ${lat}]`);
    console.log(`Range in meters: ${rangeInMeters}, Direction: ${direction}°, Angle: ${angle}°`);
    console.log(`Radius in degrees (consistent): ${radiusInDegrees}`);

    // Make sure all cone calculations use the same conversion factor
    const directionRad = (direction * Math.PI) / 180;
    const halfAngleRad = (angle / 2 * Math.PI) / 180;

    // Generate cone points using consistent calculation
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
    try {
      console.log(`Adding source: ${sourceId}`);
      map.value.addSource(sourceId, {
        type: 'geojson',
        data: conePolygon
      });
      console.log(`Source ${sourceId} added successfully`);
    } catch (sourceError) {
      console.error(`Error adding source ${sourceId}:`, sourceError);
      return null;
    }

    // Add the fill layer
    try {
      console.log(`Adding main layer: ${coneId}`);
      map.value.addLayer({
        id: coneId,
        type: 'fill',
        source: sourceId,
        layout: {},
        paint: {
          'fill-color': isDarkMode.value ? '#38a3a5' : '#4f6642',
          'fill-opacity': 0.35,
          'fill-outline-color': isDarkMode.value ? '#2C7A7B' : '#3b4e31'
        }
      });
      console.log(`Layer ${coneId} added successfully`);
    } catch (layerError) {
      console.error(`Error adding layer ${coneId}:`, layerError);
      if (map.value.getSource(sourceId)) {
        try {
          map.value.removeSource(sourceId);
        } catch (cleanupError) {
          console.error(`Error cleaning up source ${sourceId}:`, cleanupError);
        }
      }
      return false;
    }

    // Add a line layer to make the cone edge more visible
    try {
      console.log(`Adding line layer: ${coneId}-line`);
      map.value.addLayer({
        id: `${coneId}-line`,
        type: 'line',
        source: sourceId,
        layout: {
          'line-cap': 'round',
          'line-join': 'round'
        },
        paint: {
          'line-color': isDarkMode.value ? '#2C7A7B' : '#3b4e31',
          'line-width': 2,
          'line-opacity': 0.8
        }
      });
      console.log(`Line layer ${coneId}-line added successfully`);
    } catch (lineLayerError) {
      console.error(`Error adding line layer ${coneId}-line:`, lineLayerError);
    }

    // Add a directional arrow at the tip of the cone
    const arrowPoints = [
      [lng, lat],
      [
        lng + radiusInDegrees * Math.sin(directionRad),
        lat + radiusInDegrees * Math.cos(directionRad)
      ]
    ];

    // Add the arrow source
    try {
      console.log(`Adding arrow source: ${arrowSourceId}`);
      map.value.addSource(arrowSourceId, {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'LineString',
            coordinates: arrowPoints
          }
        }
      });
      console.log(`Arrow source ${arrowSourceId} added successfully`);
    } catch (arrowSourceError) {
      console.error(`Error adding arrow source ${arrowSourceId}:`, arrowSourceError);
    }

    // Add the arrow layer
    try {
      console.log(`Adding arrow layer: ${arrowLayerId}`);
      map.value.addLayer({
        id: arrowLayerId,
        type: 'line',
        source: arrowSourceId,
        layout: {
          'line-cap': 'round',
          'line-join': 'round'
        },
        paint: {
          'line-color': isDarkMode.value ? '#38a3a5' : '#4f6642',
          'line-width': 2,
          'line-dasharray': [2, 1]
        }
      });
      console.log(`Arrow layer ${arrowLayerId} added successfully`);
    } catch (arrowLayerError) {
      console.error(`Error adding arrow layer ${arrowLayerId}:`, arrowLayerError);
    }

    // Verify which layers were actually added
    setTimeout(() => {
      const existingLayers = map.value.getStyle().layers || [];
      const layerIds = existingLayers.map(layer => layer.id);
      console.log(`Verification: Map has ${existingLayers.length} layers`);
      console.log(`Verification: Layer ${coneId} exists:`, layerIds.includes(coneId) ? 'Yes' : 'No');
      console.log(`Verification: Layer ${coneId}-line exists:`, layerIds.includes(`${coneId}-line`) ? 'Yes' : 'No');
      console.log(`Verification: Layer ${arrowLayerId} exists:`, layerIds.includes(arrowLayerId) ? 'Yes' : 'No');
    }, 50);

    // Store the cone definition
    coneMap.value[cameraId] = {
      center: [lng, lat],
      radius: rangeInMeters,
      direction,
      angle,
      polygon: conePolygon.geometry.coordinates[0],
      sourceId,
      layerId: coneId,
      arrowSourceId,
      arrowLayerId
    };

    // Verify that layers and sources were added successfully
    setTimeout(() => {
      try {
        const existingLayers = map.value.getStyle().layers || [];
        const layerIds = existingLayers.map(layer => layer.id);
        console.log(`Final verification for camera ${cameraId}:`);
        console.log(`- Layer ${coneId} exists:`, layerIds.includes(coneId) ? 'Yes' : 'No');
        console.log(`- Layer ${coneId}-line exists:`, layerIds.includes(`${coneId}-line`) ? 'Yes' : 'No');
        console.log(`- Layer ${arrowLayerId} exists:`, layerIds.includes(arrowLayerId) ? 'Yes' : 'No');
        console.log(`- Source ${sourceId} exists:`, map.value.getSource(sourceId) ? 'Yes' : 'No');
        console.log(`- Source ${arrowSourceId} exists:`, map.value.getSource(arrowSourceId) ? 'Yes' : 'No');
      } catch (verifyError) {
        console.error('Error during verification:', verifyError);
      }
    }, 100);

    return {
      coneId,
      sourceId,
      cameraId,
      coordinates,
      center: [lng, lat],
      radius: rangeInMeters,
      direction,
      angle
    };
  } catch (error) {
    console.error('Error adding conical perception range:', error);
    return null;
  }
}

// Add a function to focus on a specific user area
function focusOnUserArea(featureId) {
  if (!map.value || !draw.value) {
    console.error('Map or draw control not initialized, cannot focus on user area');
    return false;
  }

  try {
    console.log(`Focusing on user area with feature ID: ${featureId}`);

    // Find the area in our userAreas collection
    const area = userAreas.value.find(area => area.feature_id === featureId);

    if (!area || !area.geometry) {
      console.error(`User area with feature ID ${featureId} not found or has no geometry`);
      return false;
    }

    // Get the coordinates from the area's geometry
    let coordinates;
    let bounds;

    // Parse the geometry if it's a string
    const geometry = typeof area.geometry === 'string' ? JSON.parse(area.geometry) : area.geometry;

    // Handle different geometry types
    if (geometry.type === 'Polygon') {
      // For polygons, calculate center and bounds
      const coords = geometry.coordinates[0]; // First ring of coordinates

      if (!coords || !coords.length) {
        console.error('Invalid polygon coordinates');
        return false;
      }

      // Calculate bounds
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

      for (const coord of coords) {
        minX = Math.min(minX, coord[0]);
        minY = Math.min(minY, coord[1]);
        maxX = Math.max(maxX, coord[0]);
        maxY = Math.max(maxY, coord[1]);
      }

      bounds = [[minX, minY], [maxX, maxY]];
      coordinates = [(minX + maxX) / 2, (minY + maxY) / 2]; // Center point
    } else if (geometry.type === 'Point') {
      // For points, use the point coordinates directly
      coordinates = geometry.coordinates;
    } else {
      console.error(`Unsupported geometry type: ${geometry.type}`);
      return false;
    }

    // If we have bounds, fit the map to the bounds
    if (bounds) {
      map.value.fitBounds(bounds, {
        padding: 50, // Add some padding around the bounds
        duration: 1000 // Animation time
      });
    } else if (coordinates) {
      // Otherwise, fly to the coordinates
      map.value.flyTo({
        center: coordinates,
        zoom: 15, // Appropriate zoom level
        essential: true,
        duration: 1000
      });
    } else {
      console.error('Could not determine coordinates to focus on');
      return false;
    }

    // Highlight this specific area if possible
    try {
      // Get all features from the draw control
      const features = draw.value.getAll().features;

      // Find the matching feature
      const feature = features.find(f => f.id === featureId);

      if (feature) {
        // Highlight this feature (implementation depends on your map library)
        console.log('Found feature to highlight:', feature);

        // If using Mapbox Draw, you might select the feature
        draw.value.changeMode('simple_select', { featureIds: [featureId] });
      }
    } catch (highlightError) {
      console.warn('Error highlighting feature:', highlightError);
      // Continue even if highlighting fails
    }

    return true;
  } catch (error) {
    console.error('Error focusing on user area:', error);
    return false;
  }
}

// Function to generate a unique color for each area based on its ID
function generateAreaColor(area) {
  if (!area || !area.feature_id) return {};

  // Create a hash from the feature_id
  let hash = 0;
  for (let i = 0; i < area.feature_id.length; i++) {
    hash = area.feature_id.charCodeAt(i) + ((hash << 5) - hash);
  }

  // Convert the hash to a hue (0-360)
  const hue = hash % 360;

  // Use a high saturation and lightness for vibrant colors
  const saturation = 70 + (hash % 20); // 70-90%
  const lightness = 45 + (hash % 10);  // 45-55%

  // Return as a CSS style object
  return {
    backgroundColor: `hsl(${hue}, ${saturation}%, ${lightness}%)`,
    borderColor: `hsl(${hue}, ${saturation - 10}%, ${lightness - 15}%)`
  };
}

// Remove a cone from the map
function removeCone(cameraId) {
  if (!map.value) return;

  try {
    console.log(`Removing cone for camera ID: ${cameraId}`);

    // Get the cone IDs using the new naming pattern
    const coneId = `cone-layer-${cameraId}`;
    const sourceId = `cone-source-${cameraId}`;
    const arrowLayerId = `cone-arrow-layer-${cameraId}`;
    const arrowSourceId = `cone-arrow-source-${cameraId}`;

    // Log existing layers before removal
    console.log(`Checking if layer ${coneId} exists:`, map.value.getLayer(coneId) ? 'Yes' : 'No');
    console.log(`Checking if layer ${coneId}-line exists:`, map.value.getLayer(`${coneId}-line`) ? 'Yes' : 'No');
    console.log(`Checking if layer ${arrowLayerId} exists:`, map.value.getLayer(arrowLayerId) ? 'Yes' : 'No');

    // Always remove layers first, in correct order
    if (map.value.getLayer(arrowLayerId)) {
      console.log(`Removing arrow layer: ${arrowLayerId}`);
      map.value.removeLayer(arrowLayerId);
    }

    // Also check for the old naming pattern for backward compatibility
    if (map.value.getLayer(`cone-${cameraId}-arrow`)) {
      console.log(`Removing old arrow layer: cone-${cameraId}-arrow`);
      map.value.removeLayer(`cone-${cameraId}-arrow`);
    }

    if (map.value.getLayer(`${coneId}-line`)) {
      console.log(`Removing line layer: ${coneId}-line`);
      map.value.removeLayer(`${coneId}-line`);
    }

    if (map.value.getLayer(coneId)) {
      console.log(`Removing main layer: ${coneId}`);
      map.value.removeLayer(coneId);
    }

    // Also check for the old naming pattern for backward compatibility
    if (map.value.getLayer(`cone-${cameraId}`)) {
      console.log(`Removing old main layer: cone-${cameraId}`);
      map.value.removeLayer(`cone-${cameraId}`);
    }

    // Now it's safe to remove sources
    if (map.value.getSource(arrowSourceId)) {
      console.log(`Removing arrow source: ${arrowSourceId}`);
      map.value.removeSource(arrowSourceId);
    }

    // Also check for the old naming pattern for backward compatibility
    if (map.value.getSource(`${sourceId}-arrow`)) {
      console.log(`Removing old arrow source: ${sourceId}-arrow`);
      map.value.removeSource(`${sourceId}-arrow`);
    }

    if (map.value.getSource(sourceId)) {
      console.log(`Removing main source: ${sourceId}`);
      map.value.removeSource(sourceId);
    }

    // Remove from cone map
    if (coneMap.value[cameraId]) {
      delete coneMap.value[cameraId];
      console.log(`Removed cone data from internal store for camera ID: ${cameraId}`);
    }

    // Verify removal
    setTimeout(() => {
      const existingLayers = map.value.getStyle().layers || [];
      const layerIds = existingLayers.map(layer => layer.id);
      console.log(`Verification after removal - Layer ${coneId} exists:`, layerIds.includes(coneId) ? 'Yes' : 'No');
      console.log(`Verification after removal - Source ${sourceId} exists:`, map.value.getSource(sourceId) ? 'Yes' : 'No');
    }, 50);

    return true;
  } catch (error) {
    console.error(`Error removing cone for camera ${cameraId}:`, error);
    return false;
  }
}

// Get random point within a cone
function getRandomPointInCone(cone) {
  if (!cone || !cone.center) {
    console.error('Invalid cone data, cannot generate random point');
    return [0, 0];
  }

  try {
    // Extract cone properties
    const center = cone.center;
    const radius = parseFloat(cone.radius || 30);
    const direction = parseFloat(cone.direction || 0);
    const angle = parseFloat(cone.angle || 60);

    // Convert to degrees for calculations
    const radiusInDegrees = radius * 0.000009; // 1m is approx 0.000009 degrees
    const directionRad = (direction * Math.PI) / 180;
    const halfAngleRad = (angle / 2 * Math.PI) / 180;

    // Generate a normal random angle biased toward the center of the viewing cone
    const normalRandom = () => {
      // Box-Muller transform for normal distribution
      const u1 = Math.random();
      const u2 = Math.random();
      const z = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
      // Scale to portion of viewing angle and center on viewing direction
      return directionRad + (z * (halfAngleRad / 2.5));
    };

    // Get angle biased toward center of cone
    let randomAngle = normalRandom();

    // Ensure angle stays within cone boundaries
    const startAngle = directionRad - halfAngleRad;
    const endAngle = directionRad + halfAngleRad;
    if (randomAngle < startAngle) randomAngle = startAngle + (Math.random() * halfAngleRad * 0.2);
    if (randomAngle > endAngle) randomAngle = endAngle - (Math.random() * halfAngleRad * 0.2);

    // Calculate distance from center (denser in middle range)
    const minDistance = 0.2; // 20% of max range
    const maxDistance = 0.8; // 80% of max range
    const distanceFactor = minDistance + Math.pow(Math.random(), 0.7) * (maxDistance - minDistance);

    // Calculate offsets using trig
    const offsetX = radiusInDegrees * distanceFactor * Math.sin(randomAngle);
    const offsetY = radiusInDegrees * distanceFactor * Math.cos(randomAngle);

    // Add a little jitter for natural appearance
    const jitter = radiusInDegrees * 0.03;
    const jitterX = jitter * (Math.random() * 2 - 1);
    const jitterY = jitter * (Math.random() * 2 - 1);

    // Apply offsets to camera position
    const result = [
      center[0] + offsetX + jitterX,
      center[1] + offsetY + jitterY
    ];

    console.log(`Generated random point in cone: [${result[0]}, ${result[1]}] from center [${center[0]}, ${center[1]}]`);
    return result;
  } catch (error) {
    console.error('Error generating random point in cone:', error);
    return cone.center || [0, 0]; // Fallback to center or origin
  }
}

// Navigate to a specific location on the map
function navigateToLocation(coordinates, zoom = 16) {
  if (!map.value) {
    console.error('Map not initialized, cannot navigate to location');
    return false;
  }

  try {
    console.log(`Navigating to coordinates: [${coordinates[0]}, ${coordinates[1]}] with zoom: ${zoom}`);

    // Fly to the location with animation
    map.value.flyTo({
      center: coordinates,
      zoom: zoom,
      essential: true, // This animation is considered essential for the intended user experience
      duration: 1500 // Animation time in milliseconds
    });

    return true;
  } catch (error) {
    console.error('Error navigating to location:', error);
    return false;
  }
}

// Toggle map selector panel
function toggleMapSelector() {
  showMapSelector.value = !showMapSelector.value;
  if (showMapSelector.value) {
    // Reset form values when opening
    accessCode.value = '';
    accessCodeError.value = '';
    isCreatingMap.value = false;
    newMapName.value = '';
    newMapDescription.value = '';
  }
}

// Access map by code
async function accessMapByCode() {
  if (accessCode.value.length !== 6) {
    accessCodeError.value = 'Please enter a valid 6-character code';
    return;
  }

  accessCodeError.value = '';
  isProcessingMapOperation.value = true;

  try {
    console.log('Accessing map by code:', accessCode.value);

    // Make API request to fetch the map data
    const response = await axios.post('/user-maps/access-by-code', {
      access_code: accessCode.value
    });

    if (response.data.success) {
      console.log('Map accessed successfully:', response.data.map);

      // Hide the selector panel
      showMapSelector.value = false;

      // Emit event to parent component with map data
      emit('map-accessed', response.data.map);

      // If map has default view, navigate to it
      if (response.data.map.default_view) {
        const defaultView = response.data.map.default_view;
        if (defaultView.center && defaultView.zoom) {
          navigateToLocation(defaultView.center, defaultView.zoom);
        }
      }
    } else {
      console.error('Failed to access map:', response.data.message);
      accessCodeError.value = response.data.message || 'Invalid access code. Please try again.';
    }
  } catch (error) {
    console.error('Error accessing map:', error);
    accessCodeError.value = error.response?.data?.message || 'An error occurred. Please try again.';
  } finally {
    isProcessingMapOperation.value = false;
  }
}

// Create a new map
async function createNewMap() {
  if (!newMapName.value) {
    accessCodeError.value = 'Please enter a name for your map';
    return;
  }

  accessCodeError.value = '';
  isProcessingMapOperation.value = true;

  try {
    // Get current map center and zoom for default view
    const center = map.value ? map.value.getCenter() : [120.9842, 14.5995]; // Manila coordinates as default
    const zoom = map.value ? map.value.getZoom() : 12; // Default zoom level

    // Format center as array
    const centerArray = center && typeof center === 'object' && 'lng' in center && 'lat' in center
      ? [center.lng, center.lat]
      : (Array.isArray(center) ? center : [120.9842, 14.5995]); // Fallback to Manila coordinates

    console.log('Creating new map:', {
      name: newMapName.value,
      description: newMapDescription.value,
      default_view: { center: centerArray, zoom }
    });

    // Make API request to create a new map
    const response = await axios.post('/user-maps', {
      name: newMapName.value,
      description: newMapDescription.value,
      default_view: { center: centerArray, zoom }
    });

    if (response.data.success) {
      console.log('New map created successfully:', response.data.map);

      // Hide the selector panel
      showMapSelector.value = false;

      // Emit event to parent component with new map data
      emit('map-created', response.data.map);

      // Reset form
      newMapName.value = '';
      newMapDescription.value = '';
    } else {
      console.error('Failed to create new map:', response.data.message);
      accessCodeError.value = response.data.message || 'Failed to create map. Please try again.';
    }
  } catch (error) {
    console.error('Error creating new map:', error);
    accessCodeError.value = error.response?.data?.message || 'An error occurred. Please try again.';
  } finally {
    isProcessingMapOperation.value = false;
  }
}

// Function to add a conical perception range to the map - camera-independent version
function addStandaloneCone(centerCoordinates, radius, direction, angle, id) {
  try {
    // Generate a unique ID if none provided
    const uniqueId = id || `standalone-cone-${Date.now()}-${Math.floor(Math.random() * 1000)}`;

    console.log(`Creating standalone cone at [${centerCoordinates[0]}, ${centerCoordinates[1]}] with radius ${radius}m, direction ${direction}°, angle ${angle}°, ID: ${uniqueId}`);

    if (!map.value) {
      console.error('Map not initialized, cannot add standalone cone');
      return false;
    }

    const coneId = `cone-layer-${uniqueId}`;
    const sourceId = `cone-source-${uniqueId}`;
    const arrowLayerId = `cone-arrow-layer-${uniqueId}`;
    const arrowSourceId = `cone-arrow-source-${uniqueId}`;

    // Wait for map style to load if needed
    if (!map.value.isStyleLoaded()) {
      console.log('Map style not yet loaded, waiting...');
      map.value.once('styledata', () => {
        console.log('Map style loaded, re-adding standalone cone.');
        addStandaloneCone(centerCoordinates, radius, direction, angle, uniqueId);
      });
      return false;
    }

    // Remove existing cone with this ID if it exists without affecting other cones
    if (coneMap.value[uniqueId]) {
      try {
        console.log(`Removing existing standalone cone with ID ${uniqueId}`);

        // Always remove layers first, in correct order
        if (map.value.getLayer(arrowLayerId)) {
          console.log(`Removing arrow layer: ${arrowLayerId}`);
          map.value.removeLayer(arrowLayerId);
        }

        if (map.value.getLayer(`${coneId}-line`)) {
          console.log(`Removing line layer: ${coneId}-line`);
          map.value.removeLayer(`${coneId}-line`);
        }

        if (map.value.getLayer(coneId)) {
          console.log(`Removing main layer: ${coneId}`);
          map.value.removeLayer(coneId);
        }

        // Now it's safe to remove sources
        if (map.value.getSource(arrowSourceId)) {
          console.log(`Removing arrow source: ${arrowSourceId}`);
          map.value.removeSource(arrowSourceId);
        }

        if (map.value.getSource(sourceId)) {
          console.log(`Removing main source: ${sourceId}`);
          map.value.removeSource(sourceId);
        }
      } catch (removeError) {
        console.warn(`Error removing existing cone ${uniqueId}:`, removeError);
        // Continue with creating the new cone even if removal fails
      }
    }

    // Convert radius from meters to approximate degrees
    // 1 degree of latitude is approximately 111km at the equator
    const radiusInDegrees = radius * 0.000009;

    // Destructure the center coordinates
    const [lng, lat] = centerCoordinates;

    // Convert direction and angle to radians
    const directionRad = (direction * Math.PI) / 180;
    const halfAngleRad = (angle / 2 * Math.PI) / 180;

    // Generate cone points
    const conePoints = [[lng, lat]]; // Start with center point
    const numPoints = 30; // Number of points along the arc
    const startAngle = directionRad - halfAngleRad;
    const endAngle = directionRad + halfAngleRad;

    // Generate the arc points
    for (let i = 0; i <= numPoints; i++) {
      const currentAngle = startAngle + (i / numPoints) * (endAngle - startAngle);
      const x = lng + radiusInDegrees * Math.sin(currentAngle);
      const y = lat + radiusInDegrees * Math.cos(currentAngle);
      conePoints.push([x, y]);
    }

    // Close the polygon by repeating the first point
    conePoints.push([lng, lat]);

    // Create GeoJSON feature for the cone
    const conePolygon = {
      type: 'Feature',
      properties: {
        id: uniqueId,
        type: 'standalone-cone',
        range_meters: radius,
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

    // Add the fill layer
    map.value.addLayer({
      id: coneId,
      type: 'fill',
      source: sourceId,
      layout: {},
      paint: {
        'fill-color': isDarkMode.value ? '#38a3a5' : '#4f6642',
        'fill-opacity': 0.35,
        'fill-outline-color': isDarkMode.value ? '#2C7A7B' : '#3b4e31'
      }
    });

    // Add a line layer to make the cone edge more visible
    map.value.addLayer({
      id: `${coneId}-line`,
      type: 'line',
      source: sourceId,
      layout: {
        'line-cap': 'round',
        'line-join': 'round'
      },
      paint: {
        'line-color': isDarkMode.value ? '#2C7A7B' : '#3b4e31',
        'line-width': 2,
        'line-opacity': 0.8
      }
    });

    // Add a directional arrow at the tip of the cone
    const arrowPoints = [
      [lng, lat],
      [
        lng + radiusInDegrees * Math.sin(directionRad),
        lat + radiusInDegrees * Math.cos(directionRad)
      ]
    ];

    map.value.addSource(`${sourceId}-arrow`, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: arrowPoints
        }
      }
    });

    map.value.addLayer({
      id: `${coneId}-arrow`,
      type: 'line',
      source: `${sourceId}-arrow`,
      layout: {
        'line-cap': 'round',
        'line-join': 'round'
      },
      paint: {
        'line-color': isDarkMode.value ? '#38a3a5' : '#4f6642',
        'line-width': 2,
        'line-dasharray': [2, 1]
      }
    });

    // Store the cone definition
    coneMap.value[uniqueId] = {
      center: [lng, lat],
      radius: radius,
      direction,
      angle,
      polygon: conePolygon.geometry.coordinates[0],
      sourceId,
      layerId: coneId,
      arrowSourceId,
      arrowLayerId,
      isStandalone: true
    };

    console.log(`Successfully created standalone cone with ID ${uniqueId}`, coneMap.value[uniqueId]);
    return uniqueId; // Return the ID so it can be tracked and removed later if needed
  } catch (error) {
    console.error('Error creating standalone cone:', error);
    return false;
  }
}

// Add a function to remove all standalone cones
function removeAllStandaloneCones() {
  try {
    if (!map.value) return false;

    console.log('Removing all standalone cones');

    // Find all standalone cones in the coneMap
    const standaloneConeIds = Object.entries(coneMap.value)
      .filter(([_, cone]) => cone.isStandalone)
      .map(([id, _]) => id);

    console.log(`Found ${standaloneConeIds.length} standalone cones to remove`);

    // Remove each standalone cone
    standaloneConeIds.forEach(id => {
      try {
        removeCone(id);
      } catch (error) {
        console.warn(`Error removing standalone cone ${id}:`, error);
      }
    });

    return true;
  } catch (error) {
    console.error('Error removing all standalone cones:', error);
    return false;
  }
}

// Enable manual pin placement for animals
function enableAnimalPinPlacement() {
  if (isAddingAnimalPin.value) return; // Already in pin placement mode

  console.log('Enabling animal pin placement mode');
  animalPinType.value = animalPinForm.value.animal_type;
  isAddingAnimalPin.value = true;

  // Focus the map for better UX
  if (mapContainer.value) {
    mapContainer.value.focus();
  }

  // Setup a click handler for the map
  if (map.value) {
    // Use a one-time click handler
    const clickHandler = (e) => {
      console.log('Map clicked at:', e.lngLat);
      // Show dialog with form to enter details
      animalPinForm.value.coordinates = [e.lngLat.lng, e.lngLat.lat];
      animalPinDialogOpen.value = true;
      // Remove the handler after click
      map.value.off('click', clickHandler);
      isAddingAnimalPin.value = false;
    };

    map.value.once('click', clickHandler);
  }
}

// Cancel animal pin placement
function cancelAnimalPinPlacement() {
  isAddingAnimalPin.value = false;
  // Remove any click handlers
  if (map.value) {
    map.value.off('click');
  }
}

// Add the animal pin with form data
function submitAnimalPin() {
  const formData = {...animalPinForm.value};

  // Create a unique ID
  formData.id = `manual-${Date.now()}`;

  // Unpack coordinates
  if (formData.coordinates) {
    formData.lng = formData.coordinates[0];
    formData.lat = formData.coordinates[1];
  }

  console.log('Adding manual animal pin with data:', formData);

  // Add the pin to the map
  addAnimalPin(formData)
    .then(result => {
      console.log('Pin added successfully:', result);
      // Reset form
      animalPinForm.value = {
        animal_type: animalPinType.value,
        description: `Stray ${animalPinType.value} sighting`,
        status: 'active',
        image_url: ''
      };
      // Close dialog
      animalPinDialogOpen.value = false;
    })
    .catch(error => {
      console.error('Error adding pin:', error);
      alert('Failed to add pin. Please try again.');
    });
}

// Add this function to handle zoom events
function handleMapZoom() {
  if (!map.value) return;

  try {
    // Get current zoom level
    currentZoom.value = map.value.getZoom();
    console.log('Current map zoom:', currentZoom.value);

    // Hide/show pin elements based on zoom level
    const pinElements = document.querySelectorAll('.mapboxgl-marker');
    pinElements.forEach(pin => {
      if (currentZoom.value < minPinZoomLevel.value) {
        pin.style.display = 'none';
      } else {
        pin.style.display = 'block';
      }
    });

    // Update area labels visibility and size based on zoom
    updateAreaLabels();
  } catch (error) {
    console.error('Error handling map zoom:', error);
  }
}

// Function to update area labels based on zoom level
function updateAreaLabels() {
  if (!map.value || !draw.value) return;

  try {
    // Remove existing area labels
    const existingLabels = document.querySelectorAll('.area-label');
    existingLabels.forEach(label => label.remove());

    // Get all areas from the draw control
    const features = draw.value.getAll().features;

    // Create labels for each area
    features.forEach(feature => {
      if (feature.geometry.type === 'Polygon') {
        // Get area properties
        const properties = feature.properties || {};
        const areaName = properties.name || 'Unnamed Area';

        // Calculate centroid of the polygon
        const coordinates = feature.geometry.coordinates[0];
        if (!coordinates || coordinates.length === 0) return;

        let sumX = 0, sumY = 0;
        coordinates.forEach(coord => {
          sumX += coord[0];
          sumY += coord[1];
        });

        const centroid = [sumX / coordinates.length, sumY / coordinates.length];

        // Create a point for this label
        const point = map.value.project(centroid);

        // Create label element
        const label = document.createElement('div');
        label.className = 'area-label';
        if (isDarkMode.value) {
          label.classList.add('dark-mode');
        }
        label.textContent = areaName;

        // Style based on zoom level
        const fontSize = Math.max(14, Math.min(24, currentZoom.value * 1.2));
        label.style.fontSize = `${fontSize}px`;

        // Position the label
        label.style.position = 'absolute';
        label.style.left = `${point.x}px`;
        label.style.top = `${point.y}px`;

        // Add to map container
        map.value.getContainer().appendChild(label);

        // Update position when map moves
        const updatePosition = () => {
          const point = map.value.project(centroid);
          label.style.left = `${point.x}px`;
          label.style.top = `${point.y}px`;
        };

        map.value.on('move', updatePosition);
      }
    });
  } catch (error) {
    console.error('Error updating area labels:', error);
  }
}

// Add this function to start area name editing
function editAreaName(area) {
  console.log('Editing area name:', area);
  areaBeingEdited.value = area;

  // Get the current name from properties or directly from area
  let currentName = '';
  try {
    const properties = typeof area.properties === 'string' ?
      JSON.parse(area.properties || '{}') :
      area.properties || {};

    currentName = properties.name || area.name || '';
  } catch (error) {
    console.error('Error parsing area properties:', error);
    currentName = area.name || '';
  }

  areaNameEdit.value = currentName;
  areaEditMode.value = true;
}

// Add this function to save area name
function saveAreaName() {
  if (!areaBeingEdited.value) return;

  try {
    console.log('Saving area name:', areaNameEdit.value);

    // Create a copy of the area properties
    let properties = {};
    try {
      properties = typeof areaBeingEdited.value.properties === 'string' ?
        JSON.parse(areaBeingEdited.value.properties || '{}') :
        {...(areaBeingEdited.value.properties || {})};
    } catch (error) {
      console.error('Error parsing area properties:', error);
      properties = {};
    }

    // Update the name property
    properties.name = areaNameEdit.value;

    // Get the feature_id
    const featureId = areaBeingEdited.value.feature_id;

    if (featureId && draw.value) {
      // Get the feature from draw
      const feature = draw.value.get(featureId);

      if (feature) {
        // Update the properties
        feature.properties = feature.properties || {};
        feature.properties.name = areaNameEdit.value;

        // Update in the draw plugin
        draw.value.add(feature);

        // Save to the database
        saveUserArea(feature, true);
      } else {
        console.warn(`Feature with ID ${featureId} not found in draw`);

        // Update the area directly
        if (typeof areaBeingEdited.value.properties === 'string') {
          areaBeingEdited.value.properties = JSON.stringify(properties);
        } else {
          areaBeingEdited.value.properties = properties;
        }

        // Find the area in the userAreas array and update it
        const areaIndex = userAreas.value.findIndex(a => a.feature_id === featureId);
        if (areaIndex >= 0) {
          if (typeof userAreas.value[areaIndex].properties === 'string') {
            userAreas.value[areaIndex].properties = JSON.stringify(properties);
          } else {
            userAreas.value[areaIndex].properties = properties;
          }

          // Also update the name field directly
          userAreas.value[areaIndex].name = areaNameEdit.value;

          // Save to the database
          axios.put(`/api/user-areas/${featureId}`, {
            name: areaNameEdit.value,
            properties: JSON.stringify(properties),
            feature_id: featureId,
            geometry: areaBeingEdited.value.geometry
          })
          .then(response => {
            console.log('Area name updated via API:', response.data);
          })
          .catch(error => {
            console.error('Error updating area name via API:', error);
          });
        }
      }

      // Update area labels
      updateAreaLabels();
    }

    // Exit edit mode
    areaEditMode.value = false;
    areaBeingEdited.value = null;

    console.log('Area name updated successfully');
  } catch (error) {
    console.error('Error saving area name:', error);
    alert('Failed to update area name. Please try again.');
  }
}

// Calculate new cone data using consistent method
// We'll standardize the calculation for cone center based on camera position and view parameters
const calculateConeCenter = (cameraLng, cameraLat, perceptionRange, viewingDirection) => {
  // Convert direction to radians
  const directionRad = (viewingDirection * Math.PI) / 180;

  // Fixed conversion factor from meters to degrees (approximately at the equator)
  // We'll use a fixed factor to ensure consistency
  const METERS_TO_DEGREES = 0.000009;

  // Calculate radius in degrees - this will be the same for all cameras with same perception range
  const radiusInDegrees = perceptionRange * METERS_TO_DEGREES;

  // Calculate cone center position using consistent trigonometry
  const centerLng = cameraLng + (radiusInDegrees * Math.sin(directionRad));
  const centerLat = cameraLat + (radiusInDegrees * Math.cos(directionRad));

  return [centerLng, centerLat];
};
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

      <!-- Map Legend -->
      <div class="map-legend" :class="{ 'dark-mode': isDarkMode }">
        <h4 class="legend-title">Map Legend</h4>
        <!-- <div class="legend-item">
          <div class="legend-color barangay-color"></div>
          <div class="legend-label">{{mapName}}</div>
        </div> -->
        <div class="legend-item">
          <div class="legend-icon camera-icon"></div>
          <div class="legend-label">CCTV Camera</div>
        </div>
        <div class="legend-item">
          <div class="legend-icon dog-icon"></div>
          <div class="legend-label">Dog Sighting</div>
        </div>
        <div class="legend-item">
          <div class="legend-icon cat-icon"></div>
          <div class="legend-label">Cat Sighting</div>
        </div>
        <div class="legend-item">
          <div class="legend-color user-area-color"></div>
          <div class="legend-label">Target Area</div>
        </div>
      </div>

      <!-- Drawing Controls -->
      <div class="drawing-controls" :class="{ 'dark-mode': isDarkMode }">
        <button @click="enableDrawingMode('polygon')" class="draw-btn">
          <i class="fas fa-draw-polygon"></i> Draw Area
        </button>
        <div class="zoom-controls">
          <span class="zoom-label">Zoom Levels:</span>
          <div class="zoom-buttons">
            <button @click="enableDrawingMode('polygon', 14)" class="zoom-btn" title="City Level">
              <i class="fas fa-city"></i>
            </button>
            <button @click="enableDrawingMode('polygon', 16)" class="zoom-btn" title="District Level">
              <i class="fas fa-building"></i>
            </button>
            <button @click="enableDrawingMode('polygon', 18)" class="zoom-btn" title="Street Level">
              <i class="fas fa-road"></i>
            </button>
          </div>
        </div>
        <button @click="disableDrawingMode()" class="draw-btn">
          <i class="fas fa-hand-pointer"></i> Select Mode
        </button>
        <span class="zoom-label">Access Code: {{ mapAccessCode }}</span>
      </div>

      <!-- User Areas Panel -->
      <div v-if="userAreas.length > 0" class="user-areas-panel" :class="{ 'dark-mode': isDarkMode, 'expanded': isUserAreasPanelExpanded }">
        <div class="panel-header" @click="toggleUserAreasPanel">
          <h4>User Areas <span>({{ userAreas.length }})</span></h4>
          <i :class="isUserAreasPanelExpanded ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
        </div>
        <div v-if="isUserAreasPanelExpanded" class="panel-content">
          <div v-if="isFocusedOnArea" class="focus-controls">
            <button @click="showAllAreas" class="focus-control-btn">
              <i class="fas fa-expand-arrows-alt"></i> Show All Areas
            </button>
          </div>
          <div class="area-list">
            <div
              v-for="area in userAreas"
              :key="area.feature_id"
              class="area-item"
              :class="{ 'focused': focusedAreaId === area.feature_id }"
              @click="focusOnArea(area.feature_id)"
            >
              <div class="area-color" :style="generateAreaColor(area)"></div>
              <div class="area-info">
                <div class="area-name">{{ area.name || 'Unnamed Area' }}</div>
                <div class="area-description">{{ area.description || 'No description' }}</div>
              </div>
              <div class="area-actions">
                <button @click.stop="editAreaName(area)" class="edit-area-btn" title="Edit area name">
                  <i class="fas fa-edit"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- User Map Access Panel -->
      <div v-if="showMapSelector" class="user-map-panel" :class="{ 'dark-mode': isDarkMode }">
        <div class="panel-header">
          <h4>{{ isCreatingMap ? 'Create New Map' : 'Access Shared Map' }}</h4>
          <button @click="showMapSelector = false" class="close-panel-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="panel-content">
          <div v-if="!isCreatingMap" class="access-code-form">
            <div class="form-description">
              <p>Enter a map access code to view a shared map.</p>
            </div>
            <div class="input-group">
              <input
                type="text"
                v-model="accessCode"
                placeholder="Enter 6-character code"
                maxlength="6"
                class="access-code-input"
                :class="{ 'error': accessCodeError }"
              />
              <button
                class="access-btn"
                @click="accessMapByCode"
                :disabled="isProcessingMapOperation || accessCode.length !== 6"
              >
                <i v-if="isProcessingMapOperation" class="fas fa-spinner fa-spin"></i>
                <span v-else>Access Map</span>
              </button>
            </div>
            <div v-if="accessCodeError" class="error-message">
              {{ accessCodeError }}
            </div>
            <div class="option-toggle">
              <span>Don't have a code?</span>
              <button @click="isCreatingMap = true" class="toggle-btn">Create Your Own Map</button>
            </div>
          </div>

          <div v-else class="create-map-form">
            <div class="form-description">
              <p>Create a personal map that you can share with others.</p>
            </div>
            <div class="form-group">
              <label for="map-name">Map Name</label>
              <input
                type="text"
                id="map-name"
                v-model="newMapName"
                placeholder="Enter a name for your map"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="map-description">Description (Optional)</label>
              <textarea
                id="map-description"
                v-model="newMapDescription"
                placeholder="Describe your map..."
                class="form-textarea"
              ></textarea>
            </div>
            <div class="form-actions">
              <button
                class="cancel-btn"
                @click="isCreatingMap = false"
                :disabled="isProcessingMapOperation"
              >
                Cancel
              </button>
              <button
                class="create-btn"
                @click="createNewMap"
                :disabled="isProcessingMapOperation || !newMapName"
              >
                <i v-if="isProcessingMapOperation" class="fas fa-spinner fa-spin"></i>
                <span v-else>Create Map</span>
              </button>
            </div>
            <div class="option-toggle">
              <span>Have an access code?</span>
              <button @click="isCreatingMap = false" class="toggle-btn">Enter Access Code</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Map Selector Button -->
      <button v-if="!showMapSelector" @click="toggleMapSelector" class="map-selector-btn">
        <i class="fas fa-map-marked-alt"></i>
        <span>Select Map</span>
      </button>

      <!-- Add Animal Pin Button -->
      <!-- <button @click="enableAnimalPinPlacement" class="add-animal-pin-btn" :class="{ 'active': isAddingAnimalPin }">
        <i class="fas fa-plus"></i>
        <span>Add Animal</span>
      </button> -->

      <!-- Cancel Animal Pin Button (shown when in placement mode) -->
      <button v-if="isAddingAnimalPin" @click="cancelAnimalPinPlacement" class="cancel-animal-pin-btn">
        <i class="fas fa-times"></i>
        <span>Cancel</span>
      </button>

      <!-- Pin in Map Button (Super Admin Only) -->
      <button
        v-if="props.authUser && props.authUser.role === 'super_admin'"
        @click="enablePinPlacementMode"
        class="pin-in-map-btn"
      >
        <i class="fas fa-map-pin"></i>
        <span>Pin in Map</span>
      </button>

      <!-- Animal Pin Dialog -->
      <div v-if="animalPinDialogOpen" class="animal-pin-dialog">
        <div class="dialog-header">
          <h3>Add Animal Sighting</h3>
          <button @click="animalPinDialogOpen = false" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="dialog-body">
          <form @submit.prevent="submitAnimalPin">
            <div class="form-group">
              <label for="animal-type">Animal Type</label>
              <select id="animal-type" v-model="animalPinForm.animal_type">
                <option value="dog">Dog</option>
                <option value="cat">Cat</option>
              </select>
            </div>
            <div class="form-group">
              <label for="description">Description</label>
              <textarea id="description" v-model="animalPinForm.description" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label for="status">Status</label>
              <select id="status" v-model="animalPinForm.status">
                <option value="active">Active</option>
                <option value="resolved">Resolved</option>
                <option value="in_progress">In Progress</option>
              </select>
            </div>
            <div class="form-group">
              <label for="image-url">Image URL (Optional)</label>
              <input type="text" id="image-url" v-model="animalPinForm.image_url" placeholder="https://example.com/image.jpg">
            </div>
            <div class="form-actions">
              <button type="button" @click="animalPinDialogOpen = false" class="cancel-btn">Cancel</button>
              <button type="submit" class="submit-btn">Add Pin</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Pin in Map Button (Super Admin Only) -->
      <button
        v-if="$page.props.auth.user && $page.props.auth.user.role === 'super_admin'"
        @click="enablePinPlacementMode"
        class="pin-in-map-btn"
      >
        <i class="fas fa-map-pin"></i>
        <span>Pin in Map</span>
      </button>
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
  top: -4px;
  left: 50%;
  margin-left: -5px;
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
  box-shadow: 0 0 0 2px white, 0 0 0 4px #4285F4;
}

.camera-marker.has-cone {
  background-color: #1a73e8;
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(26, 115, 232, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(26, 115, 232, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(26, 115, 232, 0);
  }
}

/* Popup styles */
.mapboxgl-popup-content {
  padding: 12px;
  border-radius: 8px;
  color: black; /* Ensure all text in popups is black */
}

.camera-popup h3,
.pin-popup h3 {
  color: black !important; /* Force black color with !important */
  font-size: 16px;
  font-weight: 600;
}

.camera-popup p,
.pin-popup p {
  color: black !important; /* Force black color for paragraph text */
  margin: 5px 0;
}

.camera-popup small,
.pin-popup small {
  color: #333 !important; /* Slightly lighter but still dark and readable */
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

/* Map Legend Styles */
.map-legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 6px;
  padding: 10px;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.2);
  z-index: 1;
  max-width: 250px;
  font-size: 12px;
  transition: background-color 0.3s, color 0.3s;
}

.map-legend.dark-mode {
  background-color: rgba(30, 30, 30, 0.9);
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.5);
}

.legend-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.dark-mode .legend-title {
  color: #f0f0f0;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.legend-color {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  border-radius: 2px;
}

.barangay-color {
  background-color: rgba(255, 0, 0, 0.3);
  border: 1px solid rgba(255, 0, 0, 0.8);
}

.legend-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.camera-icon {
  background-image: url('/images/camera-marker.png');
  /* Fallback if image not available */
  background-color: #3b82f6;
  border-radius: 50%;
}

.dog-icon {
  background-image: url('/images/dog-marker.png');
  /* Fallback if image not available */
  background-color: #f59e0b;
  border-radius: 50%;
}

.cat-icon {
  background-image: url('/images/cat-marker.png');
  /* Fallback if image not available */
  background-color: #10b981;
  border-radius: 50%;
}

.legend-label {
  font-size: 12px;
  color: #333;
}

.dark-mode .legend-label {
  color: #f0f0f0;
}

/* New styles for user areas */
.user-area-color {
  background-color: rgba(63, 81, 181, 0.4);
  border: 1px solid rgba(103, 121, 221, 0.8);
}

/* Drawing controls */
.drawing-controls {
  position: absolute;
  bottom: 20px;
  left: 20px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.draw-btn {
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.draw-btn:hover {
  background-color: #f5f5f5;
}

.draw-btn i {
  font-size: 16px;
}

.drawing-controls.dark-mode {
  background-color: rgba(30, 30, 30, 0.9);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
}

.drawing-controls.dark-mode .draw-btn {
  background-color: #333;
  color: white;
  border: 1px solid #555;
}

.drawing-controls.dark-mode .draw-btn:hover {
  background-color: #444;
}

.zoom-controls {
  display: flex;
  flex-direction: column;
  margin: 8px 0;
  border-top: 1px solid #ddd;
  border-bottom: 1px solid #ddd;
  padding: 8px 0;
}

.drawing-controls.dark-mode .zoom-controls {
  border-top: 1px solid #444;
  border-bottom: 1px solid #444;
}

.zoom-label {
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: bold;
  color: #333;
}

.drawing-controls.dark-mode .zoom-label {
  color: #f0f0f0;
}

.zoom-buttons {
  display: flex;
  gap: 6px;
  justify-content: space-between;
}

.zoom-btn {
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 6px 10px;
  cursor: pointer;
  flex: 1;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zoom-btn:hover {
  background-color: #f0f0f0;
}

.drawing-controls.dark-mode .zoom-btn {
  background-color: #333;
  color: white;
  border: 1px solid #555;
}

.drawing-controls.dark-mode .zoom-btn:hover {
  background-color: #444;
}

/* Mapbox Draw custom styles */
.mapboxgl-ctrl-group.mapboxgl-ctrl {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* User Areas Panel Styles */
.user-areas-panel {
  position: absolute;
  top: 20px;
  right: 80px;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  width: 280px;
  overflow: hidden;
  z-index: 10;
  transition: all 0.3s ease;
}

.user-areas-panel.dark-mode {
  background-color: rgba(33, 33, 33, 0.95);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background-color: rgba(255, 255, 255, 0.1);
  transition: background-color 0.2s;
}

.panel-header:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.dark-mode .panel-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.dark-mode .panel-header:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.panel-header h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.dark-mode .panel-header h4 {
  color: #f0f0f0;
}

.panel-header h4 span {
  opacity: 0.7;
  font-size: 13px;
  margin-left: 5px;
}

.panel-header i {
  font-size: 14px;
  color: #666;
}

.dark-mode .panel-header i {
  color: #aaa;
}

.panel-content {
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.focus-controls {
  margin-bottom: 16px;
}

.focus-control-btn {
  background-color: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
  color: #333;
}

.focus-control-btn:hover {
  background-color: #f1f3f4;
  border-color: #ccc;
}

.dark-mode .focus-control-btn {
  background-color: #2c2c2c;
  border-color: #444;
  color: #f0f0f0;
}

.dark-mode .focus-control-btn:hover {
  background-color: #3c3c3c;
  border-color: #555;
}

.area-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.area-item {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 10px;
  border-radius: 6px;
  transition: all 0.2s;
  background-color: #fafafa;
  border: 1px solid #eaeaea;
}

.area-item:hover {
  background-color: #f0f0f0;
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.dark-mode .area-item {
  background-color: #2a2a2a;
  border-color: #3a3a3a;
}

.dark-mode .area-item:hover {
  background-color: #333;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
}

.area-color {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  margin-right: 10px;
  background-color: rgba(63, 81, 181, 0.7);
  border: 1px solid rgba(63, 81, 181, 0.9);
}

.area-info {
  flex: 1;
  overflow: hidden;
}

.area-name {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #333;
}

.dark-mode .area-name {
  color: #f0f0f0;
}

.area-description {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark-mode .area-description {
  color: #aaa;
}

.area-item.focused {
  background-color: #e8f0fe;
  border-color: #4285f4;
}

.dark-mode .area-item.focused {
  background-color: #1e3a5f;
  border-color: #4285f4;
}

/* Area label styles */
.area-label {
  position: absolute;
  transform: translate(-50%, -50%);
  background-color: rgba(255, 255, 255, 0.8);
  color: #333;
  padding: 5px 10px;
  border-radius: 4px;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  pointer-events: none;
  font-weight: bold;
  text-align: center;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.area-label.dark-mode {
  background-color: rgba(33, 33, 33, 0.8);
  color: #f0f0f0;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.user-map-panel {
  position: absolute;
  top: 70px;
  right: 400px;
  transform: none;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  width: 350px;
  z-index: 15;
  overflow: hidden;
  transition: all 0.3s ease;
}

.user-map-panel.dark-mode {
  background-color: rgba(33, 33, 33, 0.95);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.user-map-panel .panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background-color: rgba(255, 255, 255, 0.2);
}

.user-map-panel.dark-mode .panel-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.user-map-panel .panel-header h4 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.user-map-panel.dark-mode .panel-header h4 {
  color: #f0f0f0;
}

.close-panel-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  font-size: 18px;
  padding: 4px;
}

.close-panel-btn:hover {
  color: #333;
}

.user-map-panel.dark-mode .close-panel-btn {
  color: #aaa;
}

.user-map-panel.dark-mode .close-panel-btn:hover {
  color: #fff;
}

.user-map-panel .panel-content {
  padding: 20px;
}

.form-description {
  margin-bottom: 16px;
}

.form-description p {
  margin: 0;
  color: #555;
  font-size: 14px;
}

.user-map-panel.dark-mode .form-description p {
  color: #bbb;
}

.input-group {
  display: flex;
  margin-bottom: 16px;
}

.access-code-input {
  flex: 1;
  padding: 10px 16px;
  border: 1px solid #ddd;
  border-radius: 4px 0 0 4px;
  font-size: 16px;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.access-code-input.error {
  border-color: #f44336;
}

.user-map-panel.dark-mode .access-code-input {
  background-color: #333;
  border-color: #444;
  color: #fff;
}

.access-btn {
  padding: 10px 16px;
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 0 4px 4px 0;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 110px;
}

.access-btn:hover {
  background-color: #3367d6;
}

.access-btn:disabled {
  background-color: #a0bdfd;
  cursor: not-allowed;
}

.error-message {
  color: #f44336;
  font-size: 12px;
  margin-top: -8px;
  margin-bottom: 16px;
}

.option-toggle {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
}

.user-map-panel.dark-mode .option-toggle {
  color: #aaa;
}

.toggle-btn {
  background: none;
  border: none;
  color: #4285f4;
  cursor: pointer;
  font-weight: 500;
  padding: 4px;
  margin-left: 4px;
}

.toggle-btn:hover {
  text-decoration: underline;
}

/* Create map form */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.user-map-panel.dark-mode .form-group label {
  color: #f0f0f0;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.user-map-panel.dark-mode .form-input,
.user-map-panel.dark-mode .form-textarea {
  background-color: #333;
  border-color: #444;
  color: #fff;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 10px 16px;
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn:hover {
  background-color: #e5e5e5;
}

.user-map-panel.dark-mode .cancel-btn {
  background-color: #444;
  border-color: #555;
  color: #f0f0f0;
}

.user-map-panel.dark-mode .cancel-btn:hover {
  background-color: #555;
}

.create-btn {
  padding: 10px 16px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.create-btn:hover {
  background-color: #43a047;
}

.create-btn:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

/* Map selector button */
.map-selector-btn {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 5;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.map-selector-btn:hover {
  background-color: #f5f5f5;
}

.dark-mode .map-selector-btn {
  background-color: #333;
  color: white;
  border-color: #444;
}

.dark-mode .map-selector-btn:hover {
  background-color: #444;
}

.add-animal-pin-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 5;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.add-animal-pin-btn:hover {
  background-color: #f5f5f5;
}

.dark-mode .add-animal-pin-btn {
  background-color: #333;
  color: white;
  border-color: #444;
}

.dark-mode .add-animal-pin-btn:hover {
  background-color: #444;
}

.cancel-animal-pin-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 5;
  background-color: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.cancel-animal-pin-btn:hover {
  background-color: #f5f5f5;
}

.dark-mode .cancel-animal-pin-btn {
  background-color: #333;
  color: white;
  border-color: #444;
}

.dark-mode .cancel-animal-pin-btn:hover {
  background-color: #444;
}

.submit-btn {
  padding: 10px 16px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-btn:hover {
  background-color: #43a047;
}

.submit-btn:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  font-size: 18px;
  padding: 4px;
}

.close-btn:hover {
  color: #333;
}

.dark-mode .close-btn {
  color: #aaa;
}

.dark-mode .close-btn:hover {
  color: #fff;
}

.animal-pin-dialog {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  width: 350px;
  z-index: 15;
  overflow: hidden;
  transition: all 0.3s ease;
}

.animal-pin-dialog.dark-mode {
  background-color: rgba(33, 33, 33, 0.95);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background-color: rgba(255, 255, 255, 0.2);
}

.dialog-header.dark-mode {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.dialog-header.dark-mode h3 {
  color: #f0f0f0;
}

.dialog-body {
  padding: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.user-map-panel.dark-mode .form-group label {
  color: #f0f0f0;
}

.form-input, .form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.user-map-panel.dark-mode .form-input,
.user-map-panel.dark-mode .form-textarea {
  background-color: #333;
  border-color: #444;
  color: #fff;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 10px 16px;
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn:hover {
  background-color: #e5e5e5;
}

.user-map-panel.dark-mode .cancel-btn {
  background-color: #444;
  border-color: #555;
  color: #f0f0f0;
}

.user-map-panel.dark-mode .cancel-btn:hover {
  background-color: #555;
}

.submit-btn {
  padding: 10px 16px;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.submit-btn:hover {
  background-color: #43a047;
}

.submit-btn:disabled {
  background-color: #a5d6a7;
  cursor: not-allowed;
}

.animal-pin-dialog select,
.animal-pin-dialog input,
.animal-pin-dialog textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
  margin-bottom: 15px;
}

.animal-pin-dialog .form-group {
  margin-bottom: 15px;
}

.dark-mode .animal-pin-dialog {
  background-color: #333;
  color: #f0f0f0;
}

.dark-mode .animal-pin-dialog select,
.dark-mode .animal-pin-dialog input,
.dark-mode .animal-pin-dialog textarea {
  background-color: #444;
  border-color: #555;
  color: #fff;
}

.dark-mode .animal-pin-dialog label {
  color: #f0f0f0;
}

.animal-pin-dialog .form-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* Area edit button styles */
.area-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-left: 5px;
}

.edit-area-btn {
  background-color: transparent;
  color: #4285f4;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.edit-area-btn:hover {
  background-color: rgba(66, 133, 244, 0.1);
  transform: scale(1.1);
}

.dark-mode .edit-area-btn {
  color: #8ab4f8;
}

.dark-mode .edit-area-btn:hover {
  background-color: rgba(138, 180, 248, 0.1);
}

/* Area edit dialog styles */
.area-edit-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  width: 350px;
  max-width: 95vw;
  z-index: 1000;
  overflow: hidden;
}

.dark-mode .area-edit-dialog {
  background-color: #2a2a2a;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.area-edit-dialog .dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.dark-mode .area-edit-dialog .dialog-header {
  background-color: #333;
  border-bottom: 1px solid #444;
}

.area-edit-dialog .dialog-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.dark-mode .area-edit-dialog .dialog-header h3 {
  color: #f0f0f0;
}

.area-edit-dialog .close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  padding: 5px;
}

.dark-mode .area-edit-dialog .close-btn {
  color: #aaa;
}

.area-edit-dialog .dialog-body {
  padding: 20px;
}

.area-edit-dialog .form-group {
  margin-bottom: 20px;
}

.area-edit-dialog label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.dark-mode .area-edit-dialog label {
  color: #e0e0e0;
}

.area-edit-dialog input[type="text"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  color: #333;
}

.dark-mode .area-edit-dialog input[type="text"] {
  background-color: #333;
  border-color: #555;
  color: #f0f0f0;
}

.area-edit-dialog .form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.area-edit-dialog .cancel-btn {
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  color: #333;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.area-edit-dialog .save-btn {
  background-color: #4285f4;
  border: 1px solid #3367d6;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.area-edit-dialog .cancel-btn:hover {
  background-color: #e0e0e0;
}

.area-edit-dialog .save-btn:hover {
  background-color: #3367d6;
}

.dark-mode .area-edit-dialog .cancel-btn {
  background-color: #333;
  border-color: #444;
  color: #f0f0f0;
}

.dark-mode .area-edit-dialog .cancel-btn:hover {
  background-color: #444;
}

/* Area label styles */
.area-label {
  font-size: 12px;
  font-weight: bold;
  color: #333;
  background-color: rgba(255, 255, 255, 0.8);
  padding: 4px 8px;
  border-radius: 4px;
  pointer-events: none;
  text-align: center;
  white-space: nowrap;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dark-mode .area-label {
  color: #f0f0f0;
  background-color: rgba(33, 33, 33, 0.8);
}

/* Edit button styles */
.edit-button {
  background-color: transparent;
  color: #4285f4;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.edit-button:hover {
  background-color: rgba(66, 133, 244, 0.1);
  transform: scale(1.1);
}

.dark-mode .edit-button {
  color: #8ab4f8;
}

.dark-mode .edit-button:hover {
  background-color: rgba(138, 180, 248, 0.1);
}

/* Edit dialog styles */
.edit-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  width: 350px;
  max-width: 95vw;
  z-index: 1000;
  overflow: hidden;
}

.dark-mode .edit-dialog {
  background-color: #2a2a2a;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.edit-dialog .dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.dark-mode .edit-dialog .dialog-header {
  background-color: #333;
  border-bottom: 1px solid #444;
}

.edit-dialog .dialog-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.dark-mode .edit-dialog .dialog-header h3 {
  color: #f0f0f0;
}

.edit-dialog .close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  padding: 5px;
}

.dark-mode .edit-dialog .close-btn {
  color: #aaa;
}

.edit-dialog .dialog-body {
  padding: 20px;
}

.edit-dialog .form-group {
  margin-bottom: 20px;
}

.edit-dialog label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.dark-mode .edit-dialog label {
  color: #e0e0e0;
}

.edit-dialog input[type="text"] {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  color: #333;
}

.dark-mode .edit-dialog input[type="text"] {
  background-color: #333;
  border-color: #555;
  color: #f0f0f0;
}

.edit-dialog .form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.edit-dialog .cancel-btn {
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  color: #333;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.edit-dialog .save-btn {
  background-color: #4285f4;
  border: 1px solid #3367d6;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.edit-dialog .cancel-btn:hover {
  background-color: #e0e0e0;
}

.edit-dialog .save-btn:hover {
  background-color: #3367d6;
}

.dark-mode .edit-dialog .cancel-btn {
  background-color: #333;
  border-color: #444;
  color: #f0f0f0;
}

.dark-mode .edit-dialog .cancel-btn:hover {
  background-color: #444;
}
</style>

