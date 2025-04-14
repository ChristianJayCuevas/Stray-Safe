<template>
    <AuthenticatedLayout>
        <div class="registered-pets-container px-6 py-4" :class="{ 'dark-mode': isDarkMode }">
            <!-- Standardized Header Section -->
            <div class="page-header px-6">
                <div class="flex justify-between items-center">
                    <div class="header-title">
                        <h1 class="text-3xl font-bold font-poppins">Registered Animals</h1>
                        <p class="text-gray-600 dark:text-gray-400">{{ user.name }}</p>
                    </div>

                    <!-- Action Buttons -->
                    <div class="header-actions flex gap-3">
                        <q-btn
                            class="primary-btn"
                            icon-right="add"
                            label="Register New"
                        >
                            <q-tooltip>Add a new animal registration</q-tooltip>
                        </q-btn>
                        <q-btn
                            class="secondary-btn"
                            icon="refresh"
                            @click="fetchRegisteredAnimals"
                        >
                            <q-tooltip>Refresh animal data</q-tooltip>
                        </q-btn>
                    </div>
                </div>
            </div>

            <!-- Main Content with consistent padding -->

                <!-- Statistics Cards -->
                <div class="stats-section grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div class="stat-card">
                        <div class="stat-icon total-icon">
                            <q-icon name="pets" size="sm" />
                        </div>
                        <div class="stat-info">
                            <div class="stat-value">{{ totalRegistered }}</div>
                            <div class="stat-label">Total Registered</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon today-icon">
                            <q-icon name="today" size="sm" />
                        </div>
                        <div class="stat-info">
                            <div class="stat-value">{{ registeredToday }}</div>
                            <div class="stat-label">Registered Today</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon dog-icon">
                            <q-icon name="dog" size="sm" />
                        </div>
                        <div class="stat-info">
                            <div class="stat-value">{{ dogCount }}</div>
                            <div class="stat-label">Dogs</div>
                        </div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-icon cat-icon">
                            <q-icon name="cat" size="sm" />
                        </div>
                        <div class="stat-info">
                            <div class="stat-value">{{ catCount }}</div>
                            <div class="stat-label">Cats</div>
                        </div>
                    </div>
                </div>

                <!-- Search and Filter Bar -->
                <q-card flat class="filter-card mb-6">
                    <q-card-section>
                        <div class="filter-section flex flex-wrap gap-4">
                            <q-input
                                v-model="searchText"
                                placeholder="Search by owner or animal type..."
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
                                class="filter-select"
                                bg-color="white"
                            >
                                <template v-slot:prepend>
                                    <q-icon name="pets" />
                                </template>
                            </q-select>

                            <q-select
                                v-model="statusFilter"
                                :options="['All Status', 'Active', 'Inactive']"
                                label="Status"
                                class="filter-select"
                                bg-color="white"
                            >
                                <template v-slot:prepend>
                                    <q-icon name="check_circle" />
                                </template>
                            </q-select>

                            <q-btn
                                class="reset-btn self-end"
                                label="Reset Filters"
                                @click="resetFilters"
                            >
                                <q-tooltip>Clear all filters</q-tooltip>
                            </q-btn>
                        </div>
                    </q-card-section>
                </q-card>

                <!-- Registered Animals Table -->
                <q-card flat class="theme-card mb-6">
                    <q-card-section>
                        <q-table
                            :rows="filteredAnimals"
                            :columns="columns"
                            row-key="id"
                            :loading="loading"
                            :pagination="pagination"
                            :rows-per-page-options="[10, 15, 20]"
                            no-data-label="No registered animals to display."
                            :dark="isDarkMode"

                        >
                            <template v-slot:loading>
                                <q-inner-loading showing color="primary">
                                    <q-spinner-dots size="50px" color="primary" />
                                </q-inner-loading>
                            </template>

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
                                        class="animal-chip"
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
                                        <q-btn flat round size="sm" color="info" icon="visibility">
                                            <q-tooltip>View details</q-tooltip>
                                        </q-btn>
                                        <q-btn flat round size="sm" color="warning" icon="edit">
                                            <q-tooltip>Edit registration</q-tooltip>
                                        </q-btn>
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
import { ref, computed, onMounted, inject } from 'vue';
import { QCard, QCardSection, QTable, QImg, QBtn, QIcon, QBadge, QChip, QAvatar, QInput, QSelect, QTd, QTooltip, QSpinnerDots, QInnerLoading } from 'quasar';
import axios from 'axios';
import { Notify } from 'quasar';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import '../../css/registered-pets.css';

// Get the global dark mode state from the AuthenticatedLayout
const isDarkMode = inject('isDarkMode', ref(false));

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
const user = ref({ name: 'User' }); // Added user data reference

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
    if (typeLower === 'dog') return '#38a3a5';
    if (typeLower === 'cat') return '#57cc99';
    return '#4f6642';
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

    // Fetch current user data
    try {
        axios.get('/api/user').then(response => {
            if (response.data) {
                user.value = response.data;
            }
        });
    } catch (error) {
        console.error('Error fetching user data:', error);
    }
});
</script>

<style>
/* Component styles are now in the dedicated CSS file */
</style>
