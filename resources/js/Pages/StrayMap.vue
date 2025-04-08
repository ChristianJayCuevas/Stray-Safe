<script setup>
import Map from '@/Components/MapComponent.vue';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { ref, onMounted, inject, computed, onUnmounted } from 'vue';
import { QCard, QCardSection, QBtn, QIcon, QBadge, QSeparator, QTooltip, QDialog, QSelect, QSpinner, QSpace } from 'quasar';
import '../../css/stray-map.css';
import axios from 'axios';

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

// Detection monitoring variables
const previousDetections = ref({});
const detectionMonitorInterval = ref(null);
const isMonitoring = ref(false);
const lastApiCheckTime = ref(null);

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
    
    // Ask user if this is a directional camera
    const isDirectional = confirm('Is this a directional camera (with a specific viewing angle)?\nClick OK for directional, Cancel for 360-degree view.');
    
    let viewingDirection = 0;
    let viewingAngle = 60; // Default viewing angle for directional cameras
    
    if (isDirectional) {
        // Ask for viewing direction (0-360 degrees)
        const directionPrompt = prompt('Enter the viewing direction in degrees (0-360):\n0° = North, 90° = East, 180° = South, 270° = West', '0');
        if (directionPrompt === null) {
            // User cancelled
            viewingDirection = 0;
        } else {
            viewingDirection = parseInt(directionPrompt) || 0;
            // Ensure value is between 0-360
            viewingDirection = Math.max(0, Math.min(360, viewingDirection));
        }
        
        // Ask for viewing angle
        const anglePrompt = prompt('Enter the camera\'s field of view angle in degrees (10-180):', '60');
        if (anglePrompt === null) {
            // User cancelled
            viewingAngle = 60;
        } else {
            viewingAngle = parseInt(anglePrompt) || 60;
            // Ensure value is between 10-180
            viewingAngle = Math.max(10, Math.min(180, viewingAngle));
        }
    }
    
    // Add conical view properties to camera info
    const enhancedCameraInfo = {
        ...cameraInfo,
        perceptionRange: perceptionRange.value,
        viewingDirection: viewingDirection,
        viewingAngle: viewingAngle,
        conicalView: isDirectional,
        rtmp_key: cameraInfo.rtmp_key || cameraInfo.id, // Use the RTMP key from the API if available
        original_id: cameraInfo.id, // Store original ID for reference
    };
    
    console.log('Enhanced camera info with viewing parameters:', enhancedCameraInfo);
    
    placingPinMode.value = true;
    showCameraDialog.value = false;
    
    // Display clear instructions to the user
    alert(`Click on the map to place the camera pin${isDirectional ? ` with a viewing direction of ${viewingDirection}° and field of view of ${viewingAngle}°` : ''}.\nYou can click the Cancel button to exit placement mode.`);
    
    // Enable pin placement mode in the map component
    if (mapRef.value) {
        try {
            mapRef.value.enablePinPlacementMode((coordinates) => {
                console.log('User clicked map at coordinates:', coordinates);
                // When user clicks on map, add the camera pin with the selected camera
                addCameraPin(coordinates, enhancedCameraInfo)
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
                        // Reset placement mode regardless of success/failure
                        placingPinMode.value = false;
                        mapRef.value.disablePinPlacementMode();
                    })
                    .catch(error => {
                        console.error('Error adding camera pin:', error);
                        alert('Failed to place camera pin. Please try again.');
                        // Reset placement mode on error
                        placingPinMode.value = false;
                        mapRef.value.disablePinPlacementMode();
                    });
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

// Cancel the pin placement mode
function cancelPinPlacement() {
    console.log('Cancelling pin placement mode');
    placingPinMode.value = false;
    
    // Disable pin placement mode in the map component
    if (mapRef.value) {
        try {
            mapRef.value.disablePinPlacementMode();
        } catch (error) {
            console.error('Error disabling pin placement mode:', error);
        }
    }
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

// Start and stop monitoring on component mount/unmount
onMounted(() => {
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
    <AuthenticatedLayout>
        <!-- Standardized Header Section -->
        <div class="page-header mx-6 mt-6 mb-6">
            <div class="flex justify-between items-center">
                <div class="header-title">
                    <h1 class="text-3xl font-bold font-poppins">Stray Map</h1>
                    <p class="text-gray-600 dark:text-gray-400">Barangay Sacred Heart</p>
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
                    <q-btn 
                        class="primary-btn"
                        @click="openAddCameraDialog"
                        :disable="placingPinMode"
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
        <div v-if="showFilters" class="filter-panel mx-6 mb-4">
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
        <div v-if="placingPinMode" class="placement-alert mx-6 mb-4">
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
        
        <!-- Detection Monitor Status -->
        <div class="detection-monitor-status mx-6 mb-4">
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
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mx-6 mb-4">
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
        <Map ref="mapRef" />
        
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
</style>