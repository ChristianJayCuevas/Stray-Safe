<script setup>
import { ref, onMounted, watch } from 'vue';
import { QCard, QCardSection, QTable, QImg, QInput, QSelect, QIcon, QBtn, QDate } from 'quasar';
import { Head } from '@inertiajs/vue3';
import VueApexCharts from 'vue3-apexcharts';
import axios from 'axios';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import Swal from 'sweetalert2';

const authUser = ref({ name: 'User', isNewUser: true }); // Assuming isNewUser flag to check if it's the user's first visit
const strayAnimalsData = ref({
    totalSightings: 120,
    strayDogs: 70,
    strayCats: 40,
    registeredDogs: 35,
    registeredCats: 25,
});

// Search functionality
const searchQuery = ref('');

// Date selection
const selectedDate = ref(new Date().toISOString().split('T')[0]);
const showDatePicker = ref(false);

// Data for Recent Sightings Feed
const recentSightings = ref([]);

// Filter data based on date
function filterDataByDate() {
    console.log(`Filtering data for date: ${selectedDate.value}`);
    // Here you would implement the actual filtering logic
    // For example, fetching data for the selected date from your API
    fetchDataForDate(selectedDate.value);
}

// Watch for date changes and update data
watch(selectedDate, (newDate) => {
    filterDataByDate();
});

// Fetch data for a specific date
async function fetchDataForDate(date) {
    try {
        // This would be your actual API call
        // const response = await axios.get(`https://straysafe.me/api/sightings?date=${date}`);
        // Update your data with the response
        console.log(`Fetched data for date: ${date}`);
    } catch (error) {
        console.error('Error fetching data for date:', error);
    }
}

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
    filterDataByDate(); // Initial data load based on default date
    
    // Show Swal2 popup if the user is new
    if (authUser.value.isNewUser) {
        Swal.fire({
            title: 'Welcome to StraySafe!',
            text: 'Please select your barangay or create your own map.',
            icon: 'info',
            showCancelButton: true,
            confirmButtonText: 'Select Barangay',
            cancelButtonText: 'Create Own Map',
            allowOutsideClick: false,  // Prevent clicking outside to close
            allowEscapeKey: false,  
        }).then((result) => {
            if (result.isConfirmed) {
                // Redirect or open barangay selection
                console.log('User selected barangay');
                // You can redirect or show barangay selection component here
            } else if (result.dismiss === Swal.DismissReason.cancel) {
                // Open MapBox or create your own map logic
                console.log('User wants to create their own map');
                // You can open the map creation logic or redirect to the map creation page
            }
        });
    }
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
const lineChartSeries = ref([{
    name: 'Detected Stray Animals',
    data: [10, 20, 15, 25, 30, 18, 27],
}]);

// Pie chart for stray animal types
const pieChartOptions = ref({
    chart: {
        type: 'pie',
    },
    labels: ['Stray Dogs', 'Stray Cats', 'Registered Dogs', 'Registered Cats'],
    title: {
        text: 'Distribution of Animal Types',
        align: 'left',
    },
});
const pieChartSeries = ref([
    strayAnimalsData.value.strayDogs, 
    strayAnimalsData.value.strayCats,
    strayAnimalsData.value.registeredDogs,
    strayAnimalsData.value.registeredCats
]);

// Heatmap data
const heatmapOptions = ref({
    chart: {
        type: 'heatmap',
        height: 350
    },
    dataLabels: {
        enabled: false
    },
    colors: ["#008FFB"],
    title: {
        text: 'Stray Animal Sightings Heatmap',
        align: 'left'
    },
    xaxis: {
        categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    }
});

const heatmapSeries = ref([
    {
        name: 'Morning',
        data: generateHeatmapData(7, 12, 30)
    },
    {
        name: 'Afternoon',
        data: generateHeatmapData(7, 8, 40)
    },
    {
        name: 'Evening',
        data: generateHeatmapData(7, 15, 25)
    },
    {
        name: 'Night',
        data: generateHeatmapData(7, 10, 20)
    }
]);

// Helper function to generate random data for heatmap
function generateHeatmapData(count, min, max) {
    const data = [];
    for(let i = 0; i < count; i++) {
        data.push({
            x: i,
            y: Math.floor(Math.random() * (max - min + 1)) + min
        });
    }
    return data;
}
</script>

<template>
    <Head title="Dashboard" />

    <AuthenticatedLayout>
        <!-- Dashboard Header with Title, Search, and Date Picker -->
        <div class="dashboard-header mx-6 mt-6 mb-4">
            <div class="flex justify-between items-center">
                <!-- Dashboard Title -->
                <div class="dashboard-title">
                    <h1 class="text-3xl font-bold text-black font-poppins">Dashboard</h1>
                </div>
                
                <!-- Search and Date Picker -->
                <div class="dashboard-controls flex items-center gap-4">
                    <!-- Search Bar -->
                    <q-input 
                        v-model="searchQuery" 
                        outlined 
                        dense
                        placeholder="Search..." 
                        class="search-input bg-white"
                        bg-color="white"
                    >
                        <template v-slot:append>
                            <div class="search-icon">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                    <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
                                </svg>
                            </div>
                        </template>
                    </q-input>
                    
                    <!-- Date Picker -->
                    <div class="date-picker-container">
                        <q-btn 
                            outline 
                            class="date-picker-btn bg-white"
                            color="black"
                            @click="showDatePicker = !showDatePicker"
                        >
                            <div class="flex items-center">
                                <q-icon name="event" class="mr-2" />
                                <span class="font-poppins">{{ selectedDate }}</span>
                            </div>
                        </q-btn>
                        
                        <q-menu v-model="showDatePicker" anchor="bottom right" self="top right">
                            <q-date 
                                v-model="selectedDate" 
                                @update:model-value="(date) => { showDatePicker = false; filterDataByDate(); }"
                                minimal
                                class="bg-white"
                            />
                        </q-menu>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Dashboard Content - Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6 mx-6">
            <!-- Total Detected Animals Card -->
            <q-card class="info-card total-animals-card" flat>
                <q-card-section class="flex flex-col items-center justify-center h-full">
                    <div class="text-center">
                        <h3 class="text-lg font-semibold mb-2 font-poppins">Total Detected Animals</h3>
                        <p class="text-6xl font-bold text-primary font-poppins">{{ strayAnimalsData.totalSightings }}</p>
                    </div>
                </q-card-section>
            </q-card>

            <!-- Stray Dogs Card -->
            <q-card class="info-card stray-dogs-card" flat>
                <q-card-section class="flex flex-col items-center justify-center h-full">
                    <div class="text-center">
                        <h3 class="text-lg font-semibold mb-2 font-poppins">Stray Dogs</h3>
                        <p class="text-6xl font-bold text-primary font-poppins">{{ strayAnimalsData.strayDogs }}</p>
                    </div>
                </q-card-section>
            </q-card>

            <!-- Stray Cats Card -->
            <q-card class="info-card stray-cats-card" flat>
                <q-card-section class="flex flex-col items-center justify-center h-full">
                    <div class="text-center">
                        <h3 class="text-lg font-semibold mb-2 font-poppins">Stray Cats</h3>
                        <p class="text-6xl font-bold text-primary font-poppins">{{ strayAnimalsData.strayCats }}</p>
                    </div>
                </q-card-section>
            </q-card>

            <!-- Registered Dogs Card -->
            <q-card class="info-card registered-dogs-card" flat>
                <q-card-section class="flex flex-col items-center justify-center h-full">
                    <div class="text-center">
                        <h3 class="text-lg font-semibold mb-2 font-poppins">Registered Dogs</h3>
                        <p class="text-6xl font-bold text-primary font-poppins">{{ strayAnimalsData.registeredDogs }}</p>
                    </div>
                </q-card-section>
            </q-card>

            <!-- Registered Cats Card -->
            <q-card class="info-card registered-cats-card" flat>
                <q-card-section class="flex flex-col items-center justify-center h-full">
                    <div class="text-center">
                        <h3 class="text-lg font-semibold mb-2 font-poppins">Registered Cats</h3>
                        <p class="text-6xl font-bold text-primary font-poppins">{{ strayAnimalsData.registeredCats }}</p>
                    </div>
                </q-card-section>
            </q-card>

            <!-- Empty Card for Balance (or can be used for another metric) -->
            <q-card class="info-card empty-card" flat>
                <q-card-section class="flex flex-col items-center justify-center h-full">
                    <div class="text-center">
                        <h3 class="text-lg font-semibold mb-2 font-poppins">Total Registered</h3>
                        <p class="text-6xl font-bold text-primary font-poppins">{{ strayAnimalsData.registeredDogs + strayAnimalsData.registeredCats }}</p>
                    </div>
                </q-card-section>
            </q-card>
        </div>

        <!-- Charts Section -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 mx-6">
            <!-- Line Chart Card -->
            <q-card class="chart-card line-chart-card" flat>
                <q-card-section>
                    <VueApexCharts :series="lineChartSeries" :options="lineChartOptions" type="line" height="350" />
                </q-card-section>
            </q-card>

            <!-- Pie Chart Card -->
            <q-card class="chart-card pie-chart-card" flat>
                <q-card-section>
                    <VueApexCharts :series="pieChartSeries" :options="pieChartOptions" type="pie" height="350" />
                </q-card-section>
            </q-card>
        </div>

        <!-- Heatmap Section -->
        <div class="mt-6 mx-6 mb-6">
            <q-card class="chart-card heatmap-card" flat>
                <q-card-section>
                    <VueApexCharts :series="heatmapSeries" :options="heatmapOptions" type="heatmap" height="350" />
                </q-card-section>
            </q-card>
        </div>
    </AuthenticatedLayout>
</template>

<style scoped>
.dashboard-container {
    padding-top: 20px;
}

.dashboard-header {
    margin-bottom: 20px;
}

.search-input {
    width: 250px;
    background-color: white !important;
}

.date-picker-btn {
    min-width: 150px;
    background-color: white !important;
}

.info-card,
.chart-card {
    background-color: #d4d8bd;
    border-radius: 8px;
    overflow: hidden;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

.info-card:hover,
.chart-card:hover {
    transform: translateY(-5px);
    transition: all 0.3s ease;
}

.heatmap-card,
.total-animals-card,
.stray-dogs-card,
.stray-cats-card,
.registered-dogs-card,
.registered-cats-card,
.line-chart-card,
.pie-chart-card {
    background-color: #d4d8bd;
    border-radius: 8px;
    overflow: hidden;
    transition: all 0.3s ease;
}

.heatmap-card:hover,
.total-animals-card:hover,
.stray-dogs-card:hover,
.stray-cats-card:hover,
.registered-dogs-card:hover,
.registered-cats-card:hover,
.line-chart-card:hover,
.pie-chart-card:hover {
    transform: translateY(-5px);
    transition: all 0.3s ease;
}

.q-card-section {
    padding: 16px;
}

.text-primary {
    color: #4f6642;
}

.text-gray-800 {
    color: #333;
}

.text-gray-200 {
    color: #eee;
}

/* Apply Poppins font to all text */
* {
    font-family: 'Poppins', sans-serif;
}
</style>
