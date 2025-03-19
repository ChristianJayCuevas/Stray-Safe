<script setup>
import { ref, onMounted, inject, computed, watch, nextTick, onUnmounted } from 'vue';
import { Head } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import StreamPlayer from '@/Components/StreamPlayer.vue';
import '../../css/cctvmonitor.css';
import axios from 'axios';
import Hls from 'hls.js'; // Import HLS.js library

// Get the global dark mode state from the AuthenticatedLayout
const globalIsDarkMode = inject('isDarkMode', ref(false));

// Use global dark mode directly instead of maintaining a separate state
const isDarkTheme = computed(() => globalIsDarkMode.value);

// Watch for changes to the global dark mode state
watch(globalIsDarkMode, (newValue) => {
    console.log('Dark mode changed:', newValue);
    // The isDarkTheme computed property will automatically update
});

// CCTV data
const cctvs = ref([]);
const loading = ref(true);
const streamError = ref(false);

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://20.195.42.135:5000'; // VPS server IP and port
console.log('Using API base URL:', API_BASE_URL);

// Check if HLS.js is available
const hlsAvailable = ref(Hls.isSupported());

// Sync local theme with global theme on mount and when global theme changes
onMounted(() => {
    console.log('Component mounted');
    if (!hlsAvailable.value) {
        console.warn('HLS.js is not available - video playback may be limited');
    }
    fetchCCTVStreams();
    fetchRecentSnapshots();
});

// Clean up when component is unmounted
onUnmounted(() => {
    console.log('Component unmounted');
});

// Function to fetch CCTV streams from the API
async function fetchCCTVStreams() {
    loading.value = true;
    streamError.value = false;
    
    try {
        console.log('Fetching CCTV streams from API...');
        const response = await axios.get(`${API_BASE_URL}/api/streams`, {
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            timeout: 10000 // 10 second timeout
        });
        
        console.log('API response:', response.data);
        
        if (response.data && Array.isArray(response.data)) {
            // Transform API data to match our CCTV data structure
            cctvs.value = response.data.map((stream, index) => {
                return {
                    id: index + 1,
                    name: stream.name,
                    location: `Camera ${index + 1}`,
                    status: stream.status === 'active' ? 'Online' : 'Offline',
                    videoSrc: [stream.urls.ai_processed.hls], // Use AI processed HLS stream
                    originalSrc: stream.urls.original.hls,    // Store original stream URL
                    streamInfo: stream
                };
            });
            
            // Update system stats
            systemStats.value = {
                totalCameras: cctvs.value.length,
                onlineCameras: cctvs.value.filter(cam => cam.status === 'Online').length,
                detectionsToday: Math.floor(Math.random() * 30), // This would come from the API in a real implementation
                storageUsed: '1.2 TB' // This would come from the API in a real implementation
            };
        } else {
            console.warn('No streams found in API response or invalid format, using direct m3u8 URL');
            // If no streams are available, use sample data with direct m3u8 URL
            useSampleData();
            streamError.value = true;
        }
    } catch (error) {
        console.error("Failed to fetch CCTV streams:", error);
        console.log("Using direct m3u8 URL instead");
        useSampleData();
        streamError.value = true;
    } finally {
        loading.value = false;
    }
}

// Function to use sample data when API is unavailable
function useSampleData() {
    console.log('Using sample CCTV data');
    
    // Create sample data with the proxied stream URL
    const proxiedStreamUrl = '/stream/ai_cam1/index.m3u8';
    
    cctvs.value = [
        {
            id: 1,
            name: 'CCTV 1',
            location: 'Main Entrance',
            status: 'Online',
            videoSrc: [proxiedStreamUrl],
            originalSrc: proxiedStreamUrl,
            lastDetection: new Date().toLocaleString(),
            snapshots: [
                { url: 'https://via.placeholder.com/300x200?text=Dog+Detection', timestamp: '2023-10-15 14:30:45', label: 'Stray Dog' },
            ]
        },
        {
            id: 2,
            name: 'CCTV 2',
            location: 'Back Alley',
            status: 'Online',
            videoSrc: [proxiedStreamUrl],
            originalSrc: proxiedStreamUrl,
            lastDetection: new Date().toLocaleString(),
            snapshots: []
        },
        {
            id: 3,
            name: 'CCTV 3',
            location: 'Side Street',
            status: 'Offline',
            videoSrc: [],
            originalSrc: '',
            lastDetection: 'N/A',
            snapshots: []
        },
        {
            id: 4,
            name: 'CCTV 4',
            location: 'Park Entrance',
            status: 'Online',
            videoSrc: [proxiedStreamUrl],
            originalSrc: proxiedStreamUrl,
            lastDetection: new Date().toLocaleString(),
            snapshots: [
                { url: 'https://via.placeholder.com/300x200?text=Dog+Detection', timestamp: '2023-10-14 09:45:12', label: 'Stray Dog' }
            ]
        }
    ];
    
    // Calculate total pages
    totalPages.value = Math.ceil(cctvs.value.length / pagination.value.itemsPerPage);
    
    // Update system stats with sample data
    systemStats.value = {
        totalCameras: cctvs.value.length,
        onlineCameras: cctvs.value.filter(cam => cam.status === 'Online').length,
        detectionsToday: 8,
        storageUsed: '1.2 TB'
    };
}

// Pagination settings
const pagination = ref({
    page: 1,
    rowsPerPage: 4,
    totalPages: 1
});

// Compute total pages whenever cctvs changes
watch(cctvs, () => {
    pagination.value.totalPages = Math.ceil(cctvs.value.length / pagination.value.rowsPerPage);
});

// Watch for pagination changes to reinitialize video players
watch(() => pagination.value.page, () => {
    nextTick(() => {
        // No need to manually initialize video players anymore as the StreamPlayer component handles it
    });
});

// Filtered CCTVs based on pagination
const paginatedCCTVs = computed(() => {
    const start = (pagination.value.page - 1) * pagination.value.rowsPerPage;
    const end = start + pagination.value.rowsPerPage;
    return cctvs.value.slice(start, end);
});

// System stats
const systemStats = ref({
    totalCameras: 0,
    onlineCameras: 0,
    detectionsToday: 0,
    storageUsed: '0 TB'
});

const models = ref([
    {
        name: 'Real-Time Detection Transformer (RT-DETR)',
    },
]);

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

const groupedSnapshots = computed(() => {
    if (!selectedCCTV.value) return [];
    const snapshots = selectedCCTV.value.snapshots;
    const groupSize = 2;
    return snapshots.reduce((result, snapshot, index) => {
        const groupIndex = Math.floor(index / groupSize);
        if (!result[groupIndex]) result[groupIndex] = [];
        result[groupIndex].push(snapshot);
        return result;
    }, []);
});

const dialogVisible = ref(false);
const selectedCCTV = ref(null);
const activeTab = ref('live');
const useAIStream = ref(true);

function openDialog(cctv) {
    selectedCCTV.value = cctv;
    dialogVisible.value = true;
    useAIStream.value = true;
    // No need to manually initialize HLS anymore as the StreamPlayer component handles it
}

async function fetchRecentSnapshots() {
    try {
        // Try to fetch detection events from the API
        const response = await axios.get(`${API_BASE_URL}/api/detection-events`);
        
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
    }
}

// References to active HLS instances
const hlsInstances = ref({});

// Function to setup HLS stream for a video element
function setupHlsStream(videoElementId, streamUrl, context = 'grid') {
    // This function is no longer needed as we're using the StreamPlayer component
    console.log(`Setup HLS stream function is deprecated. Using StreamPlayer component instead.`);
}

// Function to initialize HLS video player
function initHlsPlayer(videoElement, streamUrl) {
    // This function is no longer needed as we're using the StreamPlayer component
    console.log(`Init HLS player function is deprecated. Using StreamPlayer component instead.`);
}

function toggleAIView() {
    useAIStream.value = !useAIStream.value;
    console.log(`Switched to ${useAIStream.value ? 'AI' : 'original'} stream`);
    // The StreamPlayer component will automatically update when the stream-url prop changes
}

// Notification sending component state
const notificationTitle = ref('');
const notificationBody = ref('');
const notificationResponse = ref('');

async function sendMockNotification() {
    try {
        const response = await axios.post(
            'https://straysafe.me/api/send-notification',
            {
                title: notificationTitle.value,
                body: notificationBody.value,
            },
            {
                headers: {
                    Authorization: `Bearer StraySafeTeam3`, // Replace with your valid token
                },
            }
        );

        notificationResponse.value = `Notification sent successfully: ${response.data.message}`;
        notificationTitle.value = '';
        notificationBody.value = '';
    } catch (error) {
        console.error('Failed to send notification:', error);
        notificationResponse.value = 'Failed to send notification. Check console for details.';
    }
}

// Function to change pagination page
function changePage(newPage) {
    if (newPage > 0 && newPage <= pagination.value.totalPages) {
        pagination.value.page = newPage;
    }
}

function closeDialog() {
    // No need to clean up HLS instances anymore as the StreamPlayer component handles it
    dialogVisible.value = false;
    selectedCCTV.value = null;
}

// Function to open the stream in a new browser tab
function openStreamInBrowser() {
    window.open('http://20.195.42.135:8888/ai_cam1/index.m3u8', '_blank');
}

function onStreamReady(id) {
    console.log(`Stream ready for CCTV ${id}`);
}

function onStreamError(id, error) {
    console.error(`Stream error for CCTV ${id}:`, error);
}

function onModalStreamReady() {
    console.log('Modal stream ready');
}

function onModalStreamError(error) {
    console.error('Modal stream error:', error);
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
                        <q-btn class="secondary-btn" icon="refresh" label="Refresh" @click="fetchCCTVStreams" />
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
                <h2 class="text-2xl font-bold">CCTV Cameras</h2>
                <div class="header-actions">
                    <div class="current-time">
                        <i class="fas fa-clock mr-2"></i>
                        {{ new Date().toLocaleTimeString() }}
                    </div>
                    <q-btn class="secondary-btn" icon="refresh" label="Refresh" @click="fetchCCTVStreams" />
                </div>
            </div>

            <!-- Loading indicator -->
            <div v-if="loading" class="loading-container">
                <q-spinner color="primary" size="3em" />
                <p class="mt-2">Loading CCTV streams...</p>
            </div>

            <!-- Error message -->
            <div v-else-if="streamError" class="error-container">
                <i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-2"></i>
                <p class="mb-2">Unable to connect to the stream server at <strong>{{ API_BASE_URL }}</strong>.</p>
                <p class="mb-2">Using direct m3u8 URL instead: <strong>http://20.195.42.135:8888/ai_cam1/index.m3u8</strong></p>
                <p class="mb-4">Note: This stream requires authentication (user: user, password: Straysafeteam3)</p>
                <div class="flex space-x-2">
                    <q-btn class="secondary-btn" icon="refresh" label="Try Again" @click="fetchCCTVStreams" />
                    <q-btn class="primary-btn" icon="open_in_new" label="Test Stream in Browser" @click="openStreamInBrowser" />
                </div>
            </div>

            <div v-else class="cctv-grid">
                <div v-for="(cctv, index) in paginatedCCTVs" :key="cctv.id" class="cctv-card" @click="openDialog(cctv)">
                    <div class="cctv-feed">
                        <StreamPlayer 
                            v-if="cctv.status === 'Online'" 
                            :stream-url="cctv.videoSrc[0]"
                            @stream-ready="onStreamReady(cctv.id)"
                            @stream-error="onStreamError(cctv.id, $event)"
                        />
                        <div v-else class="offline-message">
                            <i class="fas fa-video-slash mr-2"></i> Camera Offline
                        </div>
                    </div>
                    <div class="cctv-info">
                        <div class="cctv-title">{{ cctv.name }}</div>
                        <div class="cctv-location">{{ cctv.location }}</div>
                        <div class="cctv-status" :class="cctv.status === 'Online' ? 'status-online' : 'status-offline'">
                            <i :class="cctv.status === 'Online' ? 'fas fa-circle' : 'fas fa-circle-xmark'" class="mr-1"></i>
                            {{ cctv.status }}
                        </div>
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
            <div class="dialog-header">
                <h2 class="text-xl font-bold">{{ selectedCCTV?.name }}</h2>
                <q-btn flat round icon="close" @click="closeDialog" class="close-btn" />
            </div>
            <div class="dialog-content">
                <div class="cctv-feed-large">
                    <StreamPlayer 
                        v-if="selectedCCTV?.status === 'Online'" 
                        :stream-url="useAIStream ? selectedCCTV?.videoSrc[0] : selectedCCTV?.originalSrc"
                        @stream-ready="onModalStreamReady"
                        @stream-error="onModalStreamError"
                    />
                    <div v-else class="offline-message">
                        <i class="fas fa-video-slash mr-2"></i> Camera Offline
                    </div>
                    <div class="feed-overlay">
                        <div class="feed-timestamp">{{ new Date().toLocaleString() }}</div>
                        <div class="feed-location">{{ selectedCCTV?.location }}</div>
                    </div>
                </div>
                <div class="cctv-info-large">
                    <div class="camera-details">
                        <div class="text-lg font-bold mb-2">Camera Details</div>
                        <div class="detail-item">
                            <span class="detail-label">Name:</span>
                            <span class="detail-value">{{ selectedCCTV?.name }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Location:</span>
                            <span class="detail-value">{{ selectedCCTV?.location }}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value" :class="selectedCCTV?.status === 'Online' ? 'text-green-500' : 'text-red-500'">
                                <i :class="selectedCCTV?.status === 'Online' ? 'fas fa-circle' : 'fas fa-circle-xmark'" class="mr-1"></i>
                                {{ selectedCCTV?.status }}
                            </span>
                        </div>
                        <div v-if="selectedCCTV?.streamInfo" class="detail-item">
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
                    <q-btn v-if="selectedCCTV?.originalSrc" class="secondary-btn ml-2" icon="switch_video" label="Toggle AI View" @click="toggleAIView" />
                </div>
            </div>
        </q-card>
    </q-dialog>
</template>
