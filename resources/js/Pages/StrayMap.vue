<script setup>
import Map from '@/Components/MapComponent.vue';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { ref, onMounted, inject, computed, onUnmounted } from 'vue';
import { QCard, QCardSection, QBtn, QIcon, QBadge, QSeparator, QTooltip, QDialog, QSelect, QSpinner, QSpace } from 'quasar';
import '../../css/stray-map.css';
import axios from 'axios';
import { Head, Link } from '@inertiajs/vue3';

// Get the global dark mode state from the AuthenticatedLayout
const isDarkMode = inject('isDarkMode', ref(false));

// Statistics data
const mapStats = ref({
    totalSightings: 0,
    dogSightings: 0,
    catSightings: 0,
    activeCCTVs: 0
});

// Tracked detections to prevent duplicates
const processedDetections = ref(new Set());

// Filter states
const filterActive = ref(false);
const selectedAnimal = ref('all');
const selectedTimeframe = ref('all');

// Toggle filter panel
const showFilters = ref(false);

// Camera pin dialog
const showCameraDialog = ref(false);
const mapRef = ref(null); // Reference to the Map component
const availableCCTVs = ref([]);
const selectedCamera = ref(null);
const loadingCCTVs = ref(false);
const cameraSelectError = ref('');
const addingPin = ref(false);
const addPinError = ref(null);
const placingPinMode = ref(false);
const addPinSuccess = ref('');
const perceptionRange = ref(30); // Default perception range in meters
const drawingAreaMode = ref(false); // State for area drawing mode

// Visual cone configuration
const showConeDialog = ref(false);
const coneDirectionDegrees = ref(0);
const coneAngleDegrees = ref(60);
const isDirectionalCamera = ref(true);
const selectedCameraInfo = ref(null);
const cameraPlacementCoordinates = ref(null);

// Detection monitoring variables
const previousDetections = ref({});
const detectionMonitorInterval = ref(null);
const isMonitoring = ref(false);
const lastApiCheckTime = ref(null);

// User map state
const currentUserMap = ref(null);
const userMaps = ref({
    owned: [],
    accessible: []
});
const userMapError = ref('');
const isLoadingMaps = ref(false);
const userMapRole = ref(null); // 'owner', 'editor', 'viewer', or null

// Computed property to determine if user can edit the current map
const canEditMap = computed(() => {
    return userMapRole.value === 'owner' || userMapRole.value === 'editor';
});

function toggleFilters() {
    showFilters.value = !showFilters.value;
}

function applyFilter(animal) {
    selectedAnimal.value = animal;
    filterActive.value = true;
}

function resetFilters() {
    selectedAnimal.value = 'all';
    selectedTimeframe.value = 'all';
    filterActive.value = false;
}

// Fetch available cameras from the CCTV API
async function fetchCCTVs() {
    loadingCCTVs.value = true;
    selectedCamera.value = null;

    try {
        console.log('Fetching cameras from API...');
        const response = await axios.get('https://straysafe.me/api2/streams');
        const streams = response.data?.streams || [];

        console.log('Received streams:', streams);

        // Transform the data for the select dropdown
        availableCCTVs.value = streams
            .filter(stream => stream.status === 'active') // Only show online cameras
            .map(stream => {
                const camera = {
                    id: stream.id,
                    name: stream.name || 'Unnamed Camera',
                    location: stream.location || 'Unknown Location',
                    videoSrc: [stream.hls_url.replace('http://', 'https://')],
                    rtmp_key: stream.rtmp_key || stream.id, // Capture rtmp_key from API
                    original_id: stream.id // Store original ID for reference
                };

                console.log('Mapped camera:', camera);
                return camera;
            });

        console.log('Available cameras:', availableCCTVs.value);

        if (availableCCTVs.value.length === 0) {
            cameraSelectError.value = 'No active cameras found. Please try again later.';
        }
    } catch (error) {
        console.error('Failed to fetch cameras:', error);
        cameraSelectError.value = 'Failed to fetch cameras: ' + (error.message || 'Unknown error');

        // Use sample data if API fails
        availableCCTVs.value = [{
            id: 'main-camera',
            name: 'Main Camera',
            location: 'Main Gate',
            videoSrc: ['https://straysafe.me/hls/main-camera.m3u8'],
            rtmp_key: 'main-camera',
            original_id: 'main-camera'
        },
        {
            id: 'dummy-camera',
            name: 'Dummy Camera',
            location: 'Test Location',
            videoSrc: ['https://straysafe.me/hls/dummy-camera.m3u8'],
            rtmp_key: 'dummy-camera',
            original_id: 'dummy-camera'
        }];

        console.log('Using fallback camera data:', availableCCTVs.value);
    } finally {
        loadingCCTVs.value = false;
    }
}

// Open the add camera dialog and fetch available cameras
function openAddCameraDialog() {
    console.log('Opening camera dialog');
    selectedCamera.value = null;
    addPinError.value = '';
    cameraSelectError.value = '';

    // Fetch available cameras
    fetchCCTVs()
        .catch(error => {
            console.error('Error fetching cameras:', error);
            cameraSelectError.value = 'Failed to load cameras. Please try again.';
        });

    showCameraDialog.value = true;
}

// Start the camera pin placement mode
function startPinPlacement() {
    console.log('Starting pin placement with selected camera:', selectedCamera.value);

    if (!selectedCamera.value) {
        alert('Please select a camera first');
        return;
    }

    // Fetch the full camera object using the selected ID
    const cameraInfo = availableCCTVs.value.find(cam => cam.id === selectedCamera.value);

    if (!cameraInfo) {
        console.error('Selected camera not found in available cameras list:', selectedCamera.value, availableCCTVs.value);
        alert('Selected camera information not found. Please try selecting again.');
        return;
    }

    console.log('Found camera info:', cameraInfo);

    // Store camera info for later use
    selectedCameraInfo.value = {
        ...cameraInfo,
        perceptionRange: perceptionRange.value,
        rtmp_key: cameraInfo.rtmp_key || cameraInfo.id,
        original_id: cameraInfo.id
    };

    placingPinMode.value = true;
    showCameraDialog.value = false;

    // Display clear instructions to the user
    alert("Click on the map to place the camera pin. After placement, you'll be able to visually set the camera's viewing direction and angle.");

    // Enable pin placement mode in the map component
    if (mapRef.value) {
        try {
            mapRef.value.enablePinPlacementMode((coordinates) => {
                console.log('User clicked map at coordinates:', coordinates);

                // Store coordinates for later camera cone placement
                cameraPlacementCoordinates.value = coordinates;

                // Show cone configuration dialog
                placingPinMode.value = false;
                showConeDialog.value = true;
            });
        } catch (error) {
            console.error('Failed to enable pin placement mode:', error);
            alert('Failed to enter pin placement mode. Please try again.');
            placingPinMode.value = false;
        }
    } else {
        console.error('Map reference not available');
        alert('Map is not ready. Please try again in a moment.');
        placingPinMode.value = false;
    }
}

// Complete camera placement after cone configuration
function completeCameraPlacement() {
    if (!selectedCameraInfo.value || !cameraPlacementCoordinates.value) {
        alert('Missing camera information. Please try again.');
        showConeDialog.value = false;
        return;
    }

    // Create the enhanced camera info with cone settings
    const enhancedCameraInfo = {
        ...selectedCameraInfo.value,
        viewingDirection: coneDirectionDegrees.value,
        viewingAngle: coneAngleDegrees.value,
        conicalView: isDirectionalCamera.value
    };

    console.log('Enhanced camera info with viewing parameters:', enhancedCameraInfo);

    // Add the camera pin with cone
    addCameraPin(cameraPlacementCoordinates.value, enhancedCameraInfo)
        .then(response => {
            console.log('Camera pin add response:', response);

            // Check if response exists and has data
            if (response && response.data && response.data.success) {
                console.log('Camera pin added successfully:', response.data);
                alert('Camera pin placed successfully!');
            } else {
                console.error('Pin was added visually but failed to save to server:', response?.error || 'Unknown error');
                alert('Pin was placed on map but could not be saved to the server. The pin will be visible until you refresh the page.');
            }

            // Close cone dialog
            showConeDialog.value = false;

            // Reset values
            selectedCameraInfo.value = null;
            cameraPlacementCoordinates.value = null;
        })
        .catch(error => {
            console.error('Error adding camera pin:', error);
            alert('Failed to place camera pin. Please try again.');
            showConeDialog.value = false;
        });
}

// Cancel cone configuration
function cancelConeConfiguration() {
    showConeDialog.value = false;
    selectedCameraInfo.value = null;
    cameraPlacementCoordinates.value = null;
}

// Function to add a camera pin to the map
async function addCameraPin(coordinates, cameraInfo) {
    try {
        console.log('Adding camera pin with coordinates:', coordinates, 'and camera:', cameraInfo);

        if (!mapRef.value) {
            throw new Error('Map reference not available');
        }

        // Add perception range to camera info
        const cameraInfoWithRange = {
            ...cameraInfo,
            perceptionRange: perceptionRange.value
        };

        // Forward the addCameraPin call to the map component
        const result = await mapRef.value.addCameraPin(coordinates, cameraInfoWithRange);

        console.log('Camera pin add result:', result);

        if (result && result.success === false) {
            // Handle partial success (pin is visible but not saved)
            console.warn('Pin added visually but failed to save to server:', result.error);
            addPinError.value = 'Camera pin was added to map but could not be saved to server';
        } else {
            // Handle complete success
            console.log('Camera pin added successfully:', result);
            addPinSuccess.value = 'Camera pin added successfully';

            // Clear success message after 3 seconds
            setTimeout(() => {
                addPinSuccess.value = '';
            }, 3000);
        }

        // Return the result for further processing
        return result;
    } catch (error) {
        console.error('Error in addCameraPin:', error);
        addPinError.value = `Failed to add camera pin: ${error.message}`;

        // Clear error message after 5 seconds
        setTimeout(() => {
            addPinError.value = '';
        }, 5000);

        throw error;
    }
}

// Check for new detections from the API
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
    const cameraPins = await mapRef.value.getCameraPinLocations();
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
        `cam-${pin.rtmp_key}`
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
      const cameraPin = streamToCameraMap[animal.stream_id];

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
        // These will be set by addAnimalPin based on the camera cone
        lng: null,
        lat: null,
        // Pass camera info for proper placement
        cameraInfo: {
          ...cameraPin,
          conicalView: cameraPin.conicalView,
          viewingDirection: cameraPin.viewingDirection,
          viewingAngle: cameraPin.viewingAngle,
          perceptionRange: cameraPin.perceptionRange
        }
      };

      // Add the animal pin
      try {
        const result = await mapRef.value.addAnimalPin(pinData);
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

// Function to monitor detection changes from API
async function monitorDetections() {
  console.log('Starting detection monitor');
  isMonitoring.value = true;

  // Clear any existing interval
  if (detectionMonitorInterval.value) {
    clearInterval(detectionMonitorInterval.value);
  }

  // Initial check for detections
  try {
    await checkForDetectedAnimals();
  } catch (error) {
    console.error('Failed to establish detection baseline:', error);
  }

  // Set up the interval to check for new detections every 10 seconds
  detectionMonitorInterval.value = setInterval(async () => {
    try {
      await checkForDetectedAnimals();
    } catch (error) {
      console.error('Error monitoring detections:', error);
    }
  }, 10000); // Check every 10 seconds
}

// Function to pause detection monitoring
function pauseMonitoring() {
  console.log('Pausing detection monitor');

  if (detectionMonitorInterval.value) {
    clearInterval(detectionMonitorInterval.value);
    detectionMonitorInterval.value = null;
  }

  isMonitoring.value = false;
}

// Function to fetch and update statistics
async function fetchStats() {
    try {
        const response = await axios.get('/api/pins/stats');
        if (response.data) {
            mapStats.value = response.data;
        }
    } catch (error) {
        console.error('Failed to fetch statistics:', error);
    }
}

// Load the user's maps
async function loadUserMaps() {
    isLoadingMaps.value = true;
    userMapError.value = '';

    try {
        const response = await axios.get('/user-maps');

        if (response.data) {
            userMaps.value.owned = response.data.owned_maps || [];
            userMaps.value.accessible = response.data.accessible_maps || [];

            console.log('User maps loaded:', userMaps.value);

            // If user has a personal map, set it as current
            if (userMaps.value.owned.length > 0) {
                await setCurrentMap(userMaps.value.owned[0]);
            }
        }
    } catch (error) {
        console.error('Error loading user maps:', error);
        userMapError.value = 'Failed to load your maps. Please try again.';
    } finally {
        isLoadingMaps.value = false;
    }
}

// Set the current map
async function setCurrentMap(map) {
    try {
        if (!map || !map.id) {
            currentUserMap.value = null;
            userMapRole.value = null;
            return;
        }

        // Fetch latest map data including pins
        const response = await axios.get(`/user-maps/${map.id}`);

        if (response.data.success) {
            currentUserMap.value = response.data.map;
            userMapRole.value = response.data.role;

            console.log('Current map set:', currentUserMap.value, 'Role:', userMapRole.value);

            // If map has default view, navigate to it
            if (currentUserMap.value.default_view && mapRef.value) {
                const defaultView = currentUserMap.value.default_view;
                if (defaultView.center && defaultView.zoom) {
                    mapRef.value.navigateToLocation(defaultView.center, defaultView.zoom);
                }
            }

            // Ensure camera pins have viewing parameters and update map pins
            if (mapRef.value && currentUserMap.value.pins) {
                const pinsWithViewParams = currentUserMap.value.pins.map(pin => {
                    return {
                        ...pin,
                        viewingDirection: pin.viewingDirection || 0,
                        viewingAngle: pin.viewingAngle || 60,
                        conicalView: pin.conicalView !== undefined ? pin.conicalView : true
                    };
                });
                // Update pins on the map component
                mapRef.value.updatePinsWithViewParams(pinsWithViewParams);
            }
        } else {
            userMapError.value = response.data.message || 'Failed to load map data';
        }
    } catch (error) {
        console.error('Error setting current map:', error);
        userMapError.value = 'Failed to load map data. Please try again.';
    }
}

// Handle map created event
function handleMapCreated(map) {
    console.log('Map created:', map);
    // Add to owned maps
    userMaps.value.owned.push(map);
    // Set as current map
    setCurrentMap(map);
}

// Handle map accessed event
function handleMapAccessed(map) {
    console.log('Map accessed:', map);

    // Check if this map is already in accessible maps
    const existingMapIndex = userMaps.value.accessible.findIndex(m => m.id === map.id);

    if (existingMapIndex >= 0) {
        // Update the existing map data
        userMaps.value.accessible[existingMapIndex] = map;
    } else {
        // Add to accessible maps
        userMaps.value.accessible.push(map);
    }

    // Set as current map
    setCurrentMap(map);
}

// Handle map ready event
function handleMapReady() {
    console.log('Map is ready');
    // If we have a current map with default view, navigate to it
    if (currentUserMap.value?.default_view && mapRef.value) {
        const defaultView = currentUserMap.value.default_view;
        if (defaultView.center && defaultView.zoom) {
            mapRef.value.navigateToLocation(defaultView.center, defaultView.zoom);
        }
    }
}

// Regenerate access code for the current map
async function regenerateAccessCode() {
    if (!currentUserMap.value || userMapRole.value !== 'owner') return;

    try {
        const response = await axios.post(`/user-maps/${currentUserMap.value.id}/regenerate-code`);

        if (response.data.success) {
            // Update the access code in the current map
            currentUserMap.value.access_code = response.data.access_code;

            // Show success message
            alert('Access code regenerated successfully. Share the new code with others who need access to this map.');
        } else {
            console.error('Failed to regenerate access code:', response.data.message);
            alert('Failed to regenerate access code. Please try again.');
        }
    } catch (error) {
        console.error('Error regenerating access code:', error);
        alert('An error occurred while regenerating the access code. Please try again.');
    }
}

// Start area drawing mode
function startAreaDrawing() {
  console.log('Starting area drawing mode');

  if (!mapRef.value) {
    alert('Map is not ready. Please try again in a moment.');
    return;
  }

  try {
    // Enable drawing mode on the map component
    if (mapRef.value.enableDrawingMode('polygon')) {
      drawingAreaMode.value = true;
      // Show alert about how to complete/cancel the drawing
      alert('Click on the map to start drawing. Click points to create your area shape, then click the first point again to complete the shape. Use the Cancel button to exit drawing mode.');
    } else {
      console.error('Failed to enable drawing mode');
      alert('Failed to enter drawing mode. Please try again.');
    }
  } catch (error) {
    console.error('Error enabling drawing mode:', error);
    alert('An error occurred while trying to draw an area. Please try again.');
  }
}

// Cancel area drawing
function cancelAreaDrawing() {
  console.log('Cancelling area drawing mode');

  if (!mapRef.value) {
    return;
  }

  try {
    // Cancel the current drawing
    mapRef.value.cancelDrawing();
    // Disable drawing mode
    mapRef.value.disableDrawingMode();
    // Update local state
    drawingAreaMode.value = false;
  } catch (error) {
    console.error('Error cancelling drawing mode:', error);
  }
}

// Handle draw-complete event
function handleDrawComplete(feature) {
    console.log('Drawing completed, auto-saving area:', feature);
    // Set a default name based on timestamp
    const areaName = `Area ${new Date().toLocaleTimeString()}`;

    // Add properties to the feature
    feature.properties = feature.properties || {};
    feature.properties.name = areaName;
    feature.properties.description = `Area created on ${new Date().toLocaleDateString()}`;

    // Attempt to save the area
    try {
      // The MapComponent will automatically save this to the current map
      mapRef.value.saveUserArea(feature);
      // Show success notification
      alert(`Area "${areaName}" has been saved to your map.`);
    } catch (error) {
      console.error('Error saving area:', error);
      alert('Failed to save the area. Please try again.');
    }

    // Reset drawing mode state
    drawingAreaMode.value = false;
}

// Setup initial state on mount
onMounted(async () => {
    await loadUserMaps();
    // Start the detection monitor
    monitorDetections();
    // Fetch initial statistics
    fetchStats();

    // Set up interval to refresh stats every minute
    const statsInterval = setInterval(fetchStats, 60000);

    // Clean up interval on unmount
    onUnmounted(() => {
        clearInterval(statsInterval);
    });
});

onUnmounted(() => {
  // Clean up monitor interval when component is destroyed
  if (detectionMonitorInterval.value) {
    clearInterval(detectionMonitorInterval.value);
    detectionMonitorInterval.value = null;
  }
});
</script>

<template>
    <Head title="Stray Map" />
    <AuthenticatedLayout>
        <!-- Main container with consistent padding -->
        <div class="stray-map-container px-6 py-4" :class="{ 'dark-mode': isDarkMode }">
            <!-- Standardized Header Section -->
            <div class="page-header px-6">
                <div class="flex justify-between items-center">
                    <div class="header-title">
                        <h1 class="text-3xl font-bold font-poppins">Stray Animal Map</h1>
                        <p class="text-gray-600 dark:text-gray-400">Track stray animals in your area</p>
                    </div>

                    <!-- Map Controls -->
                    <div class="header-actions flex gap-3">
                        <q-btn
                            class="primary-btn"
                            :class="{ 'active-btn': filterActive }"
                            @click="toggleFilters"
                        >
                            <q-icon name="filter_alt" class="q-mr-sm" />
                            Filters
                            <q-tooltip>Toggle filter options</q-tooltip>
                        </q-btn>
                        <q-btn
                            class="secondary-btn"
                            @click="$emit('refresh')"
                        >
                            <q-icon name="refresh" class="q-mr-sm" />
                            Refresh
                            <q-tooltip>Refresh map data</q-tooltip>
                        </q-btn>
                        <!-- Area creation button -->
                        <q-btn
                            v-if="canEditMap && currentUserMap"
                            class="primary-btn"
                            @click="startAreaDrawing"
                            :disable="placingPinMode || drawingAreaMode"
                        >
                            <q-icon name="dashboard_customize" class="q-mr-sm" />
                            Create Area
                            <q-tooltip>Draw an area on the map</q-tooltip>
                        </q-btn>
                        <!-- Cancel area drawing button -->
                        <q-btn
                            v-if="drawingAreaMode"
                            class="cancel-btn"
                            color="red"
                            @click="cancelAreaDrawing"
                        >
                            <q-icon name="cancel" class="q-mr-sm" />
                            Cancel Area Drawing
                            <q-tooltip>Exit area drawing mode</q-tooltip>
                        </q-btn>
                        <q-btn
                            class="primary-btn"
                            @click="openAddCameraDialog"
                            :disable="placingPinMode || drawingAreaMode"
                        >
                            <q-icon name="add_location" class="q-mr-sm" />
                            Add Camera Pin
                            <q-tooltip>Select a camera and place it on the map</q-tooltip>
                        </q-btn>
                        <q-btn
                            v-if="placingPinMode"
                            class="cancel-btn"
                            color="red"
                            @click="cancelPinPlacement"
                        >
                            <q-icon name="cancel" class="q-mr-sm" />
                            Cancel Pin Placement
                            <q-tooltip>Exit pin placement mode</q-tooltip>
                        </q-btn>
                    </div>
                </div>
            </div>

            <!-- Filter Panel (conditionally shown) -->
            <div v-if="showFilters" class="filter-panel mb-4">
                <q-card flat class="theme-card">
                    <q-card-section>
                        <div class="flex flex-wrap gap-4">
                            <div>
                                <p class="text-sm font-medium mb-2">Animal Type</p>
                                <div class="flex gap-2">
                                    <q-btn
                                        class="filter-option-btn"
                                        :class="{ 'active': selectedAnimal === 'all' }"
                                        label="All"
                                        size="sm"
                                        @click="applyFilter('all')"
                                    />
                                    <q-btn
                                        class="filter-option-btn"
                                        :class="{ 'active': selectedAnimal === 'dog' }"
                                        label="Dogs"
                                        size="sm"
                                        @click="applyFilter('dog')"
                                    />
                                    <q-btn
                                        class="filter-option-btn"
                                        :class="{ 'active': selectedAnimal === 'cat' }"
                                        label="Cats"
                                        size="sm"
                                        @click="applyFilter('cat')"
                                    />
                                </div>
                            </div>

                            <div>
                                <p class="text-sm font-medium mb-2">Time Period</p>
                                <div class="flex gap-2">
                                    <q-btn
                                        class="filter-option-btn"
                                        :class="{ 'active': selectedTimeframe === 'all' }"
                                        label="All Time"
                                        size="sm"
                                        @click="selectedTimeframe = 'all'"
                                    />
                                    <q-btn
                                        class="filter-option-btn"
                                        :class="{ 'active': selectedTimeframe === 'week' }"
                                        label="This Week"
                                        size="sm"
                                        @click="selectedTimeframe = 'week'"
                                    />
                                    <q-btn
                                        class="filter-option-btn"
                                        :class="{ 'active': selectedTimeframe === 'month' }"
                                        label="This Month"
                                        size="sm"
                                        @click="selectedTimeframe = 'month'"
                                    />
                                </div>
                            </div>

                            <div class="ml-auto self-end">
                                <q-btn
                                    class="reset-btn"
                                    label="Reset"
                                    size="sm"
                                    @click="resetFilters"
                                />
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
            </div>

            <!-- Placement Mode Alert -->
            <div v-if="placingPinMode" class="placement-alert mb-4">
                <q-card class="bg-blue-100 dark:bg-blue-900">
                    <q-card-section class="flex items-center justify-between">
                        <div class="flex items-center">
                            <q-icon name="info" size="md" color="primary" class="mr-3" />
                            <span class="text-blue-800 dark:text-blue-100">
                                Click anywhere on the map to place the camera pin
                            </span>
                        </div>
                        <q-btn flat round color="primary" icon="close" size="sm" @click="cancelPinPlacement" />
                    </q-card-section>
                </q-card>
            </div>

            <!-- Drawing Mode Alert -->
            <div v-if="drawingAreaMode" class="drawing-alert mb-4">
                <q-card class="bg-green-100 dark:bg-green-900">
                    <q-card-section class="flex items-center justify-between">
                        <div class="flex items-center">
                            <q-icon name="edit" size="md" color="green" class="mr-3" />
                            <span class="text-green-800 dark:text-green-100">
                                Click on the map to draw your area. Click the first point again to complete the shape.
                            </span>
                        </div>
                        <q-btn flat round color="green" icon="close" size="sm" @click="cancelAreaDrawing" />
                    </q-card-section>
                </q-card>
            </div>

            <!-- Detection Monitor Status -->
            <div class="detection-monitor-status mb-4">
                <q-card flat class="theme-card">
                    <q-card-section>
                        <div class="flex items-center justify-between">
                            <div class="flex items-center">
                                <q-icon
                                    :name="isMonitoring ? 'sensors' : 'sensors_off'"
                                    :color="isMonitoring ? 'positive' : 'negative'"
                                    size="md"
                                    class="mr-3"
                                />
                                <div>
                                    <div class="text-lg font-medium">Animal Detection Monitor</div>
                                    <div class="text-sm text-gray-600 dark:text-gray-400">
                                        {{ isMonitoring ? 'Actively monitoring for new detections' : 'Detection monitoring is paused' }}
                                    </div>
                                </div>
                            </div>
                            <div>
                                <q-btn
                                    v-if="!isMonitoring"
                                    class="primary-btn"
                                    icon="play_arrow"
                                    label="Start Monitoring"
                                    @click="monitorDetections"
                                />
                                <q-btn
                                    v-else
                                    class="secondary-btn"
                                    icon="pause"
                                    label="Pause Monitoring"
                                    @click="pauseMonitoring"
                                />
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
            </div>

            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div class="stat-card">
                    <div class="stat-icon total-icon">
                        <q-icon name="visibility" size="sm" />
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ mapStats.totalSightings }}</div>
                        <div class="stat-label">Total Sightings</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon dog-icon">
                        <q-icon name="pets" size="sm" />
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ mapStats.dogSightings }}</div>
                        <div class="stat-label">Dog Sightings</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon cat-icon">
                        <q-icon name="pets" size="sm" />
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ mapStats.catSightings }}</div>
                        <div class="stat-label">Cat Sightings</div>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon cctv-icon">
                        <q-icon name="videocam" size="sm" />
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ mapStats.activeCCTVs }}</div>
                        <div class="stat-label">Active CCTVs</div>
                    </div>
                </div>
            </div>

            <!-- Map Container -->
            <Map
                ref="mapRef"
                :is-dark-mode="isDarkMode"
                @map-ready="handleMapReady"
                @map-created="handleMapCreated"
                @map-accessed="handleMapAccessed"
                @draw-complete="handleDrawComplete"
                :is-map-owner="userMapRole === 'owner'"
                :user-map-id="currentUserMap?.id"
                :map-name="currentUserMap?.name"
                :map-access-code="currentUserMap?.access_code"
            />

            <!-- User Map Info Card -->
            <!-- <div v-if="currentUserMap" class="map-info-card" :class="{ 'dark-mode': isDarkMode }">
                <div class="map-info-header">
                    <h3>{{ currentUserMap.name }}</h3>
                    <div class="map-info-badge" :class="userMapRole">{{ userMapRole }}</div>
                </div>
                <div v-if="currentUserMap.description" class="map-info-description">
                    {{ currentUserMap.description }}
                </div>
                <div class="map-info-access">
                    <div class="access-code-display">
                        <span class="access-label">Access Code:</span>
                        <span class="access-value">{{ currentUserMap.access_code }}</span>
                    </div>
                    <button
                        v-if="userMapRole === 'owner'"
                        @click="regenerateAccessCode"
                        class="regenerate-btn"
                        title="Generate a new access code"
                    >
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
            </div> -->

            <!-- Add Camera Dialog -->
            <q-dialog v-model="showCameraDialog" persistent>
                <q-card class="add-camera-dialog">
                    <q-card-section class="row items-center q-pb-none">
                        <div class="text-h6">Add Camera Pin</div>
                        <q-space />
                        <q-btn icon="close" flat round dense v-close-popup />
                    </q-card-section>

                    <q-card-section>
                        <p>Select a camera to add to the map. After selection, you will be prompted to click on the map to place the camera pin at the desired location.</p>

                        <div v-if="cameraSelectError" class="text-negative q-mb-md">{{ cameraSelectError }}</div>

                        <q-select
                            v-model="selectedCamera"
                            :options="availableCCTVs"
                            option-value="id"
                            option-label="name"
                            label="Select Camera"
                            emit-value
                            map-options
                            :loading="loadingCCTVs"
                            :disable="loadingCCTVs || addingPin"
                        >
                            <template v-slot:option="scope">
                                <q-item v-bind="scope.itemProps">
                                    <q-item-section>
                                        <q-item-label>{{ scope.opt.name }}</q-item-label>
                                        <q-item-label caption>{{ scope.opt.location }}</q-item-label>
                                    </q-item-section>
                                </q-item>
                            </template>

                            <template v-slot:no-option>
                                <q-item>
                                    <q-item-section class="text-grey">
                                        No cameras found
                                    </q-item-section>
                                </q-item>
                            </template>

                            <template v-slot:loading>
                                <q-item>
                                    <q-item-section class="text-grey">
                                        <q-spinner color="primary" />
                                        Loading cameras...
                                    </q-item-section>
                                </q-item>
                            </template>
                        </q-select>

                        <!-- Perception Range Slider -->
                        <div class="q-mt-md">
                            <div class="text-subtitle2 q-mb-sm">Camera Perception Range</div>
                            <div class="flex items-center">
                                <span class="q-mr-sm">10m</span>
                                <q-slider
                                    v-model="perceptionRange"
                                    :min="10"
                                    :max="100"
                                    :step="5"
                                    label
                                    :label-value="`${perceptionRange}m`"
                                    class="col"
                                    color="primary"
                                />
                                <span class="q-ml-sm">100m</span>
                            </div>
                            <p class="text-caption text-grey q-mt-xs">
                                Set how far this camera can detect animals ({{ perceptionRange }} meters)
                            </p>
                        </div>
                    </q-card-section>

                    <q-card-section class="q-pt-none">
                        <p class="text-caption text-grey">
                            Tip: After selecting a camera, click on the map to place the pin at the exact location.
                        </p>
                    </q-card-section>

                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" color="negative" v-close-popup />
                        <q-btn flat label="Place on Map" color="primary" @click="startPinPlacement" :loading="addingPin" :disable="!selectedCamera || addingPin" />
                    </q-card-actions>
                </q-card>
            </q-dialog>

            <!-- Camera Cone Configuration Dialog -->
            <q-dialog v-model="showConeDialog" persistent>
                <q-card class="cone-config-dialog">
                    <q-card-section class="row items-center q-pb-none">
                        <div class="text-h6">Configure Camera View</div>
                        <q-space />
                        <q-btn icon="close" flat round dense @click="cancelConeConfiguration" />
                    </q-card-section>

                    <q-card-section>
                        <p>Set up how your camera views the surrounding area.</p>

                        <div class="q-mt-md">
                            <q-toggle
                                v-model="isDirectionalCamera"
                                label="This is a directional camera (faces a specific direction)"
                            />
                        </div>

                        <div v-if="isDirectionalCamera" class="q-mt-md">
                            <!-- Visual direction picker -->
                            <div class="direction-picker-container">
                                <div class="direction-picker" :style="`--rotation: ${coneDirectionDegrees}deg`">
                                    <div class="direction-circle">
                                        <div class="direction-marker">N</div>
                                        <div class="direction-marker east">E</div>
                                        <div class="direction-marker south">S</div>
                                        <div class="direction-marker west">W</div>
                                        <div class="direction-pointer"></div>
                                        <div class="direction-cone" :style="`--angle: ${coneAngleDegrees}deg`"></div>
                                    </div>
                                </div>
                            </div>

                            <!-- Direction control -->
                            <div class="q-mt-md">
                                <div class="text-subtitle2 q-mb-sm">Camera Direction: {{ coneDirectionDegrees }}°</div>
                                <div class="flex items-center">
                                    <span class="q-mr-sm">0° (N)</span>
                                    <q-slider
                                        v-model="coneDirectionDegrees"
                                        :min="0"
                                        :max="359"
                                        :step="1"
                                        label
                                        :label-value="`${coneDirectionDegrees}°`"
                                        class="col"
                                        color="primary"
                                    />
                                    <span class="q-ml-sm">359°</span>
                                </div>
                            </div>

                            <!-- Angle control -->
                            <div class="q-mt-md">
                                <div class="text-subtitle2 q-mb-sm">View Angle: {{ coneAngleDegrees }}°</div>
                                <div class="flex items-center">
                                    <span class="q-mr-sm">10°</span>
                                    <q-slider
                                        v-model="coneAngleDegrees"
                                        :min="10"
                                        :max="180"
                                        :step="5"
                                        label
                                        :label-value="`${coneAngleDegrees}°`"
                                        class="col"
                                        color="primary"
                                    />
                                    <span class="q-ml-sm">180°</span>
                                </div>
                            </div>
                        </div>

                        <div v-else class="q-mt-md text-center">
                            <div class="direction-picker-container">
                                <div class="direction-picker 360-view">
                                    <div class="direction-circle">
                                        <div class="direction-marker">N</div>
                                        <div class="direction-marker east">E</div>
                                        <div class="direction-marker south">S</div>
                                        <div class="direction-marker west">W</div>
                                        <div class="direction-360-view"></div>
                                    </div>
                                </div>
                            </div>
                            <p class="q-mt-sm">360° view selected. Camera will monitor in all directions.</p>
                        </div>
                    </q-card-section>

                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" color="negative" @click="cancelConeConfiguration" />
                        <q-btn flat label="Add Camera" color="positive" @click="completeCameraPlacement" />
                    </q-card-actions>
                </q-card>
            </q-dialog>

            <!-- Placement mode indicator -->
            <div v-if="placingPinMode" class="placement-mode-indicator">
                <div class="indicator-content">
                    <q-icon name="place" size="md" class="q-mr-sm" color="primary" />
                    <span>Click on the map to place the camera pin</span>
                    <q-space />
                    <q-btn color="negative" label="Cancel" @click="cancelPinPlacement" flat />
                </div>
            </div>

            <!-- Action buttons -->
            <div class="map-action-buttons">
                <!-- Error/Success message display -->
                <div v-if="addPinError" class="error-banner">
                    {{ addPinError }}
                </div>
                <div v-if="addPinSuccess" class="success-banner">
                    {{ addPinSuccess }}
                </div>
            </div>
        </div>
    </AuthenticatedLayout>
</template>

<style scoped>
.add-camera-dialog {
    width: 500px;
    max-width: 90vw;
}

.placement-alert {
    animation: pulse 2s infinite;
}

.drawing-alert {
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% {
        opacity: 0.8;
    }
    50% {
        opacity: 1;
    }
    100% {
        opacity: 0.8;
    }
}

.cancel-btn {
    background-color: rgba(244, 67, 54, 0.8);
    color: white;
}

.cancel-btn:hover {
    background-color: rgb(244, 67, 54);
}

.placement-mode-indicator {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: rgba(255, 255, 255, 0.8);
    padding: 10px;
    z-index: 1000;
}

.indicator-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.map-action-buttons {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.error-banner {
  background-color: #f44336;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  margin-bottom: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.success-banner {
  background-color: #4caf50;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  margin-bottom: 10px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

/* Map Info Card styles */
.map-info-card {
    position: absolute;
    top: 20px;
    right: 20px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 15px;
    min-width: 250px;
    z-index: 5;
    font-size: 14px;
}

.map-info-card.dark-mode {
    background-color: #333;
    color: white;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.map-info-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
}

.map-info-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
}

.map-info-badge {
    font-size: 12px;
    padding: 3px 8px;
    border-radius: 12px;
    text-transform: capitalize;
}

.map-info-badge.owner {
    background-color: #4caf50;
    color: white;
}

.map-info-badge.editor {
    background-color: #2196f3;
    color: white;
}

.map-info-badge.viewer {
    background-color: #ff9800;
    color: white;
}

.map-info-description {
    font-size: 13px;
    color: #666;
    margin-bottom: 12px;
    border-bottom: 1px solid #eee;
    padding-bottom: 12px;
}

.dark-mode .map-info-description {
    color: #bbb;
    border-bottom-color: #444;
}

.map-info-access {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.access-code-display {
    font-family: monospace;
    font-size: 14px;
    letter-spacing: 1px;
}

.access-label {
    font-size: 12px;
    color: #666;
    margin-right: 5px;
}

.dark-mode .access-label {
    color: #bbb;
}

.access-value {
    font-weight: bold;
    color: #333;
}

.dark-mode .access-value {
    color: #fff;
}

.regenerate-btn {
    background: none;
    border: none;
    color: #2196f3;
    cursor: pointer;
    font-size: 14px;
}

.regenerate-btn:hover {
    color: #0d8bf2;
}

.dark-mode .regenerate-btn {
    color: #64b5f6;
}

.dark-mode .regenerate-btn:hover {
    color: #90caf9;
}

.cone-config-dialog {
    width: 500px;
    max-width: 90vw;
}

.direction-picker-container {
    display: flex;
    justify-content: center;
    margin: 20px 0;
}

.direction-picker {
    position: relative;
    width: 200px;
    height: 200px;
    --rotation: 0deg;
}

.direction-circle {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    border: 2px solid #ccc;
    position: relative;
    background-color: #f5f5f5;
}

.direction-marker {
    position: absolute;
    top: 5px;
    left: 50%;
    transform: translateX(-50%);
    font-weight: bold;
}

.direction-marker.east {
    top: 50%;
    left: auto;
    right: 5px;
    transform: translateY(-50%);
}

.direction-marker.south {
    top: auto;
    bottom: 5px;
    left: 50%;
    transform: translateX(-50%);
}

.direction-marker.west {
    top: 50%;
    left: 5px;
    transform: translateY(-50%);
}

.direction-pointer {
    position: absolute;
    top: 50%;
    left: 50%;
    height: 2px;
    width: 50%;
    background-color: #4f6642;
    transform-origin: left center;
    transform: rotate(var(--rotation));
}

.direction-pointer::after {
    content: '';
    position: absolute;
    right: -5px;
    top: -4px;
    width: 0;
    height: 0;
    border-left: 10px solid #4f6642;
    border-top: 5px solid transparent;
    border-bottom: 5px solid transparent;
}

.direction-cone {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 100px;
    height: 100px;
    --angle: 60deg;
    background-color: rgba(79, 102, 66, 0.3);
    clip-path: polygon(0 0, calc(50% + 50% * tan(calc(var(--angle) / 2 * 1deg))) 100%, calc(50% - 50% * tan(calc(var(--angle) / 2 * 1deg))) 100%);
    transform-origin: center top;
    transform: translateX(-50%) rotate(calc(var(--rotation) - 90deg));
}

.direction-360-view {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 140px;
    height: 140px;
    border-radius: 50%;
    background-color: rgba(79, 102, 66, 0.3);
    transform: translate(-50%, -50%);
}

.dark-mode .direction-circle {
    background-color: #333;
    border-color: #555;
}

.dark-mode .direction-marker {
    color: #fff;
}

.dark-mode .direction-cone {
    background-color: rgba(56, 163, 165, 0.3);
}

.dark-mode .direction-360-view {
    background-color: rgba(56, 163, 165, 0.3);
}
</style>