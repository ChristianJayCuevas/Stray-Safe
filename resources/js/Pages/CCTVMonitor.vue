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
    const response = await axios.get('https://straysafe.me/api/streams')
    
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
      storageUsed: '1.2 TB'
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
      name: cctv.name,
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

// Recent detection snapshots
const recentSnapshots = ref([
  {
    imageUrl: 'https://via.placeholder.com/300x200?text=Stray+Dog',
    timestamp: '2023-06-15 14:30',
    animalType: 'Dog',
    location: 'Main Street'
  },
  {
    imageUrl: 'https://via.placeholder.com/300x200?text=Stray+Cat',
    timestamp: '2023-06-15 13:45',
    animalType: 'Cat',
    location: 'Park Avenue'
  },
  {
    imageUrl: 'https://via.placeholder.com/300x200?text=Stray+Dog',
    timestamp: '2023-06-15 12:20',
    animalType: 'Dog',
    location: 'Riverside'
  }
]);

// Fetch recent detection snapshots
async function fetchRecentSnapshots() {
  try {
    // Try to fetch detection events from the API
    const response = await axios.get('https://straysafe.me/api/detection-events');
    
    if (response.data && Array.isArray(response.data)) {
      recentSnapshots.value = response.data.map(event => {
        return {
          imageUrl: event.image_url || 'https://via.placeholder.com/300x200?text=Detection',
          timestamp: event.timestamp || new Date().toLocaleString(),
          animalType: event.animal_type || 'Unknown',
          location: event.location || 'Unknown'
        };
      });
    }
  } catch (error) {
    console.error("Failed to fetch recent snapshots:", error);
    // Keep the default snapshots
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
</script>

<template>
  <AuthenticatedLayout>
    <div class="cctv-monitor-container px-6 py-4" :class="{ 'dark-mode': isDarkTheme }">
      <!-- Header Section -->
      <div class="page-header">
        <div class="flex justify-between items-center">
          <div class="header-title">
            <h1 class="text-3xl font-bold">CCTV Surveillance System</h1>
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
      <div class="stats-grid">
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
      <div class="page-header mb-6">
        <h2 class="text-2xl font-bold">My Custom CCTV Instances</h2>
        <div class="header-actions">
          <div class="current-time">
            <i class="fas fa-clock mr-2"></i>
            {{ new Date().toLocaleTimeString() }}
          </div>
          <q-btn class="primary-btn mr-2" icon="add" label="Add Camera Card" @click="openCreateCardDialog" />
          <q-btn class="secondary-btn" icon="refresh" label="Refresh" @click="fetchStreams" />
        </div>
      </div>

      <div v-if="loading" class="loading-container">
        <q-spinner color="primary" size="3em" />
        <p class="mt-2">Loading CCTV streams...</p>
      </div>

      <!-- Error message -->
      <div v-else-if="streamError" class="error-container">
        <i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-2"></i>
        <p class="mb-2">Unable to connect to the stream server.</p>
        <p class="mb-4">Using fallback camera configuration.</p>
        <div class="flex space-x-2">
          <q-btn class="secondary-btn" icon="refresh" label="Try Again" @click="fetchStreams" />
          <q-btn class="primary-btn" icon="open_in_new" label="Test Stream in Browser" @click="openStreamInBrowser" />
        </div>
      </div>
      
      <!-- Empty streams message -->
      <div v-else-if="availableStreams.length === 0 && customCards.length === 0" class="error-container">
        <i class="fas fa-video-slash text-yellow-500 text-3xl mb-2"></i>
        <p class="mb-2">No CCTV streams are currently available.</p>
        <p class="mb-4">You can add a custom CCTV card with your own stream URL.</p>
        <div class="flex space-x-2">
          <q-btn class="primary-btn" icon="add" label="Add Custom Camera" @click="openCreateCardDialog" />
          <q-btn class="secondary-btn" icon="refresh" label="Check Again" @click="fetchStreams" />
        </div>
      </div>

      <div v-else class="cctv-grid">
        <div v-for="(cctv, index) in paginatedCCTVs" :key="cctv.id" class="cctv-card" @click="openDialog(cctv)">
          <div class="live-indicator">
            <span class="pulse"></span>
            <span class="live-text">LIVE</span>
          </div>
          <div class="cctv-feed">
            <StreamPlayer :streamUrl="cctv.videoSrc[0]" />
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
      <div class="flex justify-center mt-6 mb-6">
        <q-pagination
          v-model="pagination.page"
          :max="pagination.totalPages"
          direction-links
          boundary-links
          color="primary"
          active-color="primary"
        />
      </div>

      <!-- Recent Detections Section -->
      <div class="page-header mb-6">
        <h2 class="text-2xl font-bold">Recent Detections</h2>
      </div>

      <div class="detection-grid">
        <div v-for="(snapshot, index) in recentSnapshots" :key="index" class="detection-card">
          <img :src="snapshot.imageUrl" class="detection-image" alt="Detection" />
          <div class="detection-info">
            <div class="detection-type">{{ snapshot.animalType }}</div>
            <div class="detection-time">{{ snapshot.timestamp }}</div>
            <div class="detection-location">{{ snapshot.location }}</div>
          </div>
        </div>
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
    <q-card class="create-card-dialog">
      <q-card-section class="dialog-header">
        <div class="flex justify-between items-center">
          <h2 class="dialog-title">Add Camera Card</h2>
          <q-btn flat round icon="close" @click="closeCreateCardDialog" />
        </div>
      </q-card-section>
      
      <q-card-section>
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Camera Name</label>
          <input
            v-model="newCardName"
            type="text"
            class="form-input w-full rounded-md border border-gray-300 p-2"
            placeholder="Enter camera name"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Location (Optional)</label>
          <input
            v-model="newCardLocation"
            type="text"
            class="form-input w-full rounded-md border border-gray-300 p-2"
            placeholder="Enter camera location"
          />
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium mb-2">Stream URL</label>
          <select
            v-model="selectedStreamUrl"
            class="form-select w-full rounded-md border border-gray-300 p-2"
          >
            <option value="" disabled>Select a stream</option>
            <option v-for="stream in availableStreams" :key="stream.id" :value="stream.hls_url">
              {{ stream.name || 'Unnamed Stream' }} ({{ stream.location || 'Unknown' }})
            </option>
          </select>
        </div>
      </q-card-section>
      
      <q-card-section class="dialog-actions" align="right">
        <q-btn flat label="Cancel" @click="closeCreateCardDialog" />
        <q-btn class="primary-btn" label="Add Card" @click="addCustomCard" />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>
