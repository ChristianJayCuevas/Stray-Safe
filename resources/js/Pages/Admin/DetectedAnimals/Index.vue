<template>
    <AuthenticatedLayout>
        <Head title="Detected Animals" />

        <div class="cctv-monitor-container px-6 py-4">
            <!-- Header Section -->
            <div class="page-header mb-6">
                <div class="flex justify-between items-center">
                    <div class="header-title">
                        <h1 class="text-3xl font-bold">Detected Animals</h1>
                        <p class="text-secondary">AI-detected animals from surveillance cameras</p>
                    </div>
                    <div class="flex gap-3">
                        <q-btn 
                            color="primary" 
                            label="Refresh" 
                            icon="refresh"
                            @click="fetchDetectedAnimals" 
                            :loading="loading"
                        />
                        <q-select
                            v-model="filter"
                            :options="filterOptions"
                            label="Filter"
                            dense
                            outlined
                            class="bg-white dark:bg-gray-800 rounded-md"
                            style="min-width: 150px;"
                        />
                    </div>
                </div>
            </div>

            <!-- Stats Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <q-card flat bordered class="stat-card">
                    <q-card-section>
                        <div class="flex items-center">
                            <div class="stat-icon mr-4">
                                <i class="fas fa-paw"></i>
                            </div>
                            <div>
                                <div class="text-2xl font-bold">{{ totalAnimals }}</div>
                                <div class="text-sm text-secondary">Total Detected</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section>
                        <div class="flex items-center">
                            <div class="stat-icon mr-4">
                                <i class="fas fa-dog"></i>
                            </div>
                            <div>
                                <div class="text-2xl font-bold">{{ dogCount }}</div>
                                <div class="text-sm text-secondary">Dogs</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section>
                        <div class="flex items-center">
                            <div class="stat-icon mr-4">
                                <i class="fas fa-cat"></i>
                            </div>
                            <div>
                                <div class="text-2xl font-bold">{{ catCount }}</div>
                                <div class="text-sm text-secondary">Cats</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section>
                        <div class="flex items-center">
                            <div class="stat-icon mr-4">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <div>
                                <div class="text-2xl font-bold">{{ strayCount }}</div>
                                <div class="text-sm text-secondary">Strays Identified</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
            </div>
            
            <!-- Loading State -->
            <div v-if="loading" class="flex justify-center items-center py-12">
                <q-spinner color="primary" size="3em" />
                <p class="ml-4 text-lg">Loading detected animals...</p>
            </div>
            
            <!-- Error State -->
            <div v-else-if="error" class="bg-red-100 dark:bg-red-900 text-center p-6 rounded-lg mb-6">
                <i class="fas fa-exclamation-circle text-red-500 text-3xl mb-2"></i>
                <p class="text-red-700 dark:text-red-300">{{ error }}</p>
                <q-btn color="primary" class="mt-4" @click="fetchDetectedAnimals" label="Try Again" />
            </div>
            
            <!-- Empty State -->
            <div v-else-if="filteredAnimals.length === 0" class="bg-gray-100 dark:bg-gray-800 text-center p-12 rounded-lg mb-6">
                <i class="fas fa-search text-gray-400 text-5xl mb-4"></i>
                <p class="text-gray-600 dark:text-gray-400 text-xl">No animals detected</p>
                <p class="text-gray-500 dark:text-gray-500 mt-2">Try adjusting your filters or refresh to check for new detections</p>
            </div>
            
            <!-- Detected Animals Cards -->
            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                <q-card 
                    v-for="animal in filteredAnimals" 
                    :key="animal.id" 
                    flat 
                    bordered 
                    class="animal-card"
                    @click="showAnimalDetails(animal)"
                >
                    <div class="relative">
                        <img 
                            :src="getImageUrl(animal)" 
                            :alt="animal.animal_type"
                            class="w-full h-48 object-cover"
                            @error="handleImageError"
                        />
                        <div class="absolute top-2 right-2">
                            <q-chip 
                                :color="animal.classification === 'stray' ? 'negative' : 'positive'"
                                text-color="white"
                                class="text-bold"
                            >
                                {{ animal.classification === 'stray' ? 'Stray' : 'Not Stray' }}
                            </q-chip>
                        </div>
                        <div class="absolute top-2 left-2">
                            <q-chip 
                                color="accent"
                                text-color="white"
                            >
                                {{ animal.animal_type }}
                            </q-chip>
                        </div>
                    </div>
                    
                    <q-card-section>
                        <div class="flex justify-between items-start">
                            <div>
                                <div class="text-lg font-bold">{{ formatAnimalType(animal) }}</div>
                                <div class="text-sm text-secondary">{{ formatDate(animal.timestamp) }}</div>
                            </div>
                            <q-badge 
                                :color="getNotificationColor(animal)" 
                                class="px-2 py-1"
                            >
                                {{ formatNotificationType(animal) }}
                            </q-badge>
                        </div>
                    </q-card-section>
                    
                    <q-separator />
                    
                    <q-card-section class="q-pt-sm">
                        <div class="grid grid-cols-2 gap-2 text-sm">
                            <div>
                                <div class="text-xs font-bold text-gray-500">Camera</div>
                                <div>{{ animal.stream_id }}</div>
                            </div>
                            <div>
                                <div class="text-xs font-bold text-gray-500">Animal ID</div>
                                <div>{{ animal.animal_id }}</div>
                            </div>
                            <div class="col-span-2">
                                <div class="text-xs font-bold text-gray-500">Match Score</div>
                                <q-linear-progress
                                    :value="animal.match_score || 0"
                                    color="accent"
                                    class="q-mt-sm"
                                />
                                <div class="text-right text-xs mt-1">{{ formatPercentage(animal.match_score) }}</div>
                            </div>
                        </div>
                    </q-card-section>
                    
                    <q-card-actions align="right">
                        <q-btn flat color="primary" icon="visibility" label="View Details" />
                    </q-card-actions>
                </q-card>
            </div>
            
            <!-- Pagination -->
            <div class="flex justify-center mt-8">
                <q-pagination
                    v-model="currentPage"
                    :max="totalPages"
                    direction-links
                    boundary-links
                    color="primary"
                    active-color="accent"
                />
            </div>
        </div>
        
        <!-- Animal Details Modal -->
        <q-dialog v-model="showDetails" persistent>
            <q-card style="width: 700px; max-width: 90vw;">
                <q-card-section class="q-py-sm bg-accent">
                    <div class="flex justify-between items-center">
                        <div class="text-xl font-bold text-white">Animal Detection Details</div>
                        <q-btn flat round dense icon="close" @click="showDetails = false" class="text-white" />
                    </div>
                </q-card-section>
                
                <q-card-section v-if="selectedAnimal">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <div class="relative">
                                <img 
                                    :src="getImageUrl(selectedAnimal)" 
                                    :alt="selectedAnimal.animal_type"
                                    class="w-full rounded-lg"
                                    @error="handleImageError"
                                />
                                <div class="absolute top-2 right-2">
                                    <q-chip 
                                        :color="selectedAnimal.classification === 'stray' ? 'negative' : 'positive'"
                                        text-color="white"
                                        class="text-bold"
                                    >
                                        {{ selectedAnimal.classification === 'stray' ? 'Stray' : 'Not Stray' }}
                                    </q-chip>
                                </div>
                            </div>
                            
                            <div class="mt-4" v-if="selectedAnimal.match && selectedAnimal.match_method">
                                <div class="text-sm font-bold mb-2">Match Reference:</div>
                                <div class="bg-gray-100 dark:bg-gray-800 p-3 rounded">
                                    <div class="text-xs">{{ selectedAnimal.match }}</div>
                                    <div class="text-xs text-gray-500">Match method: {{ selectedAnimal.match_method }}</div>
                                    <div class="font-bold mt-1">Score: {{ formatPercentage(selectedAnimal.match_score) }}</div>
                                </div>
                            </div>
                        </div>
                        
                        <div>
                            <h3 class="text-lg font-bold mb-4">Detection Information</h3>
                            
                            <div class="mb-4">
                                <div class="text-sm font-bold text-gray-500">Animal Type</div>
                                <div class="text-lg">{{ formatAnimalType(selectedAnimal) }}</div>
                            </div>
                            
                            <div class="mb-4">
                                <div class="text-sm font-bold text-gray-500">Detection Time</div>
                                <div>{{ formatDateTime(selectedAnimal.timestamp) }}</div>
                            </div>
                            
                            <div class="mb-4">
                                <div class="text-sm font-bold text-gray-500">Camera Stream</div>
                                <div>{{ selectedAnimal.stream_id }}</div>
                            </div>
                            
                            <div class="mb-4">
                                <div class="text-sm font-bold text-gray-500">Animal ID</div>
                                <div>{{ selectedAnimal.animal_id }}</div>
                            </div>
                            
                            <div class="mb-4">
                                <div class="text-sm font-bold text-gray-500">Notification Type</div>
                                <div>
                                    <q-badge 
                                        :color="getNotificationColor(selectedAnimal)" 
                                        class="px-2 py-1"
                                    >
                                        {{ formatNotificationType(selectedAnimal) }}
                                    </q-badge>
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <div class="text-sm font-bold text-gray-500">System ID</div>
                                <div class="text-xs font-mono break-all bg-gray-100 dark:bg-gray-800 p-1 rounded">
                                    {{ selectedAnimal.id }}
                                </div>
                            </div>
                        </div>
                    </div>
                </q-card-section>
                
                <q-card-actions align="right">
                    <q-btn color="primary" label="Close" @click="showDetails = false" />
                </q-card-actions>
            </q-card>
        </q-dialog>
    </AuthenticatedLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Head } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import axios from 'axios';

// State management
const detectedAnimals = ref([]);
const loading = ref(true);
const error = ref(null);
const currentPage = ref(1);
const itemsPerPage = ref(12);
const filter = ref('all');
const showDetails = ref(false);
const selectedAnimal = ref(null);

// Filter options
const filterOptions = [
    { label: 'All Animals', value: 'all' },
    { label: 'Dogs Only', value: 'dog' },
    { label: 'Cats Only', value: 'cat' },
    { label: 'Strays Only', value: 'stray' },
    { label: 'Non-Strays', value: 'not_stray' },
];

// Calculate statistics
const totalAnimals = computed(() => detectedAnimals.value.length);
const dogCount = computed(() => detectedAnimals.value.filter(animal => animal.animal_type === 'dog').length);
const catCount = computed(() => detectedAnimals.value.filter(animal => animal.animal_type === 'cat').length);
const strayCount = computed(() => detectedAnimals.value.filter(animal => animal.classification === 'stray').length);

// Filter animals based on selection
const filteredAnimals = computed(() => {
    let filtered = [...detectedAnimals.value];
    
    // Apply filters
    if (filter.value === 'dog') {
        filtered = filtered.filter(animal => animal.animal_type === 'dog');
    } else if (filter.value === 'cat') {
        filtered = filtered.filter(animal => animal.animal_type === 'cat');
    } else if (filter.value === 'stray') {
        filtered = filtered.filter(animal => animal.classification === 'stray');
    } else if (filter.value === 'not_stray') {
        filtered = filtered.filter(animal => animal.classification === 'not_stray');
    }
    
    // Sort by timestamp (newest first)
    filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    return filtered;
});

// Pagination
const paginatedAnimals = computed(() => {
    const startIndex = (currentPage.value - 1) * itemsPerPage.value;
    const endIndex = startIndex + itemsPerPage.value;
    return filteredAnimals.value.slice(startIndex, endIndex);
});

const totalPages = computed(() => {
    return Math.ceil(filteredAnimals.value.length / itemsPerPage.value);
});

// Methods
const fetchDetectedAnimals = async () => {
    loading.value = true;
    error.value = null;
    
    try {
        const response = await axios.get('https://straysafe.me/api2/detected');
        
        if (response.data && Array.isArray(response.data.detected_animals)) {
            detectedAnimals.value = response.data.detected_animals;
        } else {
            detectedAnimals.value = [];
        }
    } catch (err) {
        console.error('Error fetching detected animals:', err);
        error.value = 'Failed to load detected animals. Please try again.';
        detectedAnimals.value = [];
    } finally {
        loading.value = false;
    }
};

const getImageUrl = (animal) => {
    if (!animal || !animal.image_url) return '/placeholder.jpg';
    
    // Convert the API path to a full URL
    const baseUrl = 'https://straysafe.me';
    return baseUrl + animal.image_url;
};

const handleImageError = (e) => {
    // Replace with placeholder if image fails to load
    e.target.src = '/placeholder.jpg';
};

const formatDate = (dateString) => {
    if (!dateString) return 'Unknown date';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        return 'Today, ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
        return 'Yesterday, ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else {
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
};

const formatDateTime = (dateString) => {
    if (!dateString) return 'Unknown date';
    
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};

const formatAnimalType = (animal) => {
    if (!animal) return '';
    
    const type = animal.animal_type || '';
    return type.charAt(0).toUpperCase() + type.slice(1) + ' ' + (animal.animal_id || '');
};

const formatPercentage = (value) => {
    if (value === undefined || value === null) return '0%';
    
    const percentage = (value * 100).toFixed(1);
    return `${percentage}%`;
};

const formatNotificationType = (animal) => {
    if (!animal) return '';
    
    const type = animal.notification_type || '';
    
    switch (type) {
        case 'owner_notification':
            return 'Owner Notified';
        case 'pound_notification':
            return 'Pound Notified';
        case 'no_notification':
            return 'No Action';
        default:
            return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
};

const getNotificationColor = (animal) => {
    if (!animal) return 'grey';
    
    const type = animal.notification_type || '';
    
    switch (type) {
        case 'owner_notification':
            return 'blue';
        case 'pound_notification':
            return 'orange';
        case 'no_notification':
            return 'grey';
        default:
            return 'primary';
    }
};

const showAnimalDetails = (animal) => {
    selectedAnimal.value = animal;
    showDetails.value = true;
};

// Fetch data on component mount
onMounted(() => {
    fetchDetectedAnimals();
});
</script>

<style scoped>
/* Card styling */
.animal-card {
    background-color: var(--card-bg, #d4d8bd);
    transition: transform 0.2s;
    height: 100%;
    cursor: pointer;
}

.animal-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.dark-mode .animal-card {
    background-color: var(--dark-card-bg, #1e293b);
}

/* Card header style */
.bg-accent {
    background-color: var(--accent-color, #4f6642);
}

/* Icon styling */
.stat-icon {
    background-color: var(--accent-color, #4f6642);
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
}

/* Text styling */
.text-secondary {
    color: var(--text-secondary, #64748b);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
    }
}
</style> 