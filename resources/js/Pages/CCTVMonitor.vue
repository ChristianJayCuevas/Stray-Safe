<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import CCTVView from '@/Components/CCTVView.vue';
import { ref, computed } from 'vue';
const cctvs = ref([
    { 
        name: 'Scout Rallos Street', 
        videoSrc: 'http://100.89.19.38:5000/video',
        snapshots: [
            { src: 'http://178.128.48.126/videos/snapshot1.png', time: '10:00 AM', classification: 'Stray' },
            { src: 'http://178.128.48.126/videos/snapshot2.png', time: '10:01 AM', classification: 'Stray' },
            { src: 'http://178.128.48.126/videos/snapshot3.png', time: '10:02 AM', classification: 'Stray' },
        ]
    },
    { 
        name: 'Scout Limbaga Street', 
        videoSrc: 'http://100.89.19.38:5000/video',
        snapshots: [
            { src: 'http://178.128.48.126/snapshots/leasheddog_09:00.jpg', time: '9:00 AM', classification: 'Leashed' },
            { src: 'http://178.128.48.126/snapshots/leasheddog_09:30.jpg', time: '9:30 AM', classification: 'Leashed' },
        ]
    },
]);

const models = ref([
    { 
        name: 'Real-Time Detection Transformer (RT-DETR)', 
    },
   
]);
const groupedSnapshots = computed(() => {
    if (!selectedCCTV.value) return [];
    // Group the snapshots in groups of 2 (or any other logic based on your data)
    const snapshots = selectedCCTV.value.snapshots;
    const groupSize = 2; // Adjust if you have different numbers of snapshots per dog
    return snapshots.reduce((result, snapshot, index) => {
        const groupIndex = Math.floor(index / groupSize);
        if (!result[groupIndex]) result[groupIndex] = [];
        result[groupIndex].push(snapshot);
        return result;
    }, []);
});
const dialogVisible = ref(false);
const selectedCCTV = ref(null);

function openDialog(cctv) {
    selectedCCTV.value = cctv;
    dialogVisible.value = true;
}

function closeDialog() {
    dialogVisible.value = false;
    selectedCCTV.value = null;
}
const loading = ref(false);
const loading1 = ref(false);
const loading2 = ref(false);
const videoUrl = ref(null);
const videoUrl1 = ref(null);
const videoUrl2 = ref(null);


async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  loading.value = true;
  videoUrl.value = null;

  try {
    const response = await axios.post('/process-video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    videoUrl.value = response.data.video_url;
  } catch (error) {
    console.error('Error processing video:', error);
  } finally {
    loading.value = false;
  }
}
async function handleFileUpload1(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  loading1.value = true;
  videoUrl1.value = null;

  try {
    const response = await axios.post('/process-video1', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    videoUrl1.value = response.data.video_url;
  } catch (error) {
    console.error('Error processing video:', error);
  } finally {
    loading1.value = false;
  }
}
async function handleFileUpload2(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  loading2.value = true;
  videoUrl2.value = null;

  try {
    const response = await axios.post('/process-video2', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    videoUrl2.value = response.data.video_url;
  } catch (error) {
    console.error('Error processing video:', error);
  } finally {
    loading2.value = false;
  }
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
                        <q-card 
                            v-for="(cctv, index) in cctvs" 
                            :key="index" 
                            class="cctv-card" 
                            @click="openDialog(cctv)"
                        >
                            <div class="title-container">
                                <p class="title">Recording</p>
                            </div>
                            <q-card-section>
                                <img
                    v-if="selectedCCTV" 
                    :src="selectedCCTV.videoSrc" 
                    autoplay 
                    loop
                    class="cctv-video"
                ></img>
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
        </q-layout>

    </AuthenticatedLayout>
    <q-dialog v-model="dialogVisible" backdrop-filter="blur(4px) saturate(150%)">
        <q-card class="cctv-dialog">
            <div class="cctv-dialog-container" style="background: black;" @click.stop>
                <img
                    v-if="selectedCCTV" 
                    :src="selectedCCTV.videoSrc" 
                    autoplay 
                    loop
                    class="cctv-video"
                ></img>
            </div>

            <div class="snapshot-details" style="width: 50%; padding: 20px;">
                <div v-if="selectedCCTV">
                <p class="sub-title">{{ selectedCCTV.name }} - Snapshots</p>

                <div v-for="(dogSnapshots, dogIndex) in groupedSnapshots" :key="dogIndex">
                    <q-expansion-item 
                        :label="'Dog ' + (dogIndex + 1)" 
                        expand-separator
                        dense
                    >
                        <div v-for="(snapshot, index) in dogSnapshots" :key="index" class="snapshot-item">
                            <img :src="snapshot.src" alt="Snapshot" class="snapshot-image" style="width: 100%; object-fit: contain;" />
                            <div class="snapshot-details">
                                <p><strong>Time:</strong> {{ snapshot.time }}</p>
                                <p><strong>Classification:</strong> {{ snapshot.classification }}</p>
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