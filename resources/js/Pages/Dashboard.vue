<script setup>
import { ref, onMounted } from 'vue';
import { QCard, QCardSection, QTable, QImg } from 'quasar';
import { Head } from '@inertiajs/vue3';
import VueApexCharts from 'vue3-apexcharts';
import axios from 'axios';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';

const authUser = ref({ name: 'User' });
const strayAnimalsData = ref({
    totalSightings: 120,
    strayDogs: 70,
    strayCats: 40,
});

// Data for Recent Sightings Feed
const recentSightings = ref([]);

// Fetch the recent sightings from the backend
async function fetchRecentSightings() {
    try {
        const response = await axios.get('https://straysafe.me/api/recent-sightings');
        recentSightings.value = response.data;
    } catch (error) {
        console.error('Error fetching recent sightings:', error);
    }
}

// Fetch data on component mount
onMounted(() => {
    fetchRecentSightings();
});

// Line chart for detected animals over time
const lineChartOptions = ref({
    chart: {
        type: 'line',
        height: 350,
    },
    xaxis: {
        categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
    },
    title: {
        text: 'Detected Stray Animals Over Time',
        align: 'left',
    },
});
const lineChartSeries = ref([
    {
        name: 'Detected Stray Animals',
        data: [10, 20, 15, 25, 30, 18, 27],
    },
]);

// Pie chart for stray animal types
const pieChartOptions = ref({
    chart: {
        type: 'pie',
    },
    labels: ['Stray Dogs', 'Stray Cats'],
    title: {
        text: 'Distribution of Stray Animal Types',
        align: 'left',
    },
});
const pieChartSeries = ref([
    strayAnimalsData.value.strayDogs,
    strayAnimalsData.value.strayCats,
]);
</script>


<template>
    <Head title="Dashboard" />

    <AuthenticatedLayout>
        <!-- Header -->
        <q-card class="welcome-card mt-5 mx-10">
            <q-card-section>
                <h3 class="text-2xl font-bold mb-2">Welcome back, {{ authUser.name }}!</h3>
            </q-card-section>
        </q-card>

        <!-- Main Dashboard Content -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <!-- Total Stray Sightings Card -->
            <q-card class="info-card total-sightings-card ml-10">
                <q-card-section class="flex flex-col items-center justify-center h-full">
                    <h3 class="text-lg font-semibold mb-2">Total Stray Sightings</h3>
                    <p class="text-8xl font-bold text-primary">{{ strayAnimalsData.totalSightings }}</p>
                </q-card-section>
            </q-card>

            <!-- Animal Type Breakdown Card -->
            <q-card class="info-card animal-type-breakdown-card mr-10">
                <q-card-section class="flex flex-col items-center justify-center h-full">
                    <h3 class="text-lg font-semibold mb-2">Animal Type Breakdown</h3>
                    <p class="text-2xl font-medium">Dogs: <span class="text-primary font-bold text-2xl">{{ strayAnimalsData.strayDogs }}</span></p>
                    <p class="text-2xl font-medium">Cats: <span class="text-primary font-bold text-2xl">{{ strayAnimalsData.strayCats }}</span></p>
        
                </q-card-section>
            </q-card>
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 mb-10">
            <q-card class="line-chart-card ml-10">
                <q-card-section>
                    <VueApexCharts :series="lineChartSeries" :options="lineChartOptions" type="line" height="350" />
                </q-card-section>
            </q-card>

            <q-card class="pie-chart-card mr-10">
                <q-card-section>
                    <VueApexCharts :series="pieChartSeries" :options="pieChartOptions" type="pie" height="350" />
                </q-card-section>
            </q-card>
        </div>

        <!-- Recent Sightings Feed -->
        <!-- <q-card class="recent-sightings-card mt-6 mx-10">
            <q-card-section>
                <h3 class="text-2xl font-bold mb-4">Recent Sightings Feed</h3>
                <q-table
                    :rows="recentSightings"
                    :columns="[
                        { name: 'timestamp', label: 'Timestamp', align: 'left' },
                        { name: 'animal_type', label: 'Animal Type', align: 'left' },
                        { name: 'location', label: 'Location', align: 'left' },
                        { name: 'snapshot', label: 'Snapshot', align: 'center' },
                    ]"
                    row-key="timestamp"
                >
                    <template v-slot:body-cell-snapshot="props">
                        <q-img :src="props.row.snapshot" style="width: 80px; height: 80px; object-fit: cover;" />
                    </template>
                </q-table>
            </q-card-section>
        </q-card> -->
    </AuthenticatedLayout>
</template>



<style scoped>
.dashboard-container {
    padding-top: 20px;
}

.welcome-card,
.info-card,
.chart-card {
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    background-color: white;
    border-radius: 8px;
    overflow: hidden;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.heatmap-card,
.total-sightings-card,
.captured-animals-card,
.animal-type-breakdown-card,
.line-chart-card,
.pie-chart-card {
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    background-color: white;
    border-radius: 8px;
    overflow: hidden;
}

.q-card-section {
    padding: 16px;
}

.text-gray-800 {
    color: #333;
}

.text-gray-200 {
    color: #ccc;
}
</style>
