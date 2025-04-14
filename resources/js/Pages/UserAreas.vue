<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { Head, Link } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import axios from 'axios';
import { QSpinnerGears } from 'quasar';
import { useQuasar } from 'quasar';

// Map libraries
import MapComponent from '@/Components/MapComponent.vue';

const $q = useQuasar();
const userAreas = ref([]);
const loading = ref(false);
const selectedArea = ref(null);
const editDialog = ref(false);
const createDialog = ref(false);
const mapComponentRef = ref(null);
const drawingMode = ref(false);
const mapReady = ref(false);

const newArea = ref({
  name: '',
  description: '',
  geometry: null,
  properties: {}
});

const drawnFeature = ref(null);

const fetchUserAreas = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/user-areas');
    userAreas.value = response.data;
    console.log('User areas fetched:', response.data);
  } catch (error) {
    console.error('Error fetching user areas:', error);
    $q.notify({
      color: 'negative',
      message: 'Failed to load user areas',
      icon: 'error'
    });
  } finally {
    loading.value = false;
  }
};

const deleteArea = async (areaId) => {
  $q.dialog({
    title: 'Confirm Deletion',
    message: 'Are you sure you want to delete this area?',
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      await axios.delete(`/api/user-areas/${areaId}`);
      $q.notify({
        color: 'positive',
        message: 'Area deleted successfully',
        icon: 'check_circle'
      });
      fetchUserAreas();
      
      // If map is initialized, also remove from the map
      if (mapComponentRef.value && mapComponentRef.value.removeFeature) {
        mapComponentRef.value.removeFeature(areaId);
      }
    } catch (error) {
      console.error('Error deleting area:', error);
      $q.notify({
        color: 'negative',
        message: 'Failed to delete area',
        icon: 'error'
      });
    }
  });
};

const editArea = (area) => {
  selectedArea.value = area;
  newArea.value = {
    name: area.name || '',
    description: area.description || '',
  };
  editDialog.value = true;
};

const saveArea = async () => {
  if (!selectedArea.value) return;
  
  try {
    const updatedArea = {
      name: newArea.value.name,
      description: newArea.value.description,
      geometry: selectedArea.value.geometry,
      properties: selectedArea.value.properties
    };
    
    await axios.put(`/api/user-areas/${selectedArea.value.feature_id}`, updatedArea);
    $q.notify({
      color: 'positive',
      message: 'Area updated successfully',
      icon: 'check_circle'
    });
    editDialog.value = false;
    fetchUserAreas();
    
    // Update area on the map
    if (mapComponentRef.value && mapComponentRef.value.updateAreaProperties) {
      mapComponentRef.value.updateAreaProperties(selectedArea.value.feature_id, {
        name: newArea.value.name,
        description: newArea.value.description
      });
    }
  } catch (error) {
    console.error('Error updating area:', error);
    $q.notify({
      color: 'negative',
      message: 'Failed to update area',
      icon: 'error'
    });
  }
};

const startDrawing = () => {
  if (!mapComponentRef.value || !mapComponentRef.value.enableDrawingMode) {
    $q.notify({
      color: 'negative',
      message: 'Map is not ready yet. Please try again.',
      icon: 'error'
    });
    return;
  }
  
  drawingMode.value = true;
  $q.notify({
    color: 'info',
    message: 'Draw mode activated. Click on the map to start drawing an area.',
    icon: 'edit',
    timeout: 3000
  });
  
  mapComponentRef.value.enableDrawingMode('polygon');
};

const onDrawComplete = (feature) => {
  drawingMode.value = false;
  drawnFeature.value = feature;
  createDialog.value = true;
  
  newArea.value = {
    name: '',
    description: '',
    geometry: feature.geometry,
    properties: feature.properties || {}
  };
};

const saveNewArea = async () => {
  if (!drawnFeature.value) {
    $q.notify({
      color: 'negative',
      message: 'No area drawn. Please draw an area first.',
      icon: 'error'
    });
    return;
  }
  
  try {
    const areaData = {
      feature_id: `user-area-${Date.now()}`,
      name: newArea.value.name,
      description: newArea.value.description,
      geometry: JSON.stringify(drawnFeature.value.geometry),
      properties: JSON.stringify({
        ...drawnFeature.value.properties,
        name: newArea.value.name,
        description: newArea.value.description
      })
    };
    
    const response = await axios.post('/api/user-areas', areaData);
    $q.notify({
      color: 'positive',
      message: 'Area created successfully',
      icon: 'check_circle'
    });
    
    createDialog.value = false;
    drawnFeature.value = null;
    fetchUserAreas();
  } catch (error) {
    console.error('Error creating area:', error);
    $q.notify({
      color: 'negative',
      message: 'Failed to create area: ' + (error.response?.data?.errors?.feature_id?.[0] || error.message),
      icon: 'error'
    });
  }
};

const cancelDrawing = () => {
  if (mapComponentRef.value && mapComponentRef.value.cancelDrawing) {
    mapComponentRef.value.cancelDrawing();
  }
  drawingMode.value = false;
  drawnFeature.value = null;
};

const highlightArea = (areaId) => {
  if (mapComponentRef.value && mapComponentRef.value.highlightFeature) {
    mapComponentRef.value.highlightFeature(areaId);
  }
};

const onMapReady = () => {
  mapReady.value = true;
  console.log('Map is ready to use');
};

onMounted(() => {
  fetchUserAreas();
});
</script>

<template>
  <Head title="User Areas" />

  <AuthenticatedLayout>
    <template #default>
      <div class="q-pa-md">
        <div class="text-3xl font-bold font-poppins">User Areas</div>
        <p class="text-subtitle1 q-mb-lg">Create and manage your custom defined areas on the map.</p>

        <div class="row q-col-gutter-md">
          <!-- Map section -->
          <div class="col-md-8 col-sm-12">
            <q-card class="map-card">
              <q-card-section class="q-pb-none">
                <div class="row items-center justify-between">
                  <div>
                    <div class="text-h6">Map</div>
                    <div class="text-caption">Draw areas on the map by using the drawing tools.</div>
                  </div>
                  <div>
                    <q-btn 
                      color="primary" 
                      icon="add" 
                      label="Create Area" 
                      :disable="drawingMode || !mapReady"
                      @click="startDrawing" 
                    />
                    <q-btn 
                      v-if="drawingMode" 
                      color="negative" 
                      icon="close" 
                      label="Cancel" 
                      class="q-ml-sm"
                      @click="cancelDrawing" 
                    />
                  </div>
                </div>
              </q-card-section>
              <q-card-section>
                <MapComponent 
                  ref="mapComponentRef"
                  class="user-areas-map" 
                  :user-areas="userAreas"
                  @map-ready="onMapReady"
                  @draw-complete="onDrawComplete"
                />
              </q-card-section>
              <q-card-section v-if="drawingMode" class="bg-blue-1">
                <div class="text-bold">Drawing Mode Active</div>
                <div class="text-caption">Click on the map to create points for your area. Double-click to complete.</div>
              </q-card-section>
            </q-card>
          </div>

          <!-- Area list section -->
          <div class="col-md-4 col-sm-12">
            <q-card>
              <q-card-section>
                <div class="text-h6">Your Areas</div>
                <div class="text-caption">You can manage your custom areas here.</div>
              </q-card-section>
              <q-card-section>
                <q-list separator>
                  <q-item v-if="loading">
                    <q-item-section>
                      <div class="text-center">
                        <q-spinner-gears color="primary" size="2em" />
                        <div class="q-mt-sm">Loading areas...</div>
                      </div>
                    </q-item-section>
                  </q-item>
                  <template v-else-if="userAreas.length > 0">
                    <q-item 
                      v-for="area in userAreas" 
                      :key="area.feature_id"
                      clickable
                      @click="highlightArea(area.feature_id)"
                      @mouseover="highlightArea(area.feature_id)"
                    >
                      <q-item-section>
                        <q-item-label>{{ area.name || 'Unnamed Area' }}</q-item-label>
                        <q-item-label caption>{{ area.description || 'No description' }}</q-item-label>
                      </q-item-section>
                      <q-item-section side>
                        <div class="row">
                          <q-btn flat round dense icon="edit" @click.stop="editArea(area)" />
                          <q-btn flat round dense icon="delete" color="negative" @click.stop="deleteArea(area.feature_id)" />
                        </div>
                      </q-item-section>
                    </q-item>
                  </template>
                  <q-item v-else>
                    <q-item-section>
                      <div class="text-center q-pa-md">
                        <q-icon name="info" size="2em" color="grey-7" />
                        <div class="q-mt-sm">No areas found. Click "Create Area" to get started.</div>
                      </div>
                    </q-item-section>
                  </q-item>
                </q-list>
              </q-card-section>
            </q-card>
          </div>
        </div>
      </div>

      <q-dialog v-model="editDialog">
        <q-card style="min-width: 350px">
          <q-card-section>
            <div class="text-h6">Edit Area</div>
          </q-card-section>

          <q-card-section>
            <q-input v-model="newArea.name" label="Area Name" dense />
            <q-input v-model="newArea.description" label="Description" type="textarea" dense class="q-mt-md" />
          </q-card-section>

          <q-card-actions align="right">
            <q-btn flat label="Cancel" color="negative" v-close-popup />
            <q-btn flat label="Save" color="primary" @click="saveArea" />
          </q-card-actions>
        </q-card>
      </q-dialog>

      <!-- Create Area Dialog -->
      <q-dialog v-model="createDialog">
        <q-card style="min-width: 350px">
          <q-card-section>
            <div class="text-h6">Create New Area</div>
          </q-card-section>

          <q-card-section>
            <q-input 
              v-model="newArea.name" 
              label="Area Name" 
              hint="Give your area a descriptive name"
              dense 
              :rules="[val => !!val || 'Name is required']"
            />
            <q-input 
              v-model="newArea.description" 
              label="Description" 
              type="textarea" 
              hint="Add details about this area (optional)"
              dense 
              class="q-mt-md" 
            />
          </q-card-section>

          <q-card-actions align="right">
            <q-btn flat label="Cancel" color="negative" v-close-popup @click="cancelDrawing" />
            <q-btn flat label="Save Area" color="primary" @click="saveNewArea" />
          </q-card-actions>
        </q-card>
      </q-dialog>
    </template>
  </AuthenticatedLayout>
</template>

<style scoped>
.map-card {
  min-height: 700px;
}

.user-areas-map {
  height: 600px;
  width: 100%;
}
</style> 