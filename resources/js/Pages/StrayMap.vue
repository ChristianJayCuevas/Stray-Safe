<script setup>
import Map from '@/Components/MapComponent.vue';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { ref, onMounted, inject } from 'vue';
import { QCard, QCardSection, QBtn, QIcon, QBadge, QSeparator, QTooltip } from 'quasar';
import '../../css/stray-map.css';

// Get the global dark mode state from the AuthenticatedLayout
const isDarkMode = inject('isDarkMode', ref(false));

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
        <!-- Standardized Header Section -->
        <div class="page-header mx-6 mt-6 mb-6">
            <div class="flex justify-between items-center">
                <div class="header-title">
                    <h1 class="text-3xl font-bold font-poppins">Stray Map</h1>
                    <p class="text-gray-600 dark:text-gray-400">Barangay Sacred Heart</p>
                </div>
                
                <!-- Map Controls -->
                <div class="header-actions flex gap-3">
                    <q-btn 
                        class="primary-btn"
                        :class="{ 'active-btn': filterActive }"
                        @click="toggleFilters"
                    >
                        <q-icon name="filter_alt" class="q-mr-sm" />
                        Filters
                        <q-tooltip>Toggle filter options</q-tooltip>
                    </q-btn>
                    <q-btn 
                        class="secondary-btn"
                        @click="$emit('refresh')"
                    >
                        <q-icon name="refresh" class="q-mr-sm" />
                        Refresh
                        <q-tooltip>Refresh map data</q-tooltip>
                    </q-btn>
                </div>
            </div>
        </div>
        
        <!-- Filter Panel (conditionally shown) -->
        <div v-if="showFilters" class="filter-panel mx-6 mb-4">
            <q-card flat class="theme-card">
                <q-card-section>
                    <div class="flex flex-wrap gap-4">
                        <div>
                            <p class="text-sm font-medium mb-2">Animal Type</p>
                            <div class="flex gap-2">
                                <q-btn 
                                    class="filter-option-btn"
                                    :class="{ 'active': selectedAnimal === 'all' }"
                                    label="All" 
                                    size="sm"
                                    @click="applyFilter('all')"
                                />
                                <q-btn 
                                    class="filter-option-btn"
                                    :class="{ 'active': selectedAnimal === 'dog' }"
                                    label="Dogs" 
                                    size="sm"
                                    @click="applyFilter('dog')"
                                />
                                <q-btn 
                                    class="filter-option-btn"
                                    :class="{ 'active': selectedAnimal === 'cat' }"
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
                                    class="filter-option-btn"
                                    :class="{ 'active': selectedTimeframe === 'all' }"
                                    label="All Time" 
                                    size="sm"
                                    @click="selectedTimeframe = 'all'"
                                />
                                <q-btn 
                                    class="filter-option-btn"
                                    :class="{ 'active': selectedTimeframe === 'week' }"
                                    label="This Week" 
                                    size="sm"
                                    @click="selectedTimeframe = 'week'"
                                />
                                <q-btn 
                                    class="filter-option-btn"
                                    :class="{ 'active': selectedTimeframe === 'month' }"
                                    label="This Month" 
                                    size="sm"
                                    @click="selectedTimeframe = 'month'"
                                />
                            </div>
                        </div>
                        
                        <div class="ml-auto self-end">
                            <q-btn 
                                class="reset-btn"
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
            <div class="stat-card">
                <div class="stat-icon total-icon">
                    <q-icon name="visibility" size="sm" />
                </div>
                <div class="stat-info">
                    <div class="stat-value">{{ mapStats.totalSightings }}</div>
                    <div class="stat-label">Total Sightings</div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon dog-icon">
                    <q-icon name="pets" size="sm" />
                </div>
                <div class="stat-info">
                    <div class="stat-value">{{ mapStats.dogSightings }}</div>
                    <div class="stat-label">Dog Sightings</div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon cat-icon">
                    <q-icon name="pets" size="sm" />
                </div>
                <div class="stat-info">
                    <div class="stat-value">{{ mapStats.catSightings }}</div>
                    <div class="stat-label">Cat Sightings</div>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon cctv-icon">
                    <q-icon name="videocam" size="sm" />
                </div>
                <div class="stat-info">
                    <div class="stat-value">{{ mapStats.activeCCTVs }}</div>
                    <div class="stat-label">Active CCTVs</div>
                </div>
            </div>
        </div>
        
        <!-- Map Container -->
        <div class="mx-6 mb-6 map-container">
            <Map />
        </div>
    </AuthenticatedLayout>
</template>