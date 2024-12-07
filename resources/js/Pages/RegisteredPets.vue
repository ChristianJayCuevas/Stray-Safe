<script setup>
import { ref, onMounted } from 'vue';
import { QCard, QCardSection, QTable, QImg, QBtn } from 'quasar';
import axios from 'axios';
import { Notify } from 'quasar';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';

// Set the default Axios authorization header
axios.defaults.headers.common['Authorization'] = 'Bearer StraySafeTeam3';

// Data references
const registeredAnimals = ref([]);
const totalRegistered = ref(0);
const registeredToday = ref(0);

// Fetch registered animals
async function fetchRegisteredAnimals() {
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
      status: animal.status || 'N/A',
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
  }
}

// Fetch data when component is mounted
onMounted(() => {
  fetchRegisteredAnimals();
});
</script>

<template>
    <AuthenticatedLayout>
        <q-card class="registered-animals-card mt-5 mx-10">
            <q-card-section>
                <h3 class="text-2xl font-bold mb-4">Registered Animals</h3>

                <!-- Statistics -->
                <div class="grid grid-cols-2 gap-6 mb-6">
                    <div class="info-card">
                        <h3 class="text-lg font-semibold">Total Registered Animals</h3>
                        <p class="text-4xl font-bold text-primary">{{ totalRegistered }}</p>
                    </div>
                    <div class="info-card">
                        <h3 class="text-lg font-semibold">Registered Today</h3>
                        <p class="text-4xl font-bold text-primary">{{ registeredToday }}</p>
                    </div>
                </div>

                <!-- Registered Animals Table -->
                <q-table
                    :rows="registeredAnimals"
                    :columns="[ 
                        { name: 'date', label: 'Time/Date', field: 'date', align: 'left' },
                        { name: 'owner', label: 'Owner', field: 'owner', align: 'left' },
                        { name: 'contact', label: 'Contact Number', field: 'contact', align: 'left' },
                        { name: 'animal_type', label: 'Animal Type', field: 'animal_type', align: 'left' },
                        { name: 'picture', label: 'Picture', field: 'picture', align: 'center' },
                        { name: 'status', label: 'Status', field: 'status', align: 'center' }
                    ]"
                    row-key="id"
                    no-data-label="No registered animals to display."
                >
                    <template v-slot:body-cell-picture="props">
                        <q-img
                            :src="props.row.picture"
                            style="width: 80px; height: 80px; object-fit: cover;"
                            :alt="props.row.owner"
                        />
                    </template>
                </q-table>
            </q-card-section>
        </q-card>
    </AuthenticatedLayout>
</template>

<style scoped>
.registered-animals-card {
  box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
  background-color: white;
  border-radius: 8px;
  overflow: hidden;
}
.info-card {
  padding: 20px;
  text-align: center;
  background: white;
  border: 1px solid #ccc;
  border-radius: 8px;
}
</style>
