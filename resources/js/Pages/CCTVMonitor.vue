<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';

// Theme toggle
const isDarkTheme = ref(true);

function toggleTheme() {
    isDarkTheme.value = !isDarkTheme.value;
    // Save theme preference to localStorage
    localStorage.setItem('cctv-theme', isDarkTheme.value ? 'dark' : 'light');
}

// Sample CCTV data - this would be fetched from an API in a real implementation
const cctvs = ref([
    {
        id: 1,
        name: 'Dog Demonstration Video',
        location: 'Main Street',
        status: 'Online',
        videoSrc: ['https://127.0.0.1:5000/video'],
        snapshots: []
    },
    {
        id: 2,
        name: 'Cat Demonstration Video',
        location: 'Park Avenue',
        status: 'Online',
        videoSrc: ['https://100.89.19.38:5001/video'],
        snapshots: []
    },
    {
        id: 3,
        name: 'Camera 3',
        location: 'City Center',
        status: 'Offline',
        videoSrc: [''],
        snapshots: []
    },
    {
        id: 4,
        name: 'Camera 4',
        location: 'Riverside',
        status: 'Online',
        videoSrc: ['https://127.0.0.1:5000/video'],
        snapshots: []
    },
]);

// Pagination settings
const pagination = ref({
    page: 1,
    rowsPerPage: 4,
    totalPages: computed(() => Math.ceil(cctvs.value.length / pagination.value.rowsPerPage))
});

// Filtered CCTVs based on pagination
const paginatedCCTVs = computed(() => {
    const start = (pagination.value.page - 1) * pagination.value.rowsPerPage;
    const end = start + pagination.value.rowsPerPage;
    return cctvs.value.slice(start, end);
});

// System stats
const systemStats = ref({
    totalCameras: cctvs.value.length,
    onlineCameras: computed(() => cctvs.value.filter(cam => cam.status === 'Online').length),
    detections: 12,
    lastUpdate: new Date().toLocaleString()
});

const models = ref([
    {
        name: 'Real-Time Detection Transformer (RT-DETR)',
    },
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

async function openDialog(cctv) {
    selectedCCTV.value = cctv;
    dialogVisible.value = true;

    // Fetch the latest snapshots and statuses for the selected CCTV
    try {
        const response = await axios.get(`http://127.0.0.1:8000/api/snapshots`, {
            params: {
                cctvName: cctv.name
            },
            headers: {
                Authorization: 'Bearer StraySafeTeam3'
            }
        });

        if (response.data && response.data.snapshots) {
            selectedCCTV.value.snapshots = response.data.snapshots.map(snapshot => ({
                src: snapshot.image_url,
                time: snapshot.timestamp,
                classification: snapshot.stray_status
            }));
        }
    } catch (error) {
        console.error("Failed to fetch snapshots:", error);
        selectedCCTV.value.snapshots = [];
    }
}

const snapshots = ref([]);
const loading = ref(true);

async function fetchRecentSnapshots() {
    loading.value = true;
    try {
        const response = await axios.get('http://127.0.0.1:8000/api/snapshots/recent');
        if (response.data && response.data.snapshots) {
            snapshots.value = response.data.snapshots.map(snapshot => ({
                imageUrl: snapshot.image_url,
                timestamp: snapshot.timestamp,
                strayStatus: snapshot.stray_status,
                location: snapshot.location,
            }));
        }
    } catch (error) {
        console.error("Failed to fetch recent snapshots:", error);
        snapshots.value = [];
    } finally {
        loading.value = false;
    }
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

// Load saved theme preference
onMounted(() => {
    fetchRecentSnapshots();
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('cctv-theme');
    if (savedTheme) {
        isDarkTheme.value = savedTheme === 'dark';
    }
});

function closeDialog() {
    dialogVisible.value = false;
    selectedCCTV.value = null;
}
</script>

<template>
    <AuthenticatedLayout>
        <div class="cctv-dashboard" :class="{ 'light-theme': !isDarkTheme }">
            <!-- Header with system stats -->
            <div class="dashboard-header">
                <h1>CCTV Surveillance System</h1>
                <div class="header-controls">
                    <button class="theme-toggle" @click="toggleTheme">
                        <i class="fas" :class="isDarkTheme ? 'fa-sun' : 'fa-moon'"></i>
                        {{ isDarkTheme ? 'Light Mode' : 'Dark Mode' }}
                    </button>
                    <div class="system-time">{{ new Date().toLocaleString() }}</div>
                </div>
            </div>
            
            <!-- System stats cards -->
            <div class="stats-container">
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
                    <div class="stat-icon online">
                        <i class="fas fa-wifi"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ systemStats.onlineCameras }}</div>
                        <div class="stat-label">Online Cameras</div>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon alert">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ systemStats.detections }}</div>
                        <div class="stat-label">Detections Today</div>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ systemStats.lastUpdate }}</div>
                        <div class="stat-label">Last Update</div>
                    </div>
                </div>
            </div>
            
            <!-- Tabs for different views -->
            <div class="cctv-tabs">
                <div 
                    class="tab" 
                    :class="{ active: activeTab === 'live' }"
                    @click="activeTab = 'live'"
                >
                    Live Feeds
                </div>
                <div 
                    class="tab" 
                    :class="{ active: activeTab === 'snapshots' }"
                    @click="activeTab = 'snapshots'"
                >
                    Recent Snapshots
                </div>
            </div>
            
            <!-- Live feeds tab content -->
            <div v-if="activeTab === 'live'" class="tab-content">
                <div class="cctv-grid">
                    <div v-for="(cctv, index) in paginatedCCTVs" :key="cctv.id" class="cctv-card" @click="openDialog(cctv)">
                        <div class="cctv-header">
                            <span class="cctv-name">{{ cctv.name }}</span>
                            <span class="cctv-location">{{ cctv.location }}</span>
                            <span class="cctv-status" :class="cctv.status.toLowerCase()">
                                {{ cctv.status }}
                            </span>
                        </div>
                        <div class="cctv-feed">
                            <img 
                                v-if="cctv.status === 'Online'"
                                :src="cctv.videoSrc[0]"
                                @error="() => { if (cctv.videoSrc.length > 1) $event.target.src = cctv.videoSrc[1]; }"
                                autoplay loop class="video-feed"
                            />
                            <div v-else class="offline-feed">
                                <i class="fas fa-video-slash"></i>
                                <span>Camera Offline</span>
                            </div>
                            <div class="feed-overlay">
                                <div class="feed-timestamp">{{ new Date().toLocaleTimeString() }}</div>
                                <div v-if="cctv.status === 'Online'" class="live-indicator">LIVE</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Pagination controls -->
                <div class="pagination-controls">
                    <button 
                        class="pagination-btn" 
                        :disabled="pagination.page === 1"
                        @click="changePage(pagination.page - 1)"
                    >
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="pagination-info">
                        Page {{ pagination.page }} of {{ pagination.totalPages }}
                    </span>
                    <button 
                        class="pagination-btn" 
                        :disabled="pagination.page === pagination.totalPages"
                        @click="changePage(pagination.page + 1)"
                    >
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
            
            <!-- Snapshots tab content -->
            <div v-if="activeTab === 'snapshots'" class="tab-content">
                <div v-if="loading" class="loading-container">
                    <q-spinner-dots color="primary" size="lg" />
                    <p>Loading recent snapshots...</p>
                </div>
                <div v-else class="snapshots-container">
                    <div v-for="(snapshot, index) in snapshots" :key="index" class="snapshot-card">
                        <img :src="snapshot.imageUrl" alt="Snapshot" class="snapshot-image" />
                        <div class="snapshot-info">
                            <div class="snapshot-time">{{ snapshot.timestamp }}</div>
                            <div class="snapshot-status" :class="snapshot.strayStatus.toLowerCase().replace(' ', '-')">
                                {{ snapshot.strayStatus }}
                            </div>
                            <div class="snapshot-location">{{ snapshot.location }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </AuthenticatedLayout>
    
    <!-- CCTV Detail Dialog -->
    <q-dialog v-model="dialogVisible" backdrop-filter="blur(4px) saturate(150%)">
        <q-card class="cctv-dialog" :class="{ 'light-theme': !isDarkTheme }">
            <div class="dialog-header">
                <h2 v-if="selectedCCTV">{{ selectedCCTV.name }}</h2>
                <button class="close-btn" @click="closeDialog">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="dialog-content">
                <div class="cctv-dialog-container">
                    <img 
                        v-if="selectedCCTV && selectedCCTV.status === 'Online'" 
                        :src="selectedCCTV.videoSrc[0]"
                        @error="() => { if (selectedCCTV.videoSrc.length > 1) $event.target.src = selectedCCTV.videoSrc[1]; }"
                        autoplay loop class="cctv-video"
                    />
                    <div v-else class="offline-feed large">
                        <i class="fas fa-video-slash"></i>
                        <span>Camera Offline</span>
                    </div>
                    
                    <div class="feed-overlay">
                        <div class="feed-timestamp">{{ new Date().toLocaleTimeString() }}</div>
                        <div v-if="selectedCCTV && selectedCCTV.status === 'Online'" class="live-indicator">LIVE</div>
                    </div>
                </div>
                
                <div class="snapshot-details">
                    <h3 v-if="selectedCCTV">Recent Detections</h3>
                    
                    <div v-if="selectedCCTV && selectedCCTV.snapshots.length > 0">
                        <div v-for="(snapshot, index) in selectedCCTV.snapshots" :key="index" class="snapshot-item">
                            <img :src="snapshot.src" alt="Snapshot" class="snapshot-image" />
                            <div class="snapshot-info">
                                <div><strong>Time:</strong> {{ snapshot.time }}</div>
                                <div><strong>Status:</strong> {{ snapshot.classification }}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div v-else class="no-snapshots">
                        <i class="fas fa-image"></i>
                        <span>No recent detections</span>
                    </div>
                </div>
            </div>
        </q-card>
    </q-dialog>
</template>

<style src="../../css/cctvmonitor.css" lang="css"></style>
