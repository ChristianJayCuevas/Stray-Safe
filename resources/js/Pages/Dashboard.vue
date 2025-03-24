<script setup>
import { ref, onMounted, inject, watch } from 'vue';
import { QCard, QCardSection, QTable, QImg, QInput, QSelect, QIcon, QBtn, QDate } from 'quasar';
import { Head } from '@inertiajs/vue3';
import VueApexCharts from 'vue3-apexcharts';
import axios from 'axios';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import Swal from 'sweetalert2';
import '../../css/dashboard.css';

// Get the global dark mode state from the AuthenticatedLayout
const isDarkMode = inject('isDarkMode', ref(false));

const authUser = ref({ name: 'User', isNewUser: true }); // Assuming isNewUser flag to check if it's the user's first visit
const strayAnimalsData = ref({
    totalSightings: 120,
    strayDogs: 70,
    strayCats: 40,
    registeredDogs: 35,
    registeredCats: 25,
});

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
    
    // if (authUser.value.isNewUser) {
    //     Swal.fire({
    //         title: 'Welcome to StraySafe!',
    //         text: 'Please select your barangay or create your own map.',
    //         icon: 'info',
    //         showCancelButton: true,
    //         confirmButtonText: 'Select Barangay',
    //         cancelButtonText: 'Create Own Map',
    //         allowOutsideClick: false,  
    //         allowEscapeKey: false,  
    //     }).then((result) => {
    //         if (result.isConfirmed) {
             
    //             console.log('User selected barangay');
      
    //         } else if (result.dismiss === Swal.DismissReason.cancel) {

    //             console.log('User wants to create their own map');
  
    //         }
    //     });
    // }
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
        <!-- Standardized Header Section -->
        <div class="page-header mx-6 mt-6 mb-6">
            <div class="flex justify-between items-center">
                <div class="header-title">
                    <h1 class="text-3xl font-bold font-poppins">Dashboard</h1>
                    <p class="text-gray-600 dark:text-gray-400">Barangay Sacred Heart</p>
                </div>
                
                <!-- Dashboard Controls -->
                <div class="header-actions flex items-center gap-4">
                    <!-- Date Picker -->
                    <div class="date-picker-wrapper relative">
                        <q-btn 
                            class="date-btn secondary-btn"
                            icon="event"
                            @click="showDatePicker = !showDatePicker"
                        >
                            {{ new Date(selectedDate).toLocaleDateString() }}
                        </q-btn>
                        
                        <q-card v-if="showDatePicker" class="date-picker-card absolute">
                            <q-date 
                                v-model="selectedDate" 
                                mask="YYYY-MM-DD" 
                                today-btn
                                @update:model-value="showDatePicker = false"
                            />
                        </q-card>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Dashboard Content -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6 mx-6">
            <!-- Total Detected Animals Card -->
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-paw"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-value">{{ strayAnimalsData.totalSightings }}</div>
                    <div class="stat-label">Total Stray Animal Sightings</div>
                </div>
            </div>
            
            <!-- Stray Dogs Card -->
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-dog"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-value">{{ strayAnimalsData.strayDogs }}</div>
                    <div class="stat-label">Stray Dogs Detected</div>
                </div>
            </div>
            
            <!-- Stray Cats Card -->
            <div class="stat-card">
                <div class="stat-icon">
                    <i class="fas fa-cat"></i>
                </div>
                <div class="stat-info">
                    <div class="stat-value">{{ strayAnimalsData.strayCats }}</div>
                    <div class="stat-label">Stray Cats Detected</div>
                </div>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 mx-6">
            <!-- Line Chart -->
            <q-card class="theme-card" flat :dark="isDarkMode">
                <q-card-section>
                    <VueApexCharts type="line" :options="lineChartOptions" :series="lineChartSeries" height="350" />
                </q-card-section>
            </q-card>
            
            <!-- Pie Chart -->
            <q-card class="theme-card" flat :dark="isDarkMode">
                <q-card-section>
                    <VueApexCharts type="pie" :options="pieChartOptions" :series="pieChartSeries" height="350" />
                </q-card-section>
            </q-card>
        </div>
        
        <!-- Heatmap -->
        <div class="mt-6 mx-6">
            <q-card class="theme-card" flat :dark="isDarkMode">
                <q-card-section>
                    <VueApexCharts type="heatmap" :options="heatmapOptions" :series="heatmapSeries" height="350" />
                </q-card-section>
            </q-card>
        </div>
        
        <!-- Recent Sightings Feed -->
        <div class="mt-6 mx-6 mb-6">
            <q-card class="theme-card" flat :dark="isDarkMode">
                <q-card-section>
                    <div class="text-xl font-bold mb-4">Recent Stray Animal Sightings</div>
                    
                    <!-- Placeholder for Recent Sightings Feed -->
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <!-- This would be populated with actual data from your backend -->
                        <q-card v-for="i in 6" :key="i" class="theme-card sighting-card" flat :dark="isDarkMode">
                            <q-img src="https://placehold.co/600x400/4f6642/FFFFFF/png?text=Stray+Animal" height="200px" />
                            <q-card-section>
                                <div class="text-lg font-bold mb-1">Stray Dog Spotted</div>
                                <div class="text-sm mb-2">Location: Sample Street, Barangay {{ i }}</div>
                                <div class="text-xs text-gray-500">Reported: {{ new Date().toLocaleDateString() }}</div>
                            </q-card-section>
                        </q-card>
                    </div>
                </q-card-section>
            </q-card>
        </div>
    </AuthenticatedLayout>
</template>
