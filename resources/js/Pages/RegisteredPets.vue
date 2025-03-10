<template>
    <AuthenticatedLayout>
        <div class="registered-pets-container px-6 py-4">
            <!-- Header Section -->
            <div class="header-section flex justify-between items-center mb-6">
                <div>
                    <h1 class="text-3xl font-bold text-black font-poppins">Registered Animals</h1>
                    <p class="text-gray-600">Barangay Sacred Heart</p>
                </div>
                
                <!-- Action Buttons -->
                <div class="flex gap-3">
                    <q-btn 
                        color="primary" 
                        icon="add" 
                        label="Register New" 
                        class="register-btn"
                    />
                    <q-btn 
                        outline 
                        color="secondary" 
                        icon="refresh" 
                        @click="fetchRegisteredAnimals"
                    />
                </div>
            </div>
            
            <!-- Statistics Cards -->
            <div class="stats-section grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <q-card flat class="stat-card">
                    <q-card-section class="flex items-center">
                        <div class="stat-icon bg-blue-100 text-blue-600">
                            <q-icon name="pets" size="sm" />
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-gray-600">Total Registered</p>
                            <p class="text-xl font-bold">{{ totalRegistered }}</p>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat class="stat-card">
                    <q-card-section class="flex items-center">
                        <div class="stat-icon bg-green-100 text-green-600">
                            <q-icon name="today" size="sm" />
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-gray-600">Registered Today</p>
                            <p class="text-xl font-bold">{{ registeredToday }}</p>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat class="stat-card">
                    <q-card-section class="flex items-center">
                        <div class="stat-icon bg-amber-100 text-amber-600">
                            <q-icon name="dog" size="sm" />
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-gray-600">Dogs</p>
                            <p class="text-xl font-bold">{{ dogCount }}</p>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat class="stat-card">
                    <q-card-section class="flex items-center">
                        <div class="stat-icon bg-purple-100 text-purple-600">
                            <q-icon name="cat" size="sm" />
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-gray-600">Cats</p>
                            <p class="text-xl font-bold">{{ catCount }}</p>
                        </div>
                    </q-card-section>
                </q-card>
            </div>
            
            <!-- Search and Filter Bar -->
            <div class="filter-section flex flex-wrap gap-4 mb-6">
                <q-input 
                    v-model="searchText" 
                    placeholder="Search by owner or animal type..." 
                    outlined 
                    dense
                    class="search-input"
                    bg-color="white"
                >
                    <template v-slot:prepend>
                        <q-icon name="search" />
                    </template>
                </q-input>
                
                <q-select
                    v-model="animalTypeFilter"
                    :options="['All Types', 'Dog', 'Cat', 'Other']"
                    label="Animal Type"
                    outlined
                    dense
                    class="filter-select"
                    bg-color="white"
                />
                
                <q-select
                    v-model="statusFilter"
                    :options="['All Status', 'Active', 'Inactive']"
                    label="Status"
                    outlined
                    dense
                    class="filter-select"
                    bg-color="white"
                />
                
                <q-btn 
                    flat 
                    color="negative" 
                    label="Reset Filters" 
                    @click="resetFilters"
                    class="self-end"
                />
            </div>
            
            <!-- Registered Animals Table -->
            <q-card flat class="table-card">
                <q-card-section>
                    <q-table
                        :rows="filteredAnimals"
                        :columns="columns"
                        row-key="id"
                        :loading="loading"
                        :pagination="pagination"
                        class="pets-table"
                        :rows-per-page-options="[10, 15, 20]"
                        no-data-label="No registered animals to display."
                    >
                        <!-- Custom Picture Cell -->
                        <template v-slot:body-cell-picture="props">
                            <q-td :props="props">
                                <div class="avatar-wrapper">
                                    <q-avatar size="60px" class="pet-avatar">
                                        <img :src="props.row.picture" :alt="props.row.owner" />
                                    </q-avatar>
                                </div>
                            </q-td>
                        </template>
                        
                        <!-- Custom Animal Type Cell -->
                        <template v-slot:body-cell-animal_type="props">
                            <q-td :props="props">
                                <q-chip
                                    :color="getAnimalTypeColor(props.row.animal_type)"
                                    text-color="white"
                                    size="sm"
                                >
                                    <q-icon :name="getAnimalTypeIcon(props.row.animal_type)" class="q-mr-xs" />
                                    {{ props.row.animal_type }}
                                </q-chip>
                            </q-td>
                        </template>
                        
                        <!-- Custom Status Cell -->
                        <template v-slot:body-cell-status="props">
                            <q-td :props="props">
                                <q-badge
                                    :color="props.row.status === 'Active' ? 'positive' : 'negative'"
                                    :label="props.row.status"
                                    class="status-badge"
                                />
                            </q-td>
                        </template>
                        
                        <!-- Custom Actions Cell -->
                        <template v-slot:body-cell-actions="props">
                            <q-td :props="props">
                                <div class="flex gap-2">
                                    <q-btn flat round size="sm" color="primary" icon="visibility" />
                                    <q-btn flat round size="sm" color="secondary" icon="edit" />
                                </div>
                            </q-td>
                        </template>
                    </q-table>
                </q-card-section>
            </q-card>
        </div>
    </AuthenticatedLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { QCard, QCardSection, QTable, QImg, QBtn, QIcon, QBadge, QChip, QAvatar, QInput, QSelect, QTd } from 'quasar';
import axios from 'axios';
import { Notify } from 'quasar';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';

// Set the default Axios authorization header
axios.defaults.headers.common['Authorization'] = 'Bearer StraySafeTeam3';

// Data references
const registeredAnimals = ref([]);
const totalRegistered = ref(0);
const registeredToday = ref(0);
const loading = ref(true);
const searchText = ref('');
const animalTypeFilter = ref('All Types');
const statusFilter = ref('All Status');

// Pagination settings
const pagination = ref({
    rowsPerPage: 10,
    sortBy: 'date',
    descending: true
});

// Table columns definition
const columns = [
    { name: 'date', label: 'Date Registered', field: 'date', align: 'left', sortable: true },
    { name: 'picture', label: 'Picture', field: 'picture', align: 'center' },
    { name: 'owner', label: 'Owner', field: 'owner', align: 'left', sortable: true },
    { name: 'contact', label: 'Contact', field: 'contact', align: 'left' },
    { name: 'animal_type', label: 'Animal Type', field: 'animal_type', align: 'left', sortable: true },
    { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
    { name: 'actions', label: 'Actions', field: 'actions', align: 'center' }
];

// Computed properties
const dogCount = computed(() => {
    return registeredAnimals.value.filter(animal => 
        animal.animal_type.toLowerCase() === 'dog'
    ).length;
});

const catCount = computed(() => {
    return registeredAnimals.value.filter(animal => 
        animal.animal_type.toLowerCase() === 'cat'
    ).length;
});

const filteredAnimals = computed(() => {
    return registeredAnimals.value.filter(animal => {
        // Text search
        const searchMatch = searchText.value === '' || 
            animal.owner.toLowerCase().includes(searchText.value.toLowerCase()) ||
            animal.animal_type.toLowerCase().includes(searchText.value.toLowerCase());
        
        // Animal type filter
        const typeMatch = animalTypeFilter.value === 'All Types' || 
            animal.animal_type.toLowerCase() === animalTypeFilter.value.toLowerCase();
        
        // Status filter
        const statusMatch = statusFilter.value === 'All Status' || 
            animal.status === statusFilter.value;
        
        return searchMatch && typeMatch && statusMatch;
    });
});

// Fetch registered animals
async function fetchRegisteredAnimals() {
    loading.value = true;
    try {
        const response = await axios.get('/api/registered-animals');
        const animals = response.data.data; // Adjusted to match your API structure

        registeredAnimals.value = animals.map((animal) => ({
            id: animal.id,
            date: new Date(animal.created_at).toLocaleString(),
            owner: animal.owner || 'Unknown',
            contact: animal.contact || 'N/A',
            animal_type: animal.animal_type || 'N/A',
            picture: animal.picture || 'https://via.placeholder.com/80', // Default placeholder if picture is null
            status: animal.status || 'Active',
            actions: null // Placeholder for actions column
        }));

        totalRegistered.value = animals.length;
        registeredToday.value = animals.filter((animal) => {
            const today = new Date().toISOString().split('T')[0];
            return animal.created_at.startsWith(today);
        }).length;
    } catch (error) {
        console.error('Error fetching registered animals:', error);
        Notify.create({
            type: 'negative',
            message: 'Failed to fetch registered animals.',
        });
        
        // Mock data for development
        registeredAnimals.value = [
            {
                id: 1,
                date: new Date().toLocaleString(),
                owner: 'John Doe',
                contact: '0912-345-6789',
                animal_type: 'Dog',
                picture: 'https://images.unsplash.com/photo-1543466835-00a7907e9de1',
                status: 'Active',
                actions: null
            },
            {
                id: 2,
                date: new Date().toLocaleString(),
                owner: 'Jane Smith',
                contact: '0998-765-4321',
                animal_type: 'Cat',
                picture: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba',
                status: 'Active',
                actions: null
            },
            {
                id: 3,
                date: new Date(Date.now() - 86400000).toLocaleString(),
                owner: 'Mark Johnson',
                contact: '0932-123-4567',
                animal_type: 'Dog',
                picture: 'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e',
                status: 'Inactive',
                actions: null
            }
        ];
        
        totalRegistered.value = registeredAnimals.value.length;
        registeredToday.value = 2;
    } finally {
        loading.value = false;
    }
}

// Reset all filters
function resetFilters() {
    searchText.value = '';
    animalTypeFilter.value = 'All Types';
    statusFilter.value = 'All Status';
}

// Helper functions for styling
function getAnimalTypeColor(type) {
    const typeLower = type.toLowerCase();
    if (typeLower === 'dog') return 'amber';
    if (typeLower === 'cat') return 'purple';
    return 'grey';
}

function getAnimalTypeIcon(type) {
    const typeLower = type.toLowerCase();
    if (typeLower === 'dog') return 'dog';
    if (typeLower === 'cat') return 'cat';
    return 'pets';
}

// Fetch data when component is mounted
onMounted(() => {
    fetchRegisteredAnimals();
});
</script>

<style scoped>
.registered-pets-container {
    background-color: #f8f9fa;
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

.table-card {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.pets-table {
    border-radius: 8px;
}

.search-input {
    min-width: 300px;
}

.filter-select {
    min-width: 150px;
}

.pet-avatar {
    border: 2px solid #eaeaea;
    overflow: hidden;
}

.pet-avatar img {
    object-fit: cover;
    width: 100%;
    height: 100%;
}

.status-badge {
    padding: 4px 8px;
    border-radius: 12px;
}

.register-btn {
    background-color: #4f6642;
}
</style>
