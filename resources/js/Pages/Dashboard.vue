<script setup>
import { ref, onMounted, inject, watch, onUnmounted } from 'vue';
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
    totalSightings: 0,
    strayDogs: 0,
    strayCats: 0,
    registeredDogs: 0,
    registeredCats: 0,
    totalRegistered: 0
});

// Time period selection for chart
const selectedTimePeriod = ref('daily');
const timePeriodOptions = ['daily', 'weekly', 'monthly'];

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

// Fetch statistics from the server
async function fetchStats() {
    try {
        // Fetch stray animal stats
        const statsResponse = await axios.get('/api/pins/stats');
        if (statsResponse.data) {
            strayAnimalsData.value = {
                totalSightings: statsResponse.data.totalSightings || 0,
                strayDogs: statsResponse.data.dogSightings || 0,
                strayCats: statsResponse.data.catSightings || 0,
                registeredDogs: 0,
                registeredCats: 0,
                totalRegistered: 0
            };
        }

        // Fetch registered animals stats
        const registeredResponse = await axios.get('/api/registered-animals/stats');
        if (registeredResponse.data) {
            strayAnimalsData.value.registeredDogs = registeredResponse.data.dogCount || 0;
            strayAnimalsData.value.registeredCats = registeredResponse.data.catCount || 0;
            strayAnimalsData.value.totalRegistered = registeredResponse.data.totalCount || 0;
        }

        // Update pie chart data
        pieChartSeries.value = [
            strayAnimalsData.value.strayDogs,
            strayAnimalsData.value.strayCats,
            strayAnimalsData.value.registeredDogs,
            strayAnimalsData.value.registeredCats
        ];

        // Update line chart data based on selected time period
        updateLineChartData();
    } catch (error) {
        console.error('Failed to fetch statistics:', error);

        // If error occurs, try to make separate requests for individual stats
        try {
            // Try to at least get stray animals data
            const fallbackStatsResponse = await axios.get('/api/pins/stats');
            if (fallbackStatsResponse.data) {
                strayAnimalsData.value.totalSightings = fallbackStatsResponse.data.totalSightings || 0;
                strayAnimalsData.value.strayDogs = fallbackStatsResponse.data.dogSightings || 0;
                strayAnimalsData.value.strayCats = fallbackStatsResponse.data.catSightings || 0;
            }
        } catch (innerError) {
            console.error('Failed to fetch fallback stats:', innerError);
        }

        // Update chart data with whatever values we have
        pieChartSeries.value = [
            strayAnimalsData.value.strayDogs,
            strayAnimalsData.value.strayCats,
            strayAnimalsData.value.registeredDogs,
            strayAnimalsData.value.registeredCats
        ];

        // Update line chart
        updateLineChartData();
    }
}

// Function to update line chart data based on selected time period
function updateLineChartData() {
    let categories = [];
    let data = [];

    if (selectedTimePeriod.value === 'daily') {
        categories = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        data = [10, 20, 15, 25, 30, 18, 27];
    } else if (selectedTimePeriod.value === 'weekly') {
        categories = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
        data = [42, 65, 48, 89];
    } else if (selectedTimePeriod.value === 'monthly') {
        categories = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        data = [35, 42, 58, 63, 70, 85, 93, 102, 87, 76, 65, 89];
    }

    lineChartOptions.value.xaxis.categories = categories;
    lineChartSeries.value[0].data = data;

    // If we have additional data for registered animals, add it
    if (!lineChartSeries.value[1]) {
        lineChartSeries.value.push({
            name: 'Registered Animals',
            data: data.map(val => Math.round(val * 0.5)) // Create some demo data for registered animals
        });
    } else {
        lineChartSeries.value[1].data = data.map(val => Math.round(val * 0.5));
    }
}

// Watch for time period changes
watch(selectedTimePeriod, () => {
    updateLineChartData();
});

// Fetch data on component mount
onMounted(() => {
    fetchRecentSightings();
    fetchStats();
    filterDataByDate();

    // Force update chart themes based on dark mode
    updateChartThemes(isDarkMode.value);

    // Set up intervals for periodic updates
    const statsInterval = setInterval(fetchStats, 60000);
    const sightingsInterval = setInterval(fetchRecentSightings, 30000);

    // Clean up intervals on unmount
    onUnmounted(() => {
        clearInterval(statsInterval);
        clearInterval(sightingsInterval);
    });
});

// Update the fetchRecentSightings function to use real data
async function fetchRecentSightings() {
    try {
        const response = await axios.get('https://straysafe.me/api2/detected');
        if (response.data && response.data.detected_animals) {
            recentSightings.value = response.data.detected_animals.map(animal => {
                // Convert the image URL from detected-img to debug-img
                const imageUrl = animal.image_url ?
                    animal.image_url.replace('detected-img', 'debug-img') :
                    'https://placehold.co/600x400/4f6642/FFFFFF/png?text=No+Image';

                return {
                    id: animal.id,
                    type: animal.animal_type,
                    location: `Camera ${animal.stream_id}`,
                    timestamp: new Date(animal.timestamp).toLocaleString(),
                    image: imageUrl,
                    classification: animal.classification || 'Unknown',
                    confidence: animal.confidence || 0
                };
            });
        }
    } catch (error) {
        console.error('Error fetching recent sightings:', error);
    }
}

// Line chart for detected animals over time
const lineChartOptions = ref({
    chart: {
        type: 'line',
        height: 350,
        foreColor: isDarkMode.value ? '#fff' : '#333',
        theme: {
            mode: isDarkMode.value ? 'dark' : 'light',
        }
    },
    xaxis: {
        categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        labels: {
            style: {
                colors: Array(7).fill(isDarkMode.value ? '#fff' : '#333'),
            }
        }
    },
    yaxis: {
        labels: {
            style: {
                colors: isDarkMode.value ? '#fff' : '#333',
            }
        }
    },
    title: {
        text: 'Animal Sightings Over Time',
        align: 'left',
        style: {
            color: isDarkMode.value ? '#fff' : '#333',
            fontFamily: 'Poppins, sans-serif',
            fontSize: '18px',
        }
    },
    tooltip: {
        theme: isDarkMode.value ? 'dark' : 'light',
    },
    grid: {
        borderColor: isDarkMode.value ? '#555' : '#e0e0e0',
    },
    legend: {
        position: 'top',
        horizontalAlign: 'right',
        labels: {
            colors: isDarkMode.value ? '#fff' : '#333',
        }
    },
    stroke: {
        width: 3,
        curve: 'smooth'
    },
    colors: ['#4f6642', '#38a3a5'] // Green for stray, blue for registered
});
const lineChartSeries = ref([{
    name: 'Stray Animal Sightings',
    data: [10, 20, 15, 25, 30, 18, 27],
}]);

// Pie chart for stray animal types
const pieChartOptions = ref({
    chart: {
        type: 'pie',
        foreColor: isDarkMode.value ? '#fff' : '#333',
        theme: {
            mode: isDarkMode.value ? 'dark' : 'light',
        }
    },
    labels: ['Stray Dogs', 'Stray Cats', 'Registered Dogs', 'Registered Cats'],
    title: {
        text: 'Distribution of Animal Types',
        align: 'left',
        style: {
            color: isDarkMode.value ? '#fff' : '#333',
            fontFamily: 'Poppins, sans-serif',
            fontSize: '18px',
        }
    },
    legend: {
        position: 'bottom',
        labels: {
            colors: isDarkMode.value ? '#fff' : '#333',
        }
    },
    tooltip: {
        theme: isDarkMode.value ? 'dark' : 'light',
    },
    stroke: {
        width: 0
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
        height: 350,
        foreColor: isDarkMode.value ? '#fff' : '#333',
        theme: {
            mode: isDarkMode.value ? 'dark' : 'light',
        }
    },
    dataLabels: {
        enabled: false
    },
    colors: ["#008FFB"],
    title: {
        text: 'Stray Animal Sightings Heatmap',
        align: 'left',
        style: {
            color: isDarkMode.value ? '#fff' : '#333',
        }
    },
    xaxis: {
        categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        labels: {
            style: {
                colors: isDarkMode.value ? '#fff' : '#333',
            }
        }
    },
    yaxis: {
        labels: {
            style: {
                colors: isDarkMode.value ? '#fff' : '#333',
            }
        }
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

// Function to update chart themes
function updateChartThemes(darkMode) {
    // Update line chart
    lineChartOptions.value = {
        ...lineChartOptions.value,
        chart: {
            ...lineChartOptions.value.chart,
            foreColor: darkMode ? '#fff' : '#333',
            theme: {
                mode: darkMode ? 'dark' : 'light',
            }
        },
        xaxis: {
            ...lineChartOptions.value.xaxis,
            labels: {
                style: {
                    colors: darkMode ? '#fff' : '#333',
                }
            }
        },
        yaxis: {
            labels: {
                style: {
                    colors: darkMode ? '#fff' : '#333',
                }
            }
        },
        title: {
            ...lineChartOptions.value.title,
            style: {
                color: darkMode ? '#fff' : '#333',
            }
        },
    };

    // Update pie chart
    pieChartOptions.value = {
        ...pieChartOptions.value,
        chart: {
            ...pieChartOptions.value.chart,
            foreColor: darkMode ? '#fff' : '#333',
            theme: {
                mode: darkMode ? 'dark' : 'light',
            }
        },
        title: {
            ...pieChartOptions.value.title,
            style: {
                color: darkMode ? '#fff' : '#333',
            }
        },
        legend: {
            labels: {
                colors: darkMode ? '#fff' : '#333',
            }
        }
    };

    // Update heatmap
    heatmapOptions.value = {
        ...heatmapOptions.value,
        chart: {
            ...heatmapOptions.value.chart,
            foreColor: darkMode ? '#fff' : '#333',
            theme: {
                mode: darkMode ? 'dark' : 'light',
            }
        },
        title: {
            ...heatmapOptions.value.title,
            style: {
                color: darkMode ? '#fff' : '#333',
            }
        },
        xaxis: {
            ...heatmapOptions.value.xaxis,
            labels: {
                style: {
                    colors: darkMode ? '#fff' : '#333',
                }
            }
        },
        yaxis: {
            labels: {
                style: {
                    colors: darkMode ? '#fff' : '#333',
                }
            }
        }
    };
}

// Watch for dark mode changes and update chart options
watch(isDarkMode, (newValue) => {
    updateChartThemes(newValue);
});
</script>

<template>
    <Head title="Dashboard" />

    <AuthenticatedLayout>
        <div class="dashboard-container px-6 py-4" :class="{ 'dark-mode': isDarkMode }">
            <!-- Standardized Header Section -->
            <div class="page-header max-w-[1400px] mx-auto">
                <div class="flex justify-between items-center">
                    <div class="header-title">
                        <h1 class="text-3xl font-bold font-poppins">Dashboard</h1>
                        <p class="text-gray-600 dark:text-gray-400">{{ authUser.name }}</p>
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
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6 max-w-[1400px] mx-auto">
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

                <!-- Total Registered Animals Card -->
                <div class="stat-card">
                    <div class="stat-icon" style="background-color: #38a3a5;">
                        <i class="fas fa-clipboard-list"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ strayAnimalsData.totalRegistered }}</div>
                        <div class="stat-label">Total Registered Pets</div>
                    </div>
                </div>

                <!-- Registered Dogs Card -->
                <div class="stat-card">
                    <div class="stat-icon" style="background-color: #38a3a5;">
                        <i class="fas fa-dog"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ strayAnimalsData.registeredDogs }}</div>
                        <div class="stat-label">Registered Dogs</div>
                    </div>
                </div>

                <!-- Registered Cats Card -->
                <div class="stat-card">
                    <div class="stat-icon" style="background-color: #38a3a5;">
                        <i class="fas fa-cat"></i>
                    </div>
                    <div class="stat-info">
                        <div class="stat-value">{{ strayAnimalsData.registeredCats }}</div>
                        <div class="stat-label">Registered Cats</div>
                    </div>
                </div>
            </div>

            <!-- Charts Section -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6 max-w-[1400px] mx-auto">
                <!-- Line Chart -->
                <q-card class="theme-card" flat :dark="isDarkMode" :style="isDarkMode ? { color: 'white' } : {}">
                    <q-card-section class="flex justify-between items-center">
                        <div class="text-xl font-bold" :style="isDarkMode ? { color: 'white' } : {}">
                            Animal Sightings Over Time
                        </div>
                        <div class="time-period-selector">
                            <q-btn-toggle
                                v-model="selectedTimePeriod"
                                :options="[
                                    { label: 'Daily', value: 'daily' },
                                    { label: 'Weekly', value: 'weekly' },
                                    { label: 'Monthly', value: 'monthly' }
                                ]"
                                spread
                                unelevated
                                class="my-custom-toggle"
                                text-color="white"
                                :toggle-color="isDarkMode ? 'blue-7' : 'blue-5'"
                                :color="isDarkMode ? 'blue-9' : 'blue-3'"
                            />
                        </div>
                    </q-card-section>
                    <q-card-section>
                        <VueApexCharts
                            :key="`line-${isDarkMode}-${selectedTimePeriod}`"
                            type="line"
                            :options="lineChartOptions"
                            :series="lineChartSeries"
                            height="350"
                        />
                    </q-card-section>
                </q-card>

                <!-- Pie Chart -->
                <q-card class="theme-card" flat :dark="isDarkMode" :style="isDarkMode ? { color: 'white' } : {}">
                    <q-card-section>
                        <div class="text-xl font-bold mb-4" :style="isDarkMode ? { color: 'white' } : {}">
                            Distribution of Animal Types
                        </div>
                        <VueApexCharts
                            :key="`pie-${isDarkMode}`"
                            type="pie"
                            :options="pieChartOptions"
                            :series="pieChartSeries"
                            height="350"
                        />
                    </q-card-section>
                </q-card>
            </div>

            <!-- Heatmap -->
            <div class="mt-6 max-w-[1400px] mx-auto">
                <q-card class="theme-card" flat :dark="isDarkMode" :style="isDarkMode ? { color: 'white' } : {}">
                    <q-card-section>
                        <div class="text-xl font-bold mb-4" :style="isDarkMode ? { color: 'white' } : {}">
                            Stray Animal Sightings Heatmap
                        </div>
                        <VueApexCharts
                            :key="`heatmap-${isDarkMode}`"
                            type="heatmap"
                            :options="heatmapOptions"
                            :series="heatmapSeries"
                            height="350"
                        />
                    </q-card-section>
                </q-card>
            </div>

            <!-- Recent Sightings Feed -->
            <div class="mt-6 mb-6 max-w-[1400px] mx-auto">
                <q-card class="theme-card" flat :dark="isDarkMode" :style="isDarkMode ? { color: 'white' } : {}">
                    <q-card-section>
                        <div class="text-xl font-bold mb-4" :style="isDarkMode ? { color: 'white' } : {}">Recent Stray Animal Sightings</div>

                        <!-- Recent Sightings Feed -->
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            <q-card
                                v-for="sighting in recentSightings"
                                :key="sighting.id"
                                class="theme-card sighting-card"
                                flat
                                :dark="isDarkMode"
                                :style="isDarkMode ? { color: 'white' } : {}"
                            >
                                <q-img
                                    :src="sighting.image"
                                    height="200px"
                                    :alt="sighting.type"
                                />
                                <q-card-section>
                                    <div class="flex items-center justify-between mb-2">
                                        <div class="text-lg font-bold" :style="isDarkMode ? { color: 'white' } : {}">{{ sighting.type }}</div>
                                        <q-badge
                                            :color="sighting.classification === 'stray' ? 'negative' : 'positive'"
                                        >
                                            {{ sighting.classification }}
                                        </q-badge>
                                    </div>
                                    <div class="text-sm mb-2" :style="isDarkMode ? { color: 'white' } : {}">{{ sighting.location }}</div>
                                    <div class="text-xs text-gray-500" :style="isDarkMode ? { color: '#cbd5e1' } : {}">{{ sighting.timestamp }}</div>
                                </q-card-section>
                            </q-card>

                            <!-- Placeholder card when no sightings -->
                            <q-card
                                v-if="recentSightings.length === 0"
                                class="theme-card sighting-card"
                                flat
                                :dark="isDarkMode"
                                :style="isDarkMode ? { color: 'white' } : {}"
                            >
                                <q-card-section class="text-center">
                                    <q-icon name="pets" size="48px" color="grey-6" />
                                    <div class="text-h6 q-mt-md" :style="isDarkMode ? { color: 'white' } : {}">No Recent Detections</div>
                                    <div class="text-subtitle2" :style="isDarkMode ? { color: 'white' } : {}">Waiting for new animal detections...</div>
                                </q-card-section>
                            </q-card>
                        </div>
                    </q-card-section>
                </q-card>
            </div>
        </div>
    </AuthenticatedLayout>
</template>
