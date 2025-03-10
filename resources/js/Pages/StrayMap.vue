<script setup>
import Map from '@/Components/MapComponent.vue';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { ref, onMounted } from 'vue';
import { QCard, QCardSection, QBtn, QIcon, QBadge, QSeparator } from 'quasar';

// Statistics data
const mapStats = ref({
    totalSightings: 87,
    dogSightings: 52,
    catSightings: 35,
    activeCCTVs: 12
});

// Filter states
const filterActive = ref(false);
const selectedAnimal = ref('all');
const selectedTimeframe = ref('all');

// Toggle filter panel
const showFilters = ref(false);

function toggleFilters() {
    showFilters.value = !showFilters.value;
}

function applyFilter(animal) {
    selectedAnimal.value = animal;
    filterActive.value = true;
}

function resetFilters() {
    selectedAnimal.value = 'all';
    selectedTimeframe.value = 'all';
    filterActive.value = false;
}
</script>

<template>
    <AuthenticatedLayout>
        <!-- Header Section -->
        <div class="map-header mx-6 mt-6 mb-4">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold text-black font-poppins">Stray Map</h1>
                    <p class="text-gray-600">Barangay Sacred Heart</p>
                </div>
                
                <!-- Map Controls -->
                <div class="flex gap-3">
                    <q-btn 
                        outline 
                        color="primary" 
                        icon="filter_alt" 
                        label="Filters" 
                        @click="toggleFilters"
                        :class="{ 'filter-active': filterActive }"
                    />
                    <q-btn 
                        outline 
                        color="secondary" 
                        icon="refresh" 
                        label="Refresh"
                    />
                </div>
            </div>
        </div>
        
        <!-- Filter Panel (conditionally shown) -->
        <div v-if="showFilters" class="filter-panel mx-6 mb-4">
            <q-card flat class="bg-gray-100">
                <q-card-section>
                    <div class="flex flex-wrap gap-4">
                        <div>
                            <p class="text-sm font-medium mb-2">Animal Type</p>
                            <div class="flex gap-2">
                                <q-btn 
                                    :outline="selectedAnimal !== 'all'" 
                                    :color="selectedAnimal === 'all' ? 'primary' : 'gray'" 
                                    label="All" 
                                    size="sm"
                                    @click="applyFilter('all')"
                                />
                                <q-btn 
                                    :outline="selectedAnimal !== 'dog'" 
                                    :color="selectedAnimal === 'dog' ? 'primary' : 'gray'" 
                                    label="Dogs" 
                                    size="sm"
                                    @click="applyFilter('dog')"
                                />
                                <q-btn 
                                    :outline="selectedAnimal !== 'cat'" 
                                    :color="selectedAnimal === 'cat' ? 'primary' : 'gray'" 
                                    label="Cats" 
                                    size="sm"
                                    @click="applyFilter('cat')"
                                />
                            </div>
                        </div>
                        
                        <div>
                            <p class="text-sm font-medium mb-2">Time Period</p>
                            <div class="flex gap-2">
                                <q-btn 
                                    :outline="selectedTimeframe !== 'all'" 
                                    :color="selectedTimeframe === 'all' ? 'primary' : 'gray'" 
                                    label="All Time" 
                                    size="sm"
                                    @click="selectedTimeframe = 'all'"
                                />
                                <q-btn 
                                    :outline="selectedTimeframe !== 'week'" 
                                    :color="selectedTimeframe === 'week' ? 'primary' : 'gray'" 
                                    label="This Week" 
                                    size="sm"
                                    @click="selectedTimeframe = 'week'"
                                />
                                <q-btn 
                                    :outline="selectedTimeframe !== 'month'" 
                                    :color="selectedTimeframe === 'month' ? 'primary' : 'gray'" 
                                    label="This Month" 
                                    size="sm"
                                    @click="selectedTimeframe = 'month'"
                                />
                            </div>
                        </div>
                        
                        <div class="ml-auto self-end">
                            <q-btn 
                                flat 
                                color="negative" 
                                label="Reset" 
                                size="sm"
                                @click="resetFilters"
                            />
                        </div>
                    </div>
                </q-card-section>
            </q-card>
        </div>
        
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mx-6 mb-4">
            <q-card flat class="stat-card">
                <q-card-section class="flex items-center">
                    <div class="stat-icon bg-blue-100 text-blue-600">
                        <q-icon name="visibility" size="sm" />
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-gray-600">Total Sightings</p>
                        <p class="text-xl font-bold">{{ mapStats.totalSightings }}</p>
                    </div>
                </q-card-section>
            </q-card>
            
            <q-card flat class="stat-card">
                <q-card-section class="flex items-center">
                    <div class="stat-icon bg-amber-100 text-amber-600">
                        <q-icon name="pets" size="sm" />
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-gray-600">Dog Sightings</p>
                        <p class="text-xl font-bold">{{ mapStats.dogSightings }}</p>
                    </div>
                </q-card-section>
            </q-card>
            
            <q-card flat class="stat-card">
                <q-card-section class="flex items-center">
                    <div class="stat-icon bg-green-100 text-green-600">
                        <q-icon name="pets" size="sm" />
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-gray-600">Cat Sightings</p>
                        <p class="text-xl font-bold">{{ mapStats.catSightings }}</p>
                    </div>
                </q-card-section>
            </q-card>
            
            <q-card flat class="stat-card">
                <q-card-section class="flex items-center">
                    <div class="stat-icon bg-purple-100 text-purple-600">
                        <q-icon name="videocam" size="sm" />
                    </div>
                    <div class="ml-3">
                        <p class="text-sm text-gray-600">Active CCTVs</p>
                        <p class="text-xl font-bold">{{ mapStats.activeCCTVs }}</p>
                    </div>
                </q-card-section>
            </q-card>
        </div>
        
        <!-- Map Container -->
        <div class="mx-6 mb-6">
            <Map />
        </div>
    </AuthenticatedLayout>
</template>

<style scoped>
.map-header {
    margin-bottom: 1rem;
}

.filter-active {
    background-color: #4f6642;
    color: white;
}

.stat-card {
    background-color: #d4d8bd;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>