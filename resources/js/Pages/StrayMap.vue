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
const perceptionRange = ref(30); // Default perception range in meters

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
    // First try to use rtmp_key if available, otherwise fall back to id
    const streamId = stream.rtmp_key || stream.id;
    
    streamLocations[streamId] = {
      id: stream.id,
      rtmp_key: stream.rtmp_key || stream.id,
      original_id: stream.id,
      name: stream.name || 'Unnamed Camera',
      location: stream.location || 'Unknown Location',
      coordinates: null, // Will be filled in based on existing pins
      perceptionRange: 30, // Default perception range
      conicalView: false, // Default to non-directional
      viewingDirection: 0,
      viewingAngle: 360
    };
    
    // If we create an entry with rtmp_key, also create a fallback entry with ID
    // This ensures we can match cameras even if the identification method varies
    if (stream.rtmp_key && stream.rtmp_key !== stream.id) {
      streamLocations[stream.id] = { ...streamLocations[streamId] };
    }
  });
  
  console.log('Created stream locations map:', streamLocations);
  
  // Get existing camera pin locations from the map
  let cameraPins = [];
  if (mapRef.value) {
    try {
      cameraPins = await mapRef.value.getCameraPinLocations();
      console.log('Current camera pin locations:', cameraPins);
      
      // Match stream IDs with camera pin locations
      cameraPins.forEach(pin => {
        // Try matching with both rtmp_key and id
        const pinId = pin.rtmp_key || pin.id;
        
        // Check for direct match with stream ID
        if (pinId && streamLocations[pinId]) {
          console.log(`Found direct match for camera pin ${pinId}`);
          streamLocations[pinId].coordinates = pin.coordinates;
          streamLocations[pinId].perceptionRange = pin.perceptionRange;
          streamLocations[pinId].conicalView = pin.conicalView;
          streamLocations[pinId].viewingDirection = pin.viewingDirection;
          streamLocations[pinId].viewingAngle = pin.viewingAngle;
        } 
        // Also match with all IDs that might contain the pin ID
        else {
          for (const streamId in streamLocations) {
            // If streamId contains pinId or pinId contains streamId, it's likely a match
            if (streamId.includes(pinId) || (pinId && pinId.includes(streamId))) {
              console.log(`Found partial match between camera pin ${pinId} and stream ${streamId}`);
              streamLocations[streamId].coordinates = pin.coordinates;
              streamLocations[streamId].perceptionRange = pin.perceptionRange;
              streamLocations[streamId].conicalView = pin.conicalView;
              streamLocations[streamId].viewingDirection = pin.viewingDirection;
              streamLocations[streamId].viewingAngle = pin.viewingAngle;
            }
          }
        }
      });
    } catch (error) {
      console.error('Error getting camera pin locations:', error);
    }
  }
  
  // Iterate through cameras in current counters
  for (const cameraId in currentCounters) {
    // Try to find matching stream location for this camera ID
    let locationInfo = null;
    
    // First try direct match
    if (streamLocations[cameraId]) {
      locationInfo = streamLocations[cameraId];
      console.log(`Found direct match for counter ID ${cameraId}`);
    } else {
      // Try partial matching
      for (const streamId in streamLocations) {
        if (streamId.includes(cameraId) || cameraId.includes(streamId)) {
          locationInfo = streamLocations[streamId];
          console.log(`Found partial match for counter ID ${cameraId} with stream ${streamId}`);
          break;
        }
      }
    }
    
    // Skip cameras that don't have pins placed on the map
    if (!locationInfo || !locationInfo.coordinates) {
      console.log(`Skipping camera ${cameraId} as it doesn't have a pin on the map`);
      continue;
    }
    
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
          await createAnimalDetectionPin(cameraId, 'cat', 1, locationInfo, i);
        }
      }
      
      // Create dog pins for the initial count
      if (initialDetections.dog > 0) {
        console.log(`Adding ${initialDetections.dog} initial dog pins for camera ${cameraId}`);
        // Create pins one by one to ensure proper distribution
        for (let i = 0; i < initialDetections.dog; i++) {
          await createAnimalDetectionPin(cameraId, 'dog', 1, locationInfo, i);
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
        await createAnimalDetectionPin(cameraId, 'cat', 1, locationInfo, i);
      }
    }
    
    // Check for new dog detections
    if (current.dog > previous.dog) {
      const newDogs = current.dog - previous.dog;
      console.log(`Detected ${newDogs} new dog(s) on camera ${cameraId}`);
      
      // Create a pin for each new dog, with different positions
      for (let i = 0; i < newDogs; i++) {
        await createAnimalDetectionPin(cameraId, 'dog', 1, locationInfo, i);
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
            lat: parseFloat(locationInfo.coordinates.lat),
            lng: parseFloat(locationInfo.coordinates.lng)
          };
        } 
        // Array format [lng, lat]
        else if (Array.isArray(locationInfo.coordinates) && locationInfo.coordinates.length >= 2) {
          coordinates = {
            lat: parseFloat(locationInfo.coordinates[1]),
            lng: parseFloat(locationInfo.coordinates[0])
          };
        }
      }
    }
    
    // Check if we got valid coordinates
    if (!coordinates || isNaN(coordinates.lat) || isNaN(coordinates.lng)) {
      console.warn(`No valid coordinates for camera ${cameraId}`, locationInfo);
      // Use a default location if we don't have coordinates (near Quezon City)
      coordinates = {
        lat: 14.631141 + (Math.random() * 0.01 - 0.005), // Add some randomness
        lng: 121.039295 + (Math.random() * 0.01 - 0.005)
      };
      console.log(`Using default coordinates for camera ${cameraId}:`, coordinates);
    }
    
    // IMPROVED: Different radius range for different animal types
    // Cats tend to stay closer to cameras, dogs might wander a bit further
    let minRadius, maxRadius;
    if (animalType === 'cat') {
      minRadius = 3 + (index % 3); // 3-5 meters for cats
      maxRadius = 8 + (index % 5); // 8-12 meters for cats
    } else { // dog
      minRadius = 5 + (index % 4); // 5-8 meters for dogs
      maxRadius = 12 + (index % 8); // 12-19 meters for dogs
    }
    
    // Generate a random radius between min and max (in meters)
    const radiusInMeters = minRadius + Math.random() * (maxRadius - minRadius);
    
    // Convert radius from meters to approximate degrees
    // 1 degree is about 111km at equator, so 1m is roughly 0.000009 degrees
    const radius = radiusInMeters * 0.000009;
    
    console.log(`Using radius of ${radiusInMeters.toFixed(1)}m for ${animalType} detection on camera ${cameraId}`);
    
    // Check if camera has directional information (conical view)
    let angle;
    const hasConicalView = locationInfo.conicalView === true || 
                           locationInfo.conical_view === true;
    
    const viewingDirection = parseFloat(locationInfo.viewingDirection || 
                                        locationInfo.viewing_direction || 0);
                                        
    const viewingAngle = parseFloat(locationInfo.viewingAngle || 
                                     locationInfo.viewing_angle || 360);
    
    if (hasConicalView && viewingAngle < 360) {
      console.log(`Camera ${cameraId} has conical view: direction=${viewingDirection}°, angle=${viewingAngle}°`);
      
      // 80% chance to be within viewing angle, 20% chance to be anywhere
      if (Math.random() < 0.8) {
        // Place the animal within the camera's viewing cone
        // Divide the viewing angle into segments based on how many animals we're placing
        const halfAngle = viewingAngle / 2;
        const segmentSize = Math.min(30, viewingAngle / 2);  // Max 30 degrees per segment
        
        // Calculate base position in the cone, with variation based on index
        const basePosition = (index % 3) - 1;  // -1, 0, or 1 to spread across the cone
        
        // Calculate a random angle within the camera's viewing direction ± half of viewing angle
        const minAngle = viewingDirection - halfAngle + (basePosition * segmentSize);
        const maxAngle = minAngle + segmentSize;
        
        // Get a random angle within this segment
        angle = minAngle + Math.random() * (maxAngle - minAngle);
        
        // Add small random variation to avoid perfect alignment
        angle += (Math.random() * 10) - 5;  // ±5 degrees random variation
        
        console.log(`Placing ${animalType} inside conical view at angle ${angle.toFixed(1)}° (direction=${viewingDirection}°±${halfAngle}°)`);
      } else {
        // Place randomly around the camera but outside the viewing direction
        // This simulates animals that might be behind or to the sides of the camera
        const outsideDirection = (viewingDirection + 180 + (Math.random() * 180 - 90)) % 360;
        angle = outsideDirection;
        console.log(`Placing ${animalType} outside conical view at angle ${angle.toFixed(1)}°`);
      }
    } else {
      // Standard 360-degree camera or no directional information
      // Use golden angle (137.5°) for more natural distribution
      const baseAngle = 137.5;
      angle = (index * baseAngle) % 360;
      
      // Add randomness to prevent animals from forming patterns
      angle += (Math.random() * 40) - 20;  // ±20 degrees random variation
      console.log(`Placing ${animalType} in 360° view at angle ${angle.toFixed(1)}°`);
    }
    
    // Convert to radians for Math functions
    const radian = angle * (Math.PI / 180);
    
    // Calculate the offset from the camera position
    const offsetLat = radius * Math.sin(radian);
    const offsetLng = radius * Math.cos(radian);
    
    // Add natural jitter to make it look more realistic
    const jitterFactor = 0.2;  // 20% jitter for natural look
    const jitterLat = radius * jitterFactor * (Math.random() * 2 - 1);
    const jitterLng = radius * jitterFactor * (Math.random() * 2 - 1);
    
    // Final position
    const animalPosition = {
      lat: coordinates.lat + offsetLat + jitterLat,
      lng: coordinates.lng + offsetLng + jitterLng
    };
    
    // Create timestamp for detection (now)
    const timestamp = new Date().toISOString();
    
    // Camera name for description
    const cameraName = locationInfo.name || 'Unknown Camera';
    
    // Create animal pin payload with all camera information
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
      camera_id: cameraId,
      rtmp_key: locationInfo.rtmp_key, // Include the rtmp_key for better matching
      original_id: locationInfo.original_id, // Include original ID for better matching
      perception_range: parseFloat(locationInfo.perceptionRange || 30) // Include the perception range in the pin data
    };
    
    // Add the pin to the map
    if (mapRef.value) {
      console.log(`Adding ${animalType} detection pin at angle ${angle.toFixed(1)}° and distance ${radiusInMeters.toFixed(1)}m:`, pinData);
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