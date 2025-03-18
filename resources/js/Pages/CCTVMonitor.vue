<script setup>
import { ref, onMounted, inject, computed, watch } from 'vue';
import { Head } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import '../../css/cctvmonitor.css';
import axios from 'axios';

// Get the global dark mode state from the AuthenticatedLayout
const globalIsDarkMode = inject('isDarkMode', ref(false));

// Use global dark mode directly instead of maintaining a separate state
const isDarkTheme = computed(() => globalIsDarkMode.value);

// Watch for changes to the global dark mode state
watch(globalIsDarkMode, (newValue) => {
    console.log('Dark mode changed:', newValue);
    // The isDarkTheme computed property will automatically update
});

// Sync local theme with global theme on mount and when global theme changes
onMounted(() => {
    fetchRecentSnapshots();
});

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
    onlineCameras: cctvs.value.filter(cam => cam.status === 'Online').length,
    detectionsToday: 12,
    storageUsed: '1.2 TB'
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

function openDialog(cctv) {
    selectedCCTV.value = cctv;
    dialogVisible.value = true;
}

const loading = ref(true);

async function fetchRecentSnapshots() {
    loading.value = true;
    try {
        // In a real implementation, this would be an API call
        // const response = await axios.get('http://127.0.0.1:8000/api/snapshots/recent');
        // recentSnapshots.value = response.data.snapshots;
        loading.value = false;
    } catch (error) {
        console.error("Failed to fetch recent snapshots:", error);
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

function closeDialog() {
    dialogVisible.value = false;
    selectedCCTV.value = null;
}
</script>

<template>
    <AuthenticatedLayout>
        <div class="cctv-monitor-container px-6 py-4" :class="{ 'dark-mode': isDarkTheme }">
            <!-- Header Section -->
            <div class="page-header">
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
                        <q-btn color="primary" icon="refresh" label="Refresh" @click="fetchRecentSnapshots" />
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

            <!-- CCTV Feeds -->
            <div class="cctv-grid">
                <div v-for="(cctv, index) in paginatedCCTVs" :key="cctv.id" class="cctv-card" @click="openDialog(cctv)">
                    <div class="cctv-feed">
                        <video v-if="cctv.status === 'Online'" :src="cctv.videoSrc[0]" autoplay loop muted></video>
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
                <q-btn flat round icon="close" @click="closeDialog" />
            </div>
            <div class="dialog-content">
                <div class="cctv-feed-large">
                    <video v-if="selectedCCTV?.status === 'Online'" :src="selectedCCTV?.videoSrc[0]" autoplay loop muted></video>
                    <div v-else class="offline-message">
                        <i class="fas fa-video-slash mr-2"></i> Camera Offline
                    </div>
                </div>
                <div class="cctv-info-large mt-4">
                    <div class="text-lg font-bold">{{ selectedCCTV?.name }}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">{{ selectedCCTV?.location }}</div>
                    <div class="mt-2" :class="selectedCCTV?.status === 'Online' ? 'text-green-500' : 'text-red-500'">
                        <i :class="selectedCCTV?.status === 'Online' ? 'fas fa-circle' : 'fas fa-circle-xmark'" class="mr-1"></i>
                        {{ selectedCCTV?.status }}
                    </div>
                </div>
            </div>
        </q-card>
    </q-dialog>
</template>
