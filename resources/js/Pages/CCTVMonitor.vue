<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const cctvs = ref([
    {
        name: 'Dog Demonstration Video',
        videoSrc: ['https://100.89.19.38:5000/video'],
        snapshots: []
    },
    {
        name: 'Cat Demonstration Video',
        videoSrc: ['https://100.89.19.38:5001/video'],
        snapshots: []
    },
]);

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

async function openDialog(cctv) {
    selectedCCTV.value = cctv;
    dialogVisible.value = true;

    // Fetch the latest snapshots and statuses for the selected CCTV
    try {
        const response = await axios.get(`http://127.0.0.1:8000/api/snapshots`, {
            params: {
                cctvName: cctv.name
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


// Fetch the recent snapshots when the component is mounted
onMounted(fetchRecentSnapshots);

function closeDialog() {
    dialogVisible.value = false;
    selectedCCTV.value = null;
}
</script>

<template> 
    <AuthenticatedLayout>
        <q-layout>
            <q-page-container>
                <div class="text-container-normal">
                    <p class="header">Barangay Sacred Heart</p>
                </div>
                <q-page class="q-pa-md">
                    <div class="q-gutter-md row justify-center">
                        <q-card v-for="(cctv, index) in cctvs" :key="index" class="cctv-card" @click="openDialog(cctv)">
                            <div class="title-container">
                                <p class="title">Recording</p>
                            </div>
                            <q-card-section>
                                <img :src="cctv.videoSrc[0]"
                                     @error="() => { if (cctv.videoSrc.length > 1) $event.target.src = cctv.videoSrc[1]; }"
                                     autoplay loop class="video-feed"></img>
                            </q-card-section>

                            <q-card-section>
                                <q-item>
                                    <q-item-section>
                                        <q-item-label class="sub-title">{{ cctv.name }}</q-item-label>
                                    </q-item-section>
                                </q-item>
                            </q-card-section>
                        </q-card>
                    </div>
                </q-page>
            </q-page-container>

            <!-- Mock Notification Sender -->
            <q-page-container>
                <div class="text-container-normal">
                    <p class="header">Send Mock Notification</p>
                </div>
                <q-page class="q-pa-md">
                    <q-form @submit.prevent="sendMockNotification">
                        <q-input v-model="notificationTitle" label="Notification Title" outlined dense />
                        <q-input v-model="notificationBody" label="Notification Body" outlined dense />
                        <q-btn label="Send Notification" color="primary" @click="sendMockNotification" />
                    </q-form>
                    <p class="q-mt-md">{{ notificationResponse }}</p>
                </q-page>
            </q-page-container>

            <q-page-container>
                <div class="text-container-normal">
                    <p class="header">Barangay Sacred Heart - Recent Snapshots</p>
                </div>
                <q-page class="q-pa-md">
                    <div v-if="loading" class="text-center q-mt-md">
                        <q-spinner-dots color="primary" size="lg" />
                        <p>Loading recent snapshots...</p>
                    </div>
                    <div v-else>
                        <q-table
                            :rows="snapshots"
                            :columns="columns"
                            row-key="timestamp"
                            class="q-pa-md"
                            flat
                            bordered
                            separator="horizontal"
                        >
                            <template v-slot:body-cell-imageUrl="props">
                                <img :src="props.row.imageUrl" alt="Snapshot" style="width: 100px; height: auto;" />
                            </template>
                        </q-table>
                    </div>
                </q-page>
            </q-page-container>
        </q-layout>
    </AuthenticatedLayout>
    <q-dialog v-model="dialogVisible" backdrop-filter="blur(4px) saturate(150%)">
        <q-card class="cctv-dialog">
            <div class="cctv-dialog-container" style="background: black;" @click.stop>
                <img v-if="selectedCCTV" :src="selectedCCTV.videoSrc[0]"
                     @error="() => { if (selectedCCTV.videoSrc.length > 1) $event.target.src = selectedCCTV.videoSrc[1]; }"
                     autoplay loop class="cctv-video"></img>
            </div>

            <div class="snapshot-details" style="width: 50%; padding: 20px;">
                <div v-if="selectedCCTV">
                    <p class="sub-title">{{ selectedCCTV.name }} - Snapshots</p>

                    <div v-for="(dogSnapshots, dogIndex) in groupedSnapshots" :key="dogIndex">
                        <q-expansion-item :label="'Dog ' + (dogIndex + 1)" expand-separator dense>
                            <div v-for="(snapshot, index) in dogSnapshots" :key="index" class="snapshot-item">
                                <img :src="snapshot.src" alt="Snapshot" class="snapshot-image"
                                     style="width: 100%; object-fit: contain;" />
                                <div class="snapshot-details">
                                    <p><strong>Time:</strong> {{ snapshot.time }}</p>
                                    <p><strong>Status:</strong> {{ snapshot.classification }}</p>
                                </div>
                            </div>
                        </q-expansion-item>
                    </div>
                </div>
            </div>
        </q-card>
    </q-dialog>
</template>

<style src="../../css/cctvmonitor.css" lang="css"></style>
