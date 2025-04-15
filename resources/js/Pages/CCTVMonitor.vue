<script setup>
import { ref, onMounted, inject, computed, watch, onUnmounted, provide } from 'vue';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import StreamPlayer from '@/Components/StreamPlayer.vue';
import '../../css/cctvmonitor.css';
import axios from 'axios';
import Hls from 'hls.js';

// Get the global dark mode state from the AuthenticatedLayout
const globalIsDarkMode = inject('isDarkMode', ref(false));

// Use global dark mode directly
const isDarkTheme = computed(() => globalIsDarkMode.value);

// CCTV data and state
const cctvs = ref([]);
const loading = ref(true);
const streamError = ref(false);

// Dialog state
const dialogVisible = ref(false);
const selectedCCTV = ref(null);

// Define props for the component
const props = defineProps({
  initialCustomCCTVs: Array
});

// Create CCTV Card dialog
const createCardDialogVisible = ref(false);
const newCardName = ref('');
const newCardLocation = ref('');
const selectedStreamUrl = ref('');
const availableStreams = ref([]);
const customCards = ref(props.initialCustomCCTVs || []);

// Authentication state
const user = ref(null);
const isAuthenticated = ref(false);

// Function to check authentication status
const checkAuthStatus = async () => {
  try {
    const response = await axios.get('/auth/check');
    isAuthenticated.value = response.data.authenticated;
    if (response.data.authenticated) {
      user.value = response.data.user;
    }
  } catch (error) {
    console.error('Auth check failed:', error);
    isAuthenticated.value = false;
  }
};

// Function to open the create card dialog
function openCreateCardDialog() {
  newCardName.value = '';
  newCardLocation.value = '';
  selectedStreamUrl.value = '';
  createCardDialogVisible.value = true;
}

// Function to close the create card dialog
function closeCreateCardDialog() {
  createCardDialogVisible.value = false;
}

// Function to add a new custom CCTV card
async function addCustomCard() {
  if (!newCardName.value || !selectedStreamUrl.value) {
    alert('Please provide a name and select a stream URL');
    return;
  }

  // Find the selected stream details
  const selectedStream = availableStreams.value.find(stream => stream.hls_url === selectedStreamUrl.value);

  // Ensure stream URL uses https
  const secureStreamUrl = selectedStreamUrl.value ? selectedStreamUrl.value.replace('http://', 'https://') : '';

  try {
    // Save to the backend
    const response = await axios.post('/cctvs', {
      name: newCardName.value,
      location: newCardLocation.value || 'Custom Location',
      stream_url: secureStreamUrl,
      original_stream_id: selectedStream ? selectedStream.id : null
    });

    if (response.data.success) {
      // Add the card with the ID from the server
      const newCard = {
        id: response.data.cctv.id,
        name: newCardName.value,
        location: newCardLocation.value || 'Custom Location',
        status: 'Online',
        videoSrc: [secureStreamUrl],
        isHls: true,
        isCustom: true,
        originalStreamId: selectedStream ? selectedStream.id : null
      };

      // Add to custom cards
      customCards.value.push(newCard);

      // Close the dialog
      closeCreateCardDialog();

      console.log('Custom CCTV saved successfully:', response.data.cctv);
    } else {
      console.error('Failed to save custom CCTV:', response.data.message);
      alert('Failed to save custom CCTV: ' + response.data.message);
    }
  } catch (error) {
    console.error('Error saving custom CCTV:', error);
    alert('Error saving custom CCTV: ' + (error.response?.data?.message || error.message));
  }
}

// Stream synchronization
const activeStreamInstances = ref({});
const activeHlsInstances = ref({});

// Provide the active stream instances to child components
provide('activeStreamInstances', activeStreamInstances);
provide('activeHlsInstances', activeHlsInstances);

// Check if HLS.js is available
const hlsAvailable = ref(Hls.isSupported());

// Fetch streams from API
const fetchStreams = async () => {
  loading.value = true;
  streamError.value = false;

  try {
    const response = await axios.get('https://straysafe.me/api2/streams')

    // Log the raw response for debugging
    console.log('Stream API response:', response.data);

    // Safely extract the streams with validation
    let streams = [];
    if (response.data && Array.isArray(response.data.streams)) {
      streams = response.data.streams;
    } else if (Array.isArray(response.data)) {
      streams = response.data;
    } else {
      console.warn('Unexpected streams data format:', response.data);
      streams = [];
    }

    // Store available streams for selection with careful validation
    availableStreams.value = streams.map(stream => {
      // Ensure we have all required properties
      return {
        id: stream.id || `stream-${Math.random().toString(36).substr(2, 9)}`,
        name: stream.name || 'Unnamed Stream',
        location: stream.location || 'Unknown Location',
        hls_url: stream.hls_url ? stream.hls_url.replace('http://', 'https://') : ''
      };
    }).filter(stream => stream.hls_url); // Only keep streams with a valid URL

    console.log('Processed streams:', availableStreams.value);

    // Update system stats - only count custom cards
    systemStats.value = {
      totalCameras: customCards.value.length,
      onlineCameras: customCards.value.length, // All custom cards are considered online
      detectionsToday: Math.floor(Math.random() * 30),
      storageUsed: '1.2 GB'
    };
  } catch (error) {
    console.error('Failed to fetch streams:', error)
    streamError.value = true;
    useSampleData();
  } finally {
    loading.value = false
  }
}

// Function to use sample data when API is unavailable
function useSampleData() {
  // Add a sample custom CCTV card if none exist
  if (customCards.value.length === 0) {
    customCards.value = [{
      id: 'sample-camera',
      name: 'Sample Camera',
      location: 'Main Gate',
      status: 'Online',
      videoSrc: ['https://straysafe.me/hls/main-camera.m3u8'],
      isHls: true,
      isCustom: true
    }];
  }

  systemStats.value = {
    totalCameras: customCards.value.length,
    onlineCameras: customCards.value.length,
    detectionsToday: 5,
    storageUsed: '1.2 GB'
  };
}

// Initialize on component mount
onMounted(() => {
  console.log('Component mounted');
  if (!hlsAvailable.value) {
    console.warn('HLS.js is not available - video playback may be limited');
  }

  // Check authentication status
  checkAuthStatus();

  // Initialize with custom CCTVs from props
  if (props.initialCustomCCTVs && props.initialCustomCCTVs.length > 0) {
    customCards.value = props.initialCustomCCTVs.map(cctv => ({
      id: cctv.id,
      name: cctv.camera_name,
      location: cctv.location,
      status: cctv.status,
      // Ensure the URL uses https
      videoSrc: [cctv.stream_url ? cctv.stream_url.replace('http://', 'https://') : ''],
      isHls: true,
      isCustom: true,
      originalStreamId: cctv.original_stream_id
    }));
  }

  fetchStreams();
  fetchRecentSnapshots();
});

// Clean up when component is unmounted
onUnmounted(() => {
  console.log('Component unmounted');
  // Clean up all HLS instances
  Object.values(activeHlsInstances.value).forEach(hls => {
    if (hls) {
      hls.destroy();
    }
  });
  activeHlsInstances.value = {};
  activeStreamInstances.value = {};
});

// Function to open the dialog for a specific CCTV
function openDialog(cctv) {
  selectedCCTV.value = { ...cctv };
  dialogVisible.value = true;
}

// Function to close the dialog
function closeDialog() {
  dialogVisible.value = false;
}

// Register a stream instance
function registerStreamInstance(id, videoElement, hlsInstance) {
  console.log(`Registering stream instance for ${id}`);

  // If we already have an instance for this stream, clean it up first
  if (activeHlsInstances.value[id] && activeHlsInstances.value[id] !== hlsInstance) {
    console.log(`Cleaning up existing HLS instance for ${id}`);
    activeHlsInstances.value[id].destroy();
  }

  activeStreamInstances.value[id] = videoElement;
  if (hlsInstance) {
    activeHlsInstances.value[id] = hlsInstance;

    // Set up quality levels if available
    hlsInstance.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
      if (data.levels.length > 1) {
        // Start with the second highest quality for better performance
        hlsInstance.currentLevel = 1;
      }
    });

    // Monitor for stalls and automatically recover
    let lastTime = 0;
    let stallCount = 0;

    const checkStall = setInterval(() => {
      if (videoElement && !videoElement.paused) {
        if (videoElement.currentTime === lastTime) {
          stallCount++;
          if (stallCount > 5) { // If stalled for more than 5 seconds
            console.log(`Stream ${id} appears stalled, attempting recovery`);
            hlsInstance.recoverMediaError();
            stallCount = 0;
          }
        } else {
          stallCount = 0;
        }
        lastTime = videoElement.currentTime;
      }
    }, 1000);

    // Clean up interval when HLS instance is destroyed
    hlsInstance.on(Hls.Events.DESTROYING, () => {
      clearInterval(checkStall);
    });
  }
}

// Pagination settings
const pagination = ref({
  page: 1,
  rowsPerPage: 4,
  totalPages: 1
});

// Compute total pages whenever customCards change
watch(customCards, () => {
  const totalCameras = customCards.value.length;
  pagination.value.totalPages = Math.ceil(totalCameras / pagination.value.rowsPerPage);
});

// Filtered CCTVs based on pagination, including custom cards
const paginatedCCTVs = computed(() => {
  // Only use custom cards
  const allCameras = [...customCards.value];
  const start = (pagination.value.page - 1) * pagination.value.rowsPerPage;
  const end = start + pagination.value.rowsPerPage;
  return allCameras.slice(start, end);
});

// System stats
const systemStats = ref({
  totalCameras: 0,
  onlineCameras: 0,
  detectionsToday: 0,
  storageUsed: '0 TB'
});

// Recent detection snapshots - Remove mock data
const recentSnapshots = ref([]);

// Update the fetchRecentSnapshots function to match dashboard implementation
async function fetchRecentSnapshots() {
    try {
        loadingSnapshots.value = true;
        const response = await axios.get('https://straysafe.me/api2/detected');

        if (response.data && response.data.detected_animals) {
            recentSnapshots.value = response.data.detected_animals.map(animal => {
                // Convert the image URL from detected-img to debug-img
                const imageUrl = animal.image_url ?
                    animal.image_url.replace('detected-img', 'debug-img') :
                    'https://placehold.co/600x400/4f6642/FFFFFF/png?text=No+Image';

                return {
                    id: animal.id,
                    animalType: animal.animal_type,
                    location: `Camera ${animal.stream_id}`,
                    timestamp: new Date(animal.timestamp).toLocaleString(),
                    imageUrl: imageUrl,
                    classification: animal.classification || 'Unknown',
                    owner_id: animal.owner_id || null,
                    notification_sent: animal.notification_sent || false,
                    notification_status: animal.notification_status || null
                };
            });

            // Initial filtering after fetch
            filterSnapshots();
        }
    } catch (error) {
        console.error('Error fetching recent snapshots:', error);
        snapshotsError.value = 'Failed to fetch recent detections';
    } finally {
        loadingSnapshots.value = false;
    }
}

// Change pagination page
function changePage(newPage) {
  if (newPage > 0 && newPage <= pagination.value.totalPages) {
    pagination.value.page = newPage;
  }
}

// Open stream in browser (for testing)
function openStreamInBrowser() {
  window.open('https://straysafe.me/hls/main-camera.m3u8', '_blank');
}

// Function to remove a custom card
async function removeCustomCard(cardId) {
  try {
    // Delete from backend
    const response = await axios.delete(`/cctvs/${cardId}`);

    if (response.data.success) {
      // Remove from local list
      const index = customCards.value.findIndex(card => card.id === cardId);
      if (index !== -1) {
        customCards.value.splice(index, 1);

        // Update system stats
        systemStats.value.totalCameras = cctvs.value.length + customCards.value.length;
        systemStats.value.onlineCameras = cctvs.value.filter(cam => cam.status === 'Online').length + customCards.value.length;
      }

      console.log('Custom CCTV deleted successfully');
    } else {
      console.error('Failed to delete custom CCTV:', response.data.message);
      alert('Failed to delete custom CCTV: ' + response.data.message);
    }
  } catch (error) {
    console.error('Error deleting custom CCTV:', error);
    alert('Error deleting custom CCTV: ' + (error.response?.data?.message || error.message));
  }
}

// Snapshot notification state
const snapshotNotification = ref({
  show: false,
  image: '',
  time: '',
  camera: ''
});

// Function to handle snapshot
function handleSnapshot(snapshotData) {
  console.log('Snapshot received:', snapshotData);

  snapshotNotification.value = {
    show: true,
    image: snapshotData.dataUrl,
    time: new Date().toLocaleString(),
    camera: snapshotData.cameraName || 'Unknown Camera'
  };

  // Auto-hide the notification after 5 seconds
  setTimeout(() => {
    if (snapshotNotification.value.show) {
      snapshotNotification.value.show = false;
    }
  }, 5000);
}

// Function to close snapshot notification
function closeSnapshotNotification() {
  snapshotNotification.value.show = false;
}

// Recent Detections Section
const selectedAnimalType = ref('All');
const timeFilter = ref('24h');
const loadingSnapshots = ref(false);
const snapshotsError = ref(null);
const filteredSnapshots = ref([]);
const snapshotsPagination = ref({
  page: 1,
  rowsPerPage: 10,
  totalPages: 1
});

// Add this computed property after the other computed properties
const paginatedSnapshots = computed(() => {
  const start = (snapshotsPagination.value.page - 1) * snapshotsPagination.value.rowsPerPage;
  const end = start + snapshotsPagination.value.rowsPerPage;
  return filteredSnapshots.value.slice(start, end);
});

// Update the filterSnapshots function to properly handle pagination
function filterSnapshots() {
  loadingSnapshots.value = true;
  snapshotsError.value = null;

  try {
    const filtered = recentSnapshots.value.filter(snapshot => {
      // Animal type filter
      const typeMatch = selectedAnimalType.value === 'All' ||
                       snapshot.animalType === selectedAnimalType.value;

      // Time filter
      const snapshotDate = new Date(snapshot.timestamp);
      const now = new Date();
      let timeMatch = true;

      if (timeFilter.value === '24h') {
        timeMatch = (now - snapshotDate) <= 24 * 60 * 60 * 1000;
      } else if (timeFilter.value === '7d') {
        timeMatch = (now - snapshotDate) <= 7 * 24 * 60 * 60 * 1000;
      } else if (timeFilter.value === '30d') {
        timeMatch = (now - snapshotDate) <= 30 * 24 * 60 * 60 * 1000;
      }

      return typeMatch && timeMatch;
    });

    filteredSnapshots.value = filtered;
    snapshotsPagination.value.totalPages = Math.ceil(filtered.length / snapshotsPagination.value.rowsPerPage);
    snapshotsPagination.value.page = 1; // Reset to first page when filter changes
  } catch (error) {
    console.error('Error filtering snapshots:', error);
    snapshotsError.value = 'Error filtering snapshots';
  } finally {
    loadingSnapshots.value = false;
  }
}

// Add watchers for filter changes
watch([selectedAnimalType, timeFilter], () => {
  filterSnapshots();
});

// Function to format timestamp
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

// Function to get animal type class
function getAnimalTypeClass(animalType) {
  switch (animalType) {
    case 'Dog':
      return 'text-green-500';
    case 'Cat':
      return 'text-blue-500';
    case 'Other':
      return 'text-gray-500';
    default:
      return '';
  }
}

// Function to download snapshot
function downloadSnapshot(snapshot) {
  // Implementation of downloadSnapshot function
}

// Function to share snapshot
function shareSnapshot(snapshot) {
  // Implementation of shareSnapshot function
}

// Function to send notification to owner
/* Temporarily disabled
async function sendNotification(snapshot) {
  try {
    const response = await axios.post('/api/send-notification', {
      owner_id: snapshot.owner_id,
      animal_type: snapshot.animalType,
      location: snapshot.location,
      detection_id: snapshot.id,
      image_url: snapshot.imageUrl
    });

    if (response.data.success) {
      // Update the snapshot with notification status
      const index = recentSnapshots.value.findIndex(s => s.id === snapshot.id);
      if (index !== -1) {
        recentSnapshots.value[index] = {
          ...recentSnapshots.value[index],
          notification_sent: true,
          notification_status: 'pending'
        };
        // Re-run filtering to update the view
        filterSnapshots();
      }

      // Show success message
      alert('Notification sent to owner successfully');
    } else {
      throw new Error(response.data.message || 'Failed to send notification');
    }
  } catch (error) {
    console.error('Error sending notification:', error);
    alert('Failed to send notification: ' + (error.response?.data?.message || error.message));
  }
}
*/
</script>

<template>
  <AuthenticatedLayout>
    <div class="cctv-monitor-container px-6 py-4" :class="{ 'dark-mode': isDarkTheme }">
      <!-- Header Section -->
      <div class="page-header px-6">
        <div class="flex justify-between items-center">
          <div class="header-title">
            <h1 class="text-3xl font-bold font-poppins">CCTV Surveillance System</h1>
            <p class="text-gray-600 dark:text-gray-400">Barangay Sacred Heart</p>
          </div>

          <!-- CCTV Controls -->
          <div class="header-actions">
            <div class="system-time">
              <i class="fas fa-clock mr-2"></i>
              {{ new Date().toLocaleTimeString() }}
            </div>
            <q-btn class="secondary-btn" icon="refresh" label="Refresh" @click="fetchStreams" />
          </div>
        </div>
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid mx-6">
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-video"></i>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ systemStats.totalCameras }}</div>
            <div class="stat-label">Total Cameras</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-wifi"></i>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ systemStats.onlineCameras }}</div>
            <div class="stat-label">Online Cameras</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-paw"></i>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ systemStats.detectionsToday }}</div>
            <div class="stat-label">Detections Today</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <i class="fas fa-database"></i>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ systemStats.storageUsed }}</div>
            <div class="stat-label">Storage Used</div>
          </div>
        </div>
      </div>

      <!-- CCTV Grid -->
      <div class="page-header px-6 mb-6">
        <div class="flex justify-between items-center">
          <div class="current-time">
            <h2 class="text-2xl font-bold">CCTV Instances</h2>
          </div>
          <q-btn class="primary-btn" icon="add" label="Add Camera Card" @click="openCreateCardDialog" />
        </div>
      </div>

      <div v-if="loading" class="loading-container mx-6">
        <q-spinner color="primary" size="3em" />
        <p class="mt-2">Loading CCTV streams...</p>
      </div>

      <!-- Error message -->
      <div v-else-if="streamError" class="error-container mx-6">
        <i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-2"></i>
        <p class="mb-2">Unable to connect to the stream server.</p>
        <p class="mb-4">Using fallback camera configuration.</p>
        <div class="flex space-x-2">
          <q-btn class="secondary-btn" icon="refresh" label="Try Again" @click="fetchStreams" />
          <q-btn class="primary-btn" icon="open_in_new" label="Test Stream in Browser" @click="openStreamInBrowser" />
        </div>
      </div>

      <!-- Empty streams message -->
      <div v-else-if="availableStreams.length === 0 && customCards.length === 0" class="error-container mx-6">
        <i class="fas fa-video-slash text-yellow-500 text-3xl mb-2"></i>
        <p class="mb-2">No CCTV streams are currently available.</p>
        <p class="mb-4">You can add a custom CCTV card with your own stream URL.</p>
        <div class="flex space-x-2">
          <q-btn class="primary-btn" icon="add" label="Add Custom Camera" @click="openCreateCardDialog" />
          <q-btn class="secondary-btn" icon="refresh" label="Check Again" @click="fetchStreams" />
        </div>
      </div>

      <div v-else class="cctv-grid mx-6">
        <div v-for="(cctv, index) in paginatedCCTVs" :key="cctv.id" class="cctv-card" @click="openDialog(cctv)">
          <div class="live-indicator">
            <span class="pulse"></span>
            <span class="live-text">LIVE</span>
          </div>
          <div class="cctv-feed">
            <StreamPlayer
              :streamUrl="cctv.videoSrc[0]"
              @snapshot="handleSnapshot"
            />
          </div>
          <div class="cctv-info">
            <div class="cctv-title">{{ cctv.name }}</div>
            <div class="cctv-location">{{ cctv.location }}</div>
            <div class="cctv-status status-online">
              <i class="fas fa-circle mr-1"></i>
              Online
            </div>
            <q-btn class="delete-card-btn" icon="delete" flat dense @click.stop="removeCustomCard(cctv.id)">
              <q-tooltip>Remove Card</q-tooltip>
            </q-btn>
          </div>
        </div>
      </div>

      <!-- Pagination Controls -->
      <div class="pagination-container mx-6">
        <q-pagination
          v-model="pagination.page"
          :max="pagination.totalPages"
          direction-links
          boundary-links
          color="primary"
          active-color="primary"
        />
      </div>

      <!-- Snapshot notification -->
      <div v-if="snapshotNotification.show" class="snapshot-notification">
        <div class="snapshot-notification-content">
          <div class="snapshot-thumbnail">
            <img :src="snapshotNotification.image" alt="Snapshot" />
          </div>
          <div class="snapshot-info">
            <p class="snapshot-title">Snapshot Captured</p>
            <p class="snapshot-time">{{ snapshotNotification.time }}</p>
          </div>
          <button @click="closeSnapshotNotification" class="close-snapshot-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>

      <!-- Recent Detections Section -->
      <div class="page-header px-6 mb-6">
        <div class="flex justify-between items-center">
          <div class="current-time">
            <h2 class="text-2xl font-bold">Recent Detections</h2>
          </div>
          <div class="header-actions">
            <div class="filter-controls">
              <q-select
                v-model="selectedAnimalType"
                :options="['All', 'Dog', 'Cat', 'Other']"
                label="Filter by type"
                dense
                outlined
                class="mr-2"
                style="min-width: 150px"
              />
              <q-btn-group outline>
                <q-btn
                  :color="timeFilter === '24h' ? 'primary' : 'grey'"
                  label="24h"
                  @click="timeFilter = '24h'"
                />
                <q-btn
                  :color="timeFilter === '7d' ? 'primary' : 'grey'"
                  label="7d"
                  @click="timeFilter = '7d'"
                />
                <q-btn
                  :color="timeFilter === '30d' ? 'primary' : 'grey'"
                  label="30d"
                  @click="timeFilter = '30d'"
                />
              </q-btn-group>
            </div>
            <q-btn class="secondary-btn ml-4" icon="refresh" label="Refresh" @click="fetchRecentSnapshots" />
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loadingSnapshots" class="loading-container mx-6">
        <q-spinner color="primary" size="3em" />
        <p class="mt-2">Loading recent detections...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="snapshotsError" class="error-container mx-6">
        <i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-2"></i>
        <p class="mb-2">{{ snapshotsError }}</p>
        <q-btn class="secondary-btn" icon="refresh" label="Try Again" @click="fetchRecentSnapshots" />
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredSnapshots.length === 0" class="empty-container mx-6">
        <i class="fas fa-camera text-gray-400 text-3xl mb-2"></i>
        <p class="mb-2">No detections found for the selected filters.</p>
        <p class="text-sm text-gray-500">Try adjusting your filters or checking back later.</p>
      </div>

      <!-- Detection Grid -->
      <div v-else class="detection-grid mx-6">
        <div v-for="snapshot in paginatedSnapshots" :key="snapshot.id" class="detection-card">
          <div class="detection-image-container">
            <img :src="snapshot.imageUrl" class="detection-image" :alt="snapshot.animalType" />
            <div class="detection-badge" :class="getAnimalTypeClass(snapshot.animalType)">
              {{ snapshot.animalType }}
            </div>
          </div>
          <div class="detection-info">
            <div class="flex items-center justify-between mb-2">
              <div class="text-lg font-bold">{{ snapshot.animalType }}</div>
              <q-badge :color="snapshot.classification === 'stray' ? 'negative' : 'positive'">
                {{ snapshot.classification }}
              </q-badge>
            </div>
            <div class="text-sm mb-1">
              <i class="fas fa-map-marker-alt mr-1"></i>
              {{ snapshot.location }}
            </div>
            <!-- <div class="text-sm mb-1" v-if="snapshot.owner_id">
              <i class="fas fa-user mr-1"></i>
              Owner ID: {{ snapshot.owner_id }}
            </div> -->
            <div class="text-xs text-gray-500">
              <i class="fas fa-clock mr-1"></i>
              {{ formatTimestamp(snapshot.timestamp) }}
            </div>
            <div class="text-xs mt-2" v-if="snapshot.notification_sent">
              <q-badge :color="snapshot.notification_status === 'delivered' ? 'positive' : 'warning'" class="full-width">
                <i class="fas fa-bell mr-1"></i>
                {{ snapshot.notification_status === 'delivered' ? 'Notification Delivered' : 'Notification Pending' }}
              </q-badge>
            </div>
          </div>
          <div class="detection-actions">
            <q-btn flat round size="sm" icon="download" @click.stop="downloadSnapshot(snapshot)">
              <q-tooltip>Download Snapshot</q-tooltip>
            </q-btn>
            <q-btn flat round size="sm" icon="share" @click.stop="shareSnapshot(snapshot)">
              <q-tooltip>Share</q-tooltip>
            </q-btn>
            <!-- Temporarily disabled
            <q-btn
              v-if="snapshot.owner_id && !snapshot.notification_sent"
              flat
              round
              size="sm"
              icon="notifications"
              @click.stop="sendNotification(snapshot)"
            >
              <q-tooltip>Send Notification to Owner</q-tooltip>
            </q-btn>
            -->
          </div>
        </div>
      </div>

      <!-- Snapshots Pagination -->
      <div v-if="filteredSnapshots.length > snapshotsPagination.rowsPerPage" class="pagination-container mx-6">
        <q-pagination
          v-model="snapshotsPagination.page"
          :max="snapshotsPagination.totalPages"
          direction-links
          boundary-links
          color="primary"
          active-color="primary"
        />
      </div>
    </div>
  </AuthenticatedLayout>

  <!-- CCTV Detail Dialog -->
  <q-dialog v-model="dialogVisible" backdrop-filter="blur(4px) saturate(150%)">
    <q-card class="cctv-dialog-card">
      <q-card-section class="dialog-header">
        <div class="flex justify-between items-center">
          <h2 class="dialog-title">{{ selectedCCTV ? selectedCCTV.name : 'Camera Feed' }}</h2>
          <q-btn flat round icon="close" @click="closeDialog" />
        </div>
      </q-card-section>

      <q-card-section class="dialog-content">
        <div class="dialog-video-container">
          <StreamPlayer v-if="selectedCCTV" :streamUrl="selectedCCTV.videoSrc[0]" />
        </div>
        <div class="cctv-info-large">
          <div class="camera-details">
            <div class="text-lg font-bold mb-2">Camera Details</div>
            <div class="detail-item">
              <span class="detail-label">Name:</span>
              <span class="detail-value">{{ selectedCCTV ? selectedCCTV.name : '' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Location:</span>
              <span class="detail-value">{{ selectedCCTV ? selectedCCTV.location : '' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Status:</span>
              <span class="detail-value" :class="selectedCCTV ? (selectedCCTV.status === 'Online' ? 'text-green-500' : 'text-red-500') : ''">
                <i :class="selectedCCTV ? (selectedCCTV.status === 'Online' ? 'fas fa-circle' : 'fas fa-circle-xmark') : ''" class="mr-1"></i>
                {{ selectedCCTV ? selectedCCTV.status : '' }}
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Stream Type:</span>
              <span class="detail-value">HLS Stream</span>
            </div>
          </div>
          <div class="camera-stats">
            <div class="text-lg font-bold mb-2">Detection Statistics</div>
            <div class="stats-item">
              <span class="stats-label">Today's Detections:</span>
              <span class="stats-value">{{ Math.floor(Math.random() * 20) }}</span>
            </div>
            <div class="stats-item">
              <span class="stats-label">Dogs Detected:</span>
              <span class="stats-value">{{ Math.floor(Math.random() * 15) }}</span>
            </div>
            <div class="stats-item">
              <span class="stats-label">Cats Detected:</span>
              <span class="stats-value">{{ Math.floor(Math.random() * 10) }}</span>
            </div>
          </div>
        </div>
        <div class="dialog-actions mt-4">
          <q-btn class="secondary-btn" icon="notifications" label="Send Alert" />
          <q-btn class="primary-btn ml-2" icon="save" label="Save Snapshot" />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>

  <!-- Create CCTV Card Dialog -->
  <q-dialog v-model="createCardDialogVisible" backdrop-filter="blur(4px) saturate(150%)">
    <q-card class="create-card-dialog" :dark="isDarkTheme">
      <q-card-section class="dialog-header">
        <div class="flex justify-between items-center">
          <h2 class="dialog-title">Add Camera Card</h2>
          <q-btn flat round icon="close" @click="closeCreateCardDialog" />
        </div>
      </q-card-section>

      <q-card-section>
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2" :class="isDarkTheme ? 'text-gray-300' : 'text-gray-700'">Camera Name</label>
          <input
            v-model="newCardName"
            type="text"
            class="form-input w-full rounded-md p-2"
            :class="isDarkTheme ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'"
            placeholder="Enter camera name"
          />
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium mb-2" :class="isDarkTheme ? 'text-gray-300' : 'text-gray-700'">Location (Optional)</label>
          <input
            v-model="newCardLocation"
            type="text"
            class="form-input w-full rounded-md p-2"
            :class="isDarkTheme ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'"
            placeholder="Enter camera location"
          />
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium mb-2" :class="isDarkTheme ? 'text-gray-300' : 'text-gray-700'">Stream URL</label>
          <select
            v-model="selectedStreamUrl"
            class="form-select w-full rounded-md p-2"
            :class="isDarkTheme ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'"
          >
            <option value="" disabled>Select a stream</option>
            <option v-for="stream in availableStreams" :key="stream.id" :value="stream.hls_url">
              {{ stream.name || 'Unnamed Stream' }} ({{ stream.location || 'Unknown' }})
            </option>
          </select>
        </div>
      </q-card-section>

      <q-card-section class="dialog-actions" align="right">
        <q-btn flat :text-color="isDarkTheme ? 'white' : 'black'" label="Cancel" @click="closeCreateCardDialog" />
        <q-btn class="primary-btn" label="Add Card" @click="addCustomCard" />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<style scoped>
.detection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  padding: 1rem 0;
}

.detection-card {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}

.detection-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.detection-image-container {
  position: relative;
  width: 100%;
  padding-top: 75%; /* 4:3 aspect ratio */
  overflow: hidden;
}

.detection-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detection-badge {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 0.875rem;
}

.detection-info {
  padding: 1rem;
}

.detection-info > div {
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  color: #4b5563;
  font-size: 0.875rem;
}

.detection-info > div:last-child {
  margin-bottom: 0;
}

.detection-actions {
  display: flex;
  justify-content: flex-end;
  padding: 0.5rem;
  border-top: 1px solid #e5e7eb;
}

.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-actions {
  display: flex;
  align-items: center;
  margin-top: 1rem;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

@media (min-width: 640px) {
  .header-actions {
    margin-top: 0;
    justify-content: flex-end;
  }
}

.detection-info .q-badge {
  padding: 4px 8px;
}

.detection-info .full-width {
  width: 100%;
  justify-content: center;
  margin-top: 8px;
}

.detection-actions {
  display: flex;
  justify-content: flex-end;
  padding: 0.5rem;
  border-top: 1px solid #e5e7eb;
  gap: 0.5rem;
}
</style>
