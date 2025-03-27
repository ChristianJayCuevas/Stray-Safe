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
    totalSightings: 87,
    dogSightings: 52,
    catSightings: 35,
    activeCCTVs: 12
});

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

// Detection monitoring variables
const previousDetections = ref({});
const detectionMonitorInterval = ref(null);
const isMonitoring = ref(false);

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
                    videoSrc: [stream.hls_url.replace('http://', 'https://')]
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
            videoSrc: ['https://straysafe.me/hls/main-camera.m3u8']
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
    placingPinMode.value = true;
    showCameraDialog.value = false;
    
    // Display clear instructions to the user
    alert('Click on the map to place the camera pin. You can click the Cancel button to exit placement mode.');
    
    // Enable pin placement mode in the map component
    if (mapRef.value) {
        try {
            mapRef.value.enablePinPlacementMode((coordinates) => {
                console.log('User clicked map at coordinates:', coordinates);
                // When user clicks on map, add the camera pin with the selected camera
                addCameraPin(coordinates, cameraInfo)
                    .then(response => {
                        if (response && response.success === false) {
                            console.error('Pin was added visually but failed to save to server:', response.error);
                            alert('Pin was placed on map but could not be saved to the server. The pin will be visible until you refresh the page.');
                        } else {
                            console.log('Camera pin added successfully:', response);
                            alert('Camera pin placed successfully!');
                        }
                        // Reset placement mode regardless of success/failure
                        placingPinMode.value = false;
                    })
                    .catch(error => {
                        console.error('Error adding camera pin:', error);
                        alert('Failed to place camera pin. Please try again.');
                        // Don't reset placement mode on error to allow user to try again
                        // placingPin.value = false;
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
        
        // Forward the addCameraPin call to the map component
        const result = await mapRef.value.addCameraPin(coordinates, cameraInfo);
        
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

// Check for new detections by comparing current with previous counts
async function checkForNewDetections(currentCounters) {
  // Fetch camera streams data to get locations
  let streams = [];
  try {
    const streamsResponse = await axios.get('https://straysafe.me/api2/streams');
    streams = streamsResponse.data?.streams || [];
    console.log('Received streams for location lookup:', streams);
  } catch (error) {
    console.error('Failed to fetch streams for location lookup:', error);
    return;
  }
  
  // Create a map of camera IDs to their locations
  const streamLocations = {};
  streams.forEach(stream => {
    streamLocations[stream.id] = {
      name: stream.name || 'Unnamed Camera',
      location: stream.location || 'Unknown Location',
      coordinates: null // Will be filled in based on existing pins
    };
  });
  
  // Get existing camera pin locations from the map
  if (mapRef.value) {
    const cameraPins = await mapRef.value.getCameraPinLocations();
    console.log('Current camera pin locations:', cameraPins);
    
    // Match stream IDs with camera pin locations
    cameraPins.forEach(pin => {
      if (pin.id && streamLocations[pin.id]) {
        streamLocations[pin.id].coordinates = pin.coordinates;
      }
    });
  }
  
  // Iterate through cameras in current counters
  for (const cameraId in currentCounters) {
    if (!previousDetections.value[cameraId]) {
      // This is a new camera, treat all detections as new
      previousDetections.value[cameraId] = { cat: 0, dog: 0 };
      
      // First time seeing this camera - create pins for all existing detections
      const initialDetections = currentCounters[cameraId];
      
      // Create cat pins for the initial count
      if (initialDetections.cat > 0) {
        console.log(`Adding ${initialDetections.cat} initial cat pins for camera ${cameraId}`);
        // Create pins one by one to ensure proper distribution
        for (let i = 0; i < initialDetections.cat; i++) {
          await createAnimalDetectionPin(cameraId, 'cat', 1, streamLocations[cameraId], i);
        }
      }
      
      // Create dog pins for the initial count
      if (initialDetections.dog > 0) {
        console.log(`Adding ${initialDetections.dog} initial dog pins for camera ${cameraId}`);
        // Create pins one by one to ensure proper distribution
        for (let i = 0; i < initialDetections.dog; i++) {
          await createAnimalDetectionPin(cameraId, 'dog', 1, streamLocations[cameraId], i);
        }
      }
      
      // Set the previous detections to match current, as we've created pins for all
      previousDetections.value[cameraId] = { ...initialDetections };
      continue; // Skip to next camera, as we've handled this one
    }
    
    const current = currentCounters[cameraId];
    const previous = previousDetections.value[cameraId];
    
    // Check for new cat detections
    if (current.cat > previous.cat) {
      const newCats = current.cat - previous.cat;
      console.log(`Detected ${newCats} new cat(s) on camera ${cameraId}`);
      
      // Create a pin for each new cat, with different positions
      for (let i = 0; i < newCats; i++) {
        await createAnimalDetectionPin(cameraId, 'cat', 1, streamLocations[cameraId], i);
      }
    }
    
    // Check for new dog detections
    if (current.dog > previous.dog) {
      const newDogs = current.dog - previous.dog;
      console.log(`Detected ${newDogs} new dog(s) on camera ${cameraId}`);
      
      // Create a pin for each new dog, with different positions
      for (let i = 0; i < newDogs; i++) {
        await createAnimalDetectionPin(cameraId, 'dog', 1, streamLocations[cameraId], i);
      }
    }
  }
}

// Create an animal detection pin near a camera
async function createAnimalDetectionPin(cameraId, animalType, count, locationInfo, index = 0) {
  try {
    console.log('Creating animal detection pin for camera:', cameraId, 'Animal type:', animalType, 'Location info:', locationInfo);
    
    // Extract or create coordinates
    let coordinates = null;
    
    // Check if locationInfo exists
    if (!locationInfo) {
      console.warn(`Invalid location info for camera ${cameraId}`);
      return;
    }
    
    // Extract coordinates from different possible formats
    if (locationInfo.coordinates) {
      if (typeof locationInfo.coordinates === 'object') {
        // Object format with lat/lng properties
        if ('lat' in locationInfo.coordinates && 'lng' in locationInfo.coordinates) {
          coordinates = {
            lat: locationInfo.coordinates.lat,
            lng: locationInfo.coordinates.lng
          };
        } 
        // Array format [lng, lat]
        else if (Array.isArray(locationInfo.coordinates) && locationInfo.coordinates.length >= 2) {
          coordinates = {
            lat: locationInfo.coordinates[1],
            lng: locationInfo.coordinates[0]
          };
        }
      }
    }
    
    // Check if we got valid coordinates
    if (!coordinates) {
      console.warn(`No valid coordinates for camera ${cameraId}`, locationInfo);
      // Use a default location if we don't have coordinates (near Quezon City)
      coordinates = {
        lat: 14.631141 + (Math.random() * 0.01 - 0.005), // Add some randomness
        lng: 121.039295 + (Math.random() * 0.01 - 0.005)
      };
      console.log(`Using default coordinates for camera ${cameraId}:`, coordinates);
    }
    
    // Calculate position using a circle distribution around the camera
    const baseRadius = 0.0003; // ~30 meters base radius
    const pinCount = index || 0; // Use index to distribute pins evenly
    
    // Calculate angle based on pin index (distribute around a circle)
    const angle = (pinCount * 45) % 360; // 45 degrees between pins, wrapping at 360
    const radian = angle * (Math.PI / 180);
    
    // Use trigonometry to place the pin at the specified angle and distance
    const offsetLat = baseRadius * Math.sin(radian);
    const offsetLng = baseRadius * Math.cos(radian);
    
    // Add some randomness to the exact position (10% variance)
    const jitterFactor = 0.1;
    const jitterLat = baseRadius * jitterFactor * (Math.random() * 2 - 1);
    const jitterLng = baseRadius * jitterFactor * (Math.random() * 2 - 1);
    
    // Final position
    const animalPosition = {
      lat: coordinates.lat + offsetLat + jitterLat,
      lng: coordinates.lng + offsetLng + jitterLng
    };
    
    // Create timestamp for detection (now)
    const timestamp = new Date().toISOString();
    
    // Camera name for description
    const cameraName = locationInfo.name || 'Unknown Camera';
    
    // Create animal pin payload
    const pinData = {
      lat: animalPosition.lat,
      lng: animalPosition.lng,
      animal_type: animalType,
      description: `${count} ${animalType}(s) detected by ${cameraName}`,
      image_url: null, // Could be filled in with a snapshot if available
      detection_timestamp: timestamp,
      is_automated: true,
      is_camera: false,
      status: 'active',
      camera_id: cameraId
    };
    
    // Add the pin to the map
    if (mapRef.value) {
      console.log(`Adding ${animalType} detection pin at angle ${angle}°:`, pinData);
      const result = await mapRef.value.addAnimalPin(pinData);
      console.log('Animal detection pin added result:', result);
      return result;
    }
  } catch (error) {
    console.error('Failed to create animal detection pin:', error);
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
  
  // Initial fetch to establish baseline and create initial pins
  try {
    const initialCounters = await fetchDetectionCounters();
    console.log('Initial detection counters:', initialCounters);
    
    // Initialize empty previous detections (to force pin creation for all existing detections)
    previousDetections.value = {}; 
    
    // Check for initial detections and create pins accordingly
    await checkForNewDetections(initialCounters);
    
    // After creating initial pins, update the previous detections for accurate future comparisons
    previousDetections.value = JSON.parse(JSON.stringify(initialCounters));
    console.log('Established detection baseline:', previousDetections.value);
  } catch (error) {
    console.error('Failed to establish detection baseline:', error);
  }
  
  // Set up the interval to check for new detections every 5 seconds (more frequent checks)
  detectionMonitorInterval.value = setInterval(async () => {
    try {
      const currentCounters = await fetchDetectionCounters();
      console.log('Current detection counters:', currentCounters);
      
      // Check for new detections by comparing with previous values
      await checkForNewDetections(currentCounters);
      
      // Update previous detections for next comparison
      previousDetections.value = JSON.parse(JSON.stringify(currentCounters));
    } catch (error) {
      console.error('Error monitoring detections:', error);
    }
  }, 5000); // Check every 5 seconds
}

// Fetch the current detection counters from the API
async function fetchDetectionCounters() {
  try {
    const response = await axios.get('https://straysafe.me/api2/counters');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch detection counters:', error);
    throw error;
  }
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

// Start and stop monitoring on component mount/unmount
onMounted(() => {
  // Start the detection monitor
  monitorDetections();
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