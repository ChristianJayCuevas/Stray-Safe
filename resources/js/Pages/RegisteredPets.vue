<script setup>
import { ref, onMounted } from 'vue';
import { QCard, QCardSection, QTable, QImg, QDialog, QInput, QSelect, QBtn, useQuasar } from 'quasar';
import axios from 'axios';
import { Head } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';

//FilePond imports for multiple file upload
import vueFilePond from "vue-filepond";
import FilePondPluginImagePreview from "filepond-plugin-image-preview";
import 'filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css';
import 'filepond/dist/filepond.min.css';

//Create an Instance of FilePond
const FilePond = vueFilePond(FilePondPluginImagePreview);
import { Notify } from 'quasar';

// Notify Example

const $q = useQuasar();
const registeredAnimals = ref([]);
const totalRegistered = ref(0);
const registeredToday = ref(0);
const createDialog = ref(false);
const editDialog = ref(false); // Separate dialog for editing

const createFormData = ref({
    owner: '',
    contact: '',
    animal_type: 'dog',
    image_url: [], // Array to store temporary folder identifiers
    status: 'free',
});

// Error message for form validation
const errorMessage = ref("");

// FilePond Handlers
function handleFilePondLoad(response) {
    createFormData.value.image_url.push(response); // Add folder ID to form data
    return response;
}

function handleFilePondRevert(uniqueId, load) {
    // Remove folder ID from form data and send DELETE request to revert endpoint
    createFormData.value.image_url = createFormData.value.image_url.filter((image) => image !== uniqueId);
    axios.delete(`/revert/${uniqueId}`)
        .then(() => load())
        .catch(console.error);
}

// Form Submission Handler
const submit = () => {
    errorMessage.value = ""; // Clear any previous error messages

    // Validate required fields
    if (!createFormData.value.owner || !createFormData.value.contact || createFormData.value.image_url.length === 0) {
        errorMessage.value = "Owner, Contact, and at least one Image are required.";
        return;
    }

    // Send form data to the backend
    axios.post('/api/registered-animals', createFormData.value)
        .then((response) => {
            console.log("Form submitted successfully:", response.data);
            Notify.create({
            type: 'positive',
            message: 'Animal registered successfully!',
        });
            createDialog.value = false;
            fetchRegisteredAnimals();
        })
        .catch((error) => {
            console.error("Form submission error:", error);
            errorMessage.value = "An error occurred while submitting the form.";
        });
};

// Fetch registered animals
async function fetchRegisteredAnimals() {
    try {
        const response = await axios.get('/api/registered-animals');
        console.log('API Response:', response.data);

        registeredAnimals.value = response.data.animals.map(animal => ({
            date: new Date(animal.created_at).toLocaleString(), // Format date
            owner: animal.owner || 'Unknown',
            contact: animal.contact || 'N/A',
            animal_type: animal.animal_type || 'N/A',
            picture: animal.picture ? `/storage/${animal.picture}` : null, // Handle null pictures
            status: animal.status || 'N/A',
            id: animal.id,
        }));
        console.log('Mapped Data:', registeredAnimals.value); // Log the mapped data
        totalRegistered.value = response.data.total || 0;
        registeredToday.value = response.data.today || 0;
    } catch (error) {
        console.error('Error fetching registered animals:', error);
    }
}



// Open dialog for creating a new entry
function openCreateDialog() {
    createFormData.value = {
        owner: '',
        contact: '',
        animal_type: 'dog',
        image_url: [],
        status: 'free',
    };
    createDialog.value = true;
}
function openEditDialog(animal) {
    console.log('Editing animal:', animal);
    if (animal && typeof animal === 'object' && 'id' in animal) {
        editFormData.value = { ...animal }; // Populate edit form data
        editDialog.value = true; // Open the edit dialog
    } else {
        console.error('Invalid animal data for editing:', animal);
    }
}

async function deleteAnimal(id) {
    try {
        await axios.delete(`/api/registered-animals/${id}`);
        Notify.create({
            type: 'positive',
            message: 'Animal deleted successfully!',
        });
        fetchRegisteredAnimals();
    } catch (error) {
        console.error('Error deleting animal:', error);
        Notify.create({
            type: 'negative',
            message: 'Failed to delete animal.',
        });
    }
}



onMounted(() => {
    fetchRegisteredAnimals();
});

</script>

<template>
    <AuthenticatedLayout>
        <Head title="Registered Animals" />

        <q-card class="registered-animals-card mt-5 mx-10">
            <q-card-section>
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-2xl font-bold">Registered Animals</h3>
                    <q-btn label="Create+" color="primary" @click="openCreateDialog" />
                </div>

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
        { name: 'status', label: 'Status', field: 'status', align: 'center' },
        { name: 'actions', label: 'Actions', align: 'center' },
    ]"
    row-key="id"
    no-data-label="No registered animals to display."
>
<template v-slot:body-cell-picture="props">
    <q-img 
        :src="props.row.picture || 'https://via.placeholder.com/80'" 
        style="width: 80px; height: 80px; object-fit: cover;" 
        :alt="props.row.owner"
    />
</template>

    <template v-slot:body-cell-actions="props">
        <q-btn icon="edit" color="blue" @click="openEditDialog(props.row)" />
        <q-btn icon="delete" color="red" @click="deleteAnimal(props.row.id)" />
    </template>
</q-table>

            </q-card-section>
        </q-card>

        <!-- Dialog for Creating New Animal -->
        <q-dialog v-model="createDialog">
    <q-card class="modal">
        <q-card-section>
            <h3 class="text-lg font-semibold">Register Animal</h3>
        </q-card-section>
        <q-card-section>
            <q-input v-model="createFormData.owner" label="Owner" outlined />
            <q-input v-model="createFormData.contact" label="Contact Number" outlined />
            <q-select v-model="createFormData.animal_type" :options="['dog', 'cat']" label="Animal Type" outlined />
            <label class="block mt-4 mb-2 font-medium">Upload Images</label>
            <file-pond 
                        name="image"
                        ref="pond"
                        class-name="my-pond"
                        label-idle="Drop files here or click to upload"
                        allow-multiple="true"
                        credits="false"
                        accepted-file-types="image/jpeg, image/png"
                        :server="{
                            url:'',
                            process: {
                                url:'/upload-image',
                                method: 'POST',
                                onload: handleFilePondLoad
                            },
                            revert: handleFilePondRevert,
                            headers:{
                                'X-CSRF-TOKEN': $page.props.csrf_token
                            }
            
                        }"
                    ></file-pond>
            <q-select v-model="createFormData.status" :options="['caught', 'free', 'claimed']" label="Status" outlined />
        </q-card-section>
        <q-card-section>
            <p class="text-red-500">{{ errorMessage }}</p>
            <q-btn 
                label="Save" 
                color="green" 
                @click="submit" 
            />
            <q-btn label="Cancel" color="red" flat @click="createDialog = false" />
        </q-card-section>
    </q-card>
</q-dialog>


        <!-- Dialog for Editing Existing Animal -->
        <q-dialog v-model="editDialog">
            <q-card class="modal">
                <q-card-section>
                    <h3 class="text-lg font-semibold">Edit Animal</h3>
                </q-card-section>
                <q-card-section>
                    <q-input v-model="editFormData.owner" label="Owner" outlined />
                    <q-input v-model="editFormData.contact" label="Contact Number" outlined />
                    <q-select v-model="editFormData.animal_type" :options="['dog', 'cat']" label="Animal Type" outlined />
                    <q-input v-model="editFormData.picture" label="Picture URL" outlined />
                    <q-select v-model="editFormData.status" :options="['caught', 'free', 'claimed']" label="Status" outlined />
                </q-card-section>
                <q-card-section>
                    <q-btn 
                        label="Save" 
                        color="green" 
                        @click="handleEditSave" 
                    />
                    <q-btn label="Cancel" color="red" flat @click="editDialog = false" />
                </q-card-section>
            </q-card>
        </q-dialog>
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
}
.modal{
    max-width: 100%;
    max-height: 100%;
    width: 80vw;
    height: auto;
}
</style>
