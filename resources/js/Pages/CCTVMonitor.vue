<script setup>
import { ref, onMounted, inject, computed, watch, nextTick, onUnmounted, provide } from 'vue';
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

// Dialog state
const dialogVisible = ref(false);
const selectedCCTV = ref(null);
const useAIStream = ref(false);
const modalStreamKey = ref(0); // Key to force StreamPlayer refresh in modal

// Stream synchronization
const activeStreamInstances = ref({}); // Store active stream instances by ID
const activeHlsInstances = ref({}); // Store active HLS instances by ID

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
const FLASK_SERVER_URL = import.meta.env.VITE_FLASK_SERVER_URL || 'http://localhost:5000';

// Server URLs - use localhost
const SERVER_URLS = [
    'http://localhost:5000'
];

// Function to get the best server URL
const getBestServerUrl = async () => {
    const serverUrl = 'http://localhost:5000';
    try {
        const response = await axios.get(`${serverUrl}/health`, {
            timeout: 5000
        });
        if (response.status === 200) {
            return serverUrl;
        }
    } catch (error) {
        console.error('Error connecting to server:', error);
    }
    
    // Return the server URL even if health check fails
    return serverUrl;
};

// Store the active server URL
const activeServerUrl = ref(FLASK_SERVER_URL);

// Check if HLS.js is available
const hlsAvailable = ref(Hls.isSupported());

// Provide the active stream instances to child components
provide('activeStreamInstances', activeStreamInstances);
provide('activeHlsInstances', activeHlsInstances);
provide('activeServerUrl', activeServerUrl);

// Sync local theme with global theme on mount and when global theme changes
onMounted(async () => {
    console.log('Component mounted');
    if (!hlsAvailable.value) {
        console.warn('HLS.js is not available - video playback may be limited');
    }
    
    // Find the best server URL
    activeServerUrl.value = await getBestServerUrl();
    console.log('Active server URL:', activeServerUrl.value);
    
    fetchCCTVStreams();
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

// Function to fetch CCTV streams from the API
async function fetchCCTVStreams() {
    loading.value = true;
    streamError.value = false;
    
    try {
        activeServerUrl.value = await getBestServerUrl();
        
        // Use direct URL for straysafe.me
        const directHlsUrl = 'https://straysafe.me/api/hls/main-camera/playlist.m3u8';
        
        // Try to get streams from API first
        let useDirectHls = false;
        
        try {
            const response = await axios.get(`${activeServerUrl.value}/streams`, {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                timeout: 5000 // Shorter timeout to fall back faster
            });
            
            if (response.data?.streams?.length) {
                cctvs.value = response.data.streams.map((stream, index) => {
                    // Get the best HLS URL from the stream data
                    // Prefer the Nginx HLS URL
                    const hlsUrl = stream.hls_url || stream.flask_hls_url || `http://localhost:5000/hls/${stream.rtmp_key || stream.id}/playlist.m3u8`;
                    
                    // If this is the main camera, use the direct URL that works
                    const finalUrl = (stream.id === 'main-camera') ? directHlsUrl : hlsUrl;
                    
                    console.log(`Stream ${stream.id}: Using HLS URL ${finalUrl}`);
                    
                    return {
                        id: stream.id || (index + 1).toString(),
                        name: stream.name || `Camera ${index + 1}`,
                        location: stream.location || `Location ${index + 1}`,
                        status: stream.status === 'active' ? 'Online' : 'Offline',
                        videoSrc: [finalUrl],
                        originalSrc: stream.url,
                        streamInfo: stream,
                        isHls: true,
                        rtmpKey: stream.rtmp_key
                    };
                });
                
                systemStats.value = {
                    totalCameras: cctvs.value.length,
                    onlineCameras: cctvs.value.filter(cam => cam.status === 'Online').length,
                    detectionsToday: Math.floor(Math.random() * 30),
                    storageUsed: '1.2 TB'
                };
            } else {
                useDirectHls = true;
            }
        } catch (error) {
            console.error("Error fetching streams from API:", error);
            useDirectHls = true;
        }
        
        // If API failed or returned no streams, use direct HLS URL
        if (useDirectHls) {
            console.log("Using direct HLS URL:", directHlsUrl);
            cctvs.value = [
                {
                    id: 'main-camera',
                    name: 'Main Camera',
                    location: 'Main Gate',
                    status: 'Online',
                    videoSrc: [directHlsUrl],
                    originalSrc: 'rtsp://localhost:8554/cam1',
                    isHls: true
                }
            ];
            
            systemStats.value = {
                totalCameras: 1,
                onlineCameras: 1,
                detectionsToday: 5,
                storageUsed: '1.2 TB'
            };
        }
    } catch (error) {
        console.error("Error in fetchCCTVStreams:", error);
        useSampleData();
        streamError.value = true;
    } finally {
        loading.value = false;
    }
}

// Function to use sample data when API is unavailable
function useSampleData() {
    // Use the direct straysafe.me URL 
    const sampleHlsUrl = 'https://straysafe.me/api/hls/main-camera/playlist.m3u8';
    
    cctvs.value = [
        {
            id: 'main-camera',
            name: 'Main Camera',
            location: 'Main Gate',
            status: 'Online',
            videoSrc: [sampleHlsUrl],
            originalSrc: 'rtsp://localhost:8554/cam1',
            isHls: true
        }
    ];
    
    systemStats.value = {
        totalCameras: 1,
        onlineCameras: 1,
        detectionsToday: 5,
        storageUsed: '1.2 TB'
    };
}

// Function to open the dialog for a specific CCTV
function openDialog(cctv) {
    selectedCCTV.value = { ...cctv };
    useAIStream.value = false;
    dialogVisible.value = true;
    modalStreamKey.value++;
}

// Function to close the dialog
function closeDialog() {
    dialogVisible.value = false;
    // Keep the selectedCCTV to maintain stream state
    // It will be cleaned up when switching to a different camera
}

// Toggle between AI and regular stream view
function toggleAIView() {
    useAIStream.value = !useAIStream.value;
    modalStreamKey.value++; // Force StreamPlayer to reinitialize when toggling
}

// Stream event handlers
function onStreamReady(id) {
    console.log(`Stream ${id} is ready`);
    // Update the CCTV status if needed
    const cctv = cctvs.value.find(c => c.id === id);
    if (cctv) {
        cctv.status = 'Online';
    }
}

function onStreamError(id, error) {
    console.error(`Stream ${id} error:`, error);
    // Update the CCTV status if needed
    const cctv = cctvs.value.find(c => c.id === id);
    if (cctv) {
        cctv.streamError = error;
    }
}

// Stream event handlers for modal
function onModalStreamReady() {
    console.log('Modal stream is ready');
}

function onModalStreamError(error) {
    console.error('Modal stream error:', error);
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

function changePage(newPage) {
    if (newPage > 0 && newPage <= pagination.value.totalPages) {
        pagination.value.page = newPage;
    }
}

function openStreamInBrowser() {
    // Direct URL for the HLS stream
    const directHlsUrl = 'https://straysafe.me/api/hls/main-camera/playlist.m3u8';
    
    // If we have any cameras, open the first one's HLS URL
    if (cctvs.value.length > 0) {
        window.open(cctvs.value[0].videoSrc[0], '_blank');
    } else {
        // Fallback to the direct URL
        window.open(directHlsUrl, '_blank');
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
                <p class="mb-2">Unable to connect to the stream server at <strong>{{ activeServerUrl.value }}</strong>.</p>
                <p class="mb-2">Using direct HTTPS URL instead: <strong>https://straysafe.me/api/hls/main-camera/playlist.m3u8</strong></p>
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
                            :stream-id="cctv.id"
                            :autoplay="true"
                            :muted="true"
                            :register-instance="true"
                            @stream-ready="onStreamReady(cctv.id)"
                            @stream-error="onStreamError(cctv.id, $event)"
                            @register-instance="registerStreamInstance"
                        />
                        <div v-else class="offline-feed">
                            <i class="fas fa-video-slash"></i>
                            <p>Camera Offline</p>
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
            <q-card-section class="dialog-header">
                <div class="flex justify-between items-center">
                    <h2 class="dialog-title">{{ selectedCCTV ? selectedCCTV.name : 'Camera Feed' }}</h2>
                    <q-btn flat round icon="close" @click="closeDialog" />
                </div>
            </q-card-section>
            
            <q-card-section class="dialog-content">
                <div class="dialog-video-container">
                    <StreamPlayer 
                        v-if="selectedCCTV && selectedCCTV.status === 'Online'"
                        :key="modalStreamKey"
                        :stream-url="selectedCCTV ? selectedCCTV.videoSrc[0] : ''"
                        :stream-id="selectedCCTV ? selectedCCTV.id : ''"
                        :autoplay="true"
                        :muted="true"
                        :use-existing-instance="true"
                        @stream-ready="onModalStreamReady"
                        @stream-error="onModalStreamError"
                    />
                    <div v-else-if="selectedCCTV && selectedCCTV.status === 'Offline'" class="offline-feed">
                        <i class="fas fa-video-slash"></i>
                        <p>Camera Offline</p>
                    </div>
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
                        <div v-if="selectedCCTV && selectedCCTV.streamInfo" class="detail-item">
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
                    <q-btn v-if="selectedCCTV && selectedCCTV.originalSrc" class="secondary-btn ml-2" icon="switch_video" label="Toggle AI View" @click="toggleAIView" />
                </div>
            </q-card-section>
        </q-card>
    </q-dialog>
</template>
