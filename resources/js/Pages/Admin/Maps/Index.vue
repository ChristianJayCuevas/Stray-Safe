<script setup>
import { ref, onMounted } from 'vue';
import { Head, Link } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import { 
  QCard, 
  QCardSection, 
  QTabs, 
  QTab, 
  QTabPanels, 
  QTabPanel, 
  QTable, 
  QTr, 
  QTd, 
  QBtn, 
  QIcon, 
  QBadge, 
  useQuasar,
  QInput,
  QSelect,
  QDialog,
  QForm,
  QSpace
} from 'quasar';
import axios from 'axios';

const $q = useQuasar();
const tab = ref('all-maps');
const maps = ref([]);
const isLoading = ref(false);
const errorMessage = ref('');
const selectedMap = ref(null);
const showMapDetailsDialog = ref(false);
const filter = ref('');

// Column definitions for the maps table
const columns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true },
  { name: 'name', label: 'Map Name', field: 'name', sortable: true },
  { name: 'owner', label: 'Owner', field: row => row.owner ? row.owner.name : 'Unknown', sortable: true },
  { name: 'access_code', label: 'Access Code', field: 'access_code' },
  { name: 'public', label: 'Public', field: 'is_public', sortable: true },
  { name: 'created_at', label: 'Created', field: 'created_at', sortable: true, format: val => new Date(val).toLocaleString() },
  { name: 'actions', label: 'Actions', field: 'actions' }
];

// Function to fetch maps from the backend
const fetchMaps = async () => {
  isLoading.value = true;
  errorMessage.value = '';
  
  try {
    const response = await axios.get(route('admin.maps.data'));
    
    if (response.data.success) {
      maps.value = response.data.maps || [];
      console.log('Maps loaded:', maps.value);
    } else {
      errorMessage.value = response.data.message || 'Failed to load maps';
    }
  } catch (error) {
    console.error('Error fetching maps:', error);
    errorMessage.value = error.response?.data?.message || 'An error occurred while loading maps';
  } finally {
    isLoading.value = false;
  }
};

// View map details
const viewMapDetails = (map) => {
  selectedMap.value = map;
  showMapDetailsDialog.value = true;
};

// Copy access code to clipboard
const copyAccessCode = (code) => {
  navigator.clipboard.writeText(code).then(() => {
    $q.notify({
      message: 'Access code copied to clipboard',
      color: 'positive',
      position: 'top',
      timeout: 1500
    });
  }, (err) => {
    console.error('Could not copy access code:', err);
    $q.notify({
      message: 'Failed to copy access code',
      color: 'negative',
      position: 'top'
    });
  });
};

// Format date
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString();
};

// Delete map
const confirmDeleteMap = (map) => {
  $q.dialog({
    title: 'Confirm Deletion',
    message: `Are you sure you want to delete the map "${map.name}"? This action cannot be undone and will remove all pins associated with this map.`,
    cancel: true,
    persistent: true
  }).onOk(() => {
    deleteMap(map.id);
  });
};

// Delete map logic
const deleteMap = async (mapId) => {
  try {
    const response = await axios.delete(route('user-maps.destroy', mapId));
    
    if (response.data.success) {
      $q.notify({
        message: 'Map deleted successfully',
        color: 'positive',
        position: 'top'
      });
      // Refresh the maps list
      fetchMaps();
      // Close dialog if it's open
      if (showMapDetailsDialog.value) {
        showMapDetailsDialog.value = false;
      }
    } else {
      $q.notify({
        message: response.data.message || 'Failed to delete map',
        color: 'negative',
        position: 'top'
      });
    }
  } catch (error) {
    console.error('Error deleting map:', error);
    $q.notify({
      message: error.response?.data?.message || 'An error occurred while deleting the map',
      color: 'negative',
      position: 'top'
    });
  }
};

// Regenerate access code
const regenerateAccessCode = async (mapId) => {
  try {
    const response = await axios.post(route('user-maps.regenerate-code', mapId));
    
    if (response.data.success) {
      $q.notify({
        message: 'Access code regenerated successfully',
        color: 'positive',
        position: 'top'
      });
      
      // Update the access code in the local state
      if (selectedMap.value && selectedMap.value.id === mapId) {
        selectedMap.value.access_code = response.data.access_code;
      }
      
      // Refresh the maps list
      fetchMaps();
    } else {
      $q.notify({
        message: response.data.message || 'Failed to regenerate access code',
        color: 'negative',
        position: 'top'
      });
    }
  } catch (error) {
    console.error('Error regenerating access code:', error);
    $q.notify({
      message: error.response?.data?.message || 'An error occurred while regenerating the access code',
      color: 'negative',
      position: 'top'
    });
  }
};

// Toggle public status
const togglePublicStatus = async (map) => {
  try {
    const response = await axios.put(route('user-maps.update', map.id), {
      is_public: !map.is_public
    });
    
    if (response.data.success) {
      $q.notify({
        message: `Map is now ${!map.is_public ? 'public' : 'private'}`,
        color: 'positive',
        position: 'top'
      });
      
      // Update the public status in the local state
      if (selectedMap.value && selectedMap.value.id === map.id) {
        selectedMap.value.is_public = !map.is_public;
      }
      
      // Refresh the maps list
      fetchMaps();
    } else {
      $q.notify({
        message: response.data.message || 'Failed to update map status',
        color: 'negative',
        position: 'top'
      });
    }
  } catch (error) {
    console.error('Error updating map status:', error);
    $q.notify({
      message: error.response?.data?.message || 'An error occurred while updating the map status',
      color: 'negative',
      position: 'top'
    });
  }
};

// Load maps on mount
onMounted(() => {
  fetchMaps();
});
</script>

<template>
  <Head title="Map Management" />

  <AuthenticatedLayout>
    <template #header>
      <h2 class="font-semibold text-xl text-gray-800 leading-tight dark:text-white">Map Management</h2>
    </template>

    <div class="py-12">
      <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
        <QCard flat bordered class="q-mb-md">
          <QCardSection>
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold dark:text-white">User Maps</h3>
              <QInput v-model="filter" dense outlined placeholder="Search maps..." class="w-64 dark-search-input">
                <template v-slot:append>
                  <QIcon name="search" />
                </template>
              </QInput>
            </div>
          </QCardSection>
          
          <QCardSection>
            <QTabs
              v-model="tab"
              dense
              class="text-grey dark:text-gray-300"
              active-color="primary"
              indicator-color="primary"
              align="left"
            >
              <QTab name="all-maps" label="All Maps" />
              <QTab name="public-maps" label="Public Maps" />
              <QTab name="private-maps" label="Private Maps" />
            </QTabs>

            <QTabPanels v-model="tab" animated>
              <QTabPanel name="all-maps">
                <div v-if="isLoading" class="text-center py-4">
                  <q-spinner color="primary" size="3em" />
                  <p class="mt-2 dark:text-gray-300">Loading maps...</p>
                </div>
                
                <div v-else-if="errorMessage" class="text-center py-4 text-red-500">
                  {{ errorMessage }}
                </div>
                
                <div v-else-if="maps.length === 0" class="text-center py-4">
                  <p class="text-gray-500 dark:text-gray-400">No maps found</p>
                </div>
                
                <QTable
                  v-else
                  :rows="maps"
                  :columns="columns"
                  row-key="id"
                  :filter="filter"
                  :loading="isLoading"
                  class="map-table"
                  :dark="$q.dark.isActive"
                >
                  <template v-slot:body="props">
                    <QTr :props="props">
                      <QTd key="id" :props="props">
                        {{ props.row.id }}
                      </QTd>
                      <QTd key="name" :props="props">
                        {{ props.row.name }}
                      </QTd>
                      <QTd key="owner" :props="props">
                        {{ props.row.owner ? props.row.owner.name : 'Unknown' }}
                      </QTd>
                      <QTd key="access_code" :props="props">
                        <div class="flex items-center">
                          <span class="font-mono mr-2">{{ props.row.access_code }}</span>
                          <QBtn flat size="sm" icon="content_copy" @click.stop="copyAccessCode(props.row.access_code)" class="text-primary dark:text-blue-400">
                            <QTooltip>Copy access code</QTooltip>
                          </QBtn>
                        </div>
                      </QTd>
                      <QTd key="public" :props="props">
                        <QBadge :color="props.row.is_public ? 'green-8' : 'grey-8'" text-color="white">
                          {{ props.row.is_public ? 'Public' : 'Private' }}
                        </QBadge>
                      </QTd>
                      <QTd key="created_at" :props="props">
                        {{ formatDate(props.row.created_at) }}
                      </QTd>
                      <QTd key="actions" :props="props">
                        <div class="flex items-center space-x-2">
                          <QBtn size="sm" color="blue-8" icon="visibility" @click.stop="viewMapDetails(props.row)" class="action-btn" flat label="View" />
                          <QBtn size="sm" color="amber-8" icon="vpn_key" @click.stop="regenerateAccessCode(props.row.id)" class="action-btn" flat label="Regen" />
                          <QBtn size="sm" :color="props.row.is_public ? 'grey-8' : 'green-8'" :icon="props.row.is_public ? 'lock' : 'public'" @click.stop="togglePublicStatus(props.row)" class="action-btn" flat :label="props.row.is_public ? 'Private' : 'Public'" />
                          <QBtn size="sm" color="red-8" icon="delete" @click.stop="confirmDeleteMap(props.row)" class="action-btn" flat label="Delete" />
                        </div>
                      </QTd>
                    </QTr>
                  </template>
                </QTable>
              </QTabPanel>
              
              <QTabPanel name="public-maps">
                <QTable
                  :rows="maps.filter(map => map.is_public)"
                  :columns="columns"
                  row-key="id"
                  :filter="filter"
                  :loading="isLoading"
                  class="map-table"
                  :dark="$q.dark.isActive"
                >
                  <!-- Same template as all-maps tab -->
                  <template v-slot:body="props">
                    <QTr :props="props">
                      <QTd key="id" :props="props">
                        {{ props.row.id }}
                      </QTd>
                      <QTd key="name" :props="props">
                        {{ props.row.name }}
                      </QTd>
                      <QTd key="owner" :props="props">
                        {{ props.row.owner ? props.row.owner.name : 'Unknown' }}
                      </QTd>
                      <QTd key="access_code" :props="props">
                        <div class="flex items-center">
                          <span class="font-mono mr-2">{{ props.row.access_code }}</span>
                          <QBtn flat size="sm" icon="content_copy" @click.stop="copyAccessCode(props.row.access_code)" class="text-primary dark:text-blue-400">
                            <QTooltip>Copy access code</QTooltip>
                          </QBtn>
                        </div>
                      </QTd>
                      <QTd key="public" :props="props">
                        <QBadge color="green-8" text-color="white">
                          Public
                        </QBadge>
                      </QTd>
                      <QTd key="created_at" :props="props">
                        {{ formatDate(props.row.created_at) }}
                      </QTd>
                      <QTd key="actions" :props="props">
                        <div class="flex items-center space-x-2">
                          <QBtn size="sm" color="blue-8" icon="visibility" @click.stop="viewMapDetails(props.row)" class="action-btn" flat label="View" />
                          <QBtn size="sm" color="amber-8" icon="vpn_key" @click.stop="regenerateAccessCode(props.row.id)" class="action-btn" flat label="Regen" />
                          <QBtn size="sm" color="grey-8" icon="lock" @click.stop="togglePublicStatus(props.row)" class="action-btn" flat label="Private" />
                          <QBtn size="sm" color="red-8" icon="delete" @click.stop="confirmDeleteMap(props.row)" class="action-btn" flat label="Delete" />
                        </div>
                      </QTd>
                    </QTr>
                  </template>
                </QTable>
              </QTabPanel>
              
              <QTabPanel name="private-maps">
                <QTable
                  :rows="maps.filter(map => !map.is_public)"
                  :columns="columns"
                  row-key="id"
                  :filter="filter"
                  :loading="isLoading"
                  class="map-table"
                  :dark="$q.dark.isActive"
                >
                  <!-- Same template as all-maps tab -->
                  <template v-slot:body="props">
                    <QTr :props="props">
                      <QTd key="id" :props="props">
                        {{ props.row.id }}
                      </QTd>
                      <QTd key="name" :props="props">
                        {{ props.row.name }}
                      </QTd>
                      <QTd key="owner" :props="props">
                        {{ props.row.owner ? props.row.owner.name : 'Unknown' }}
                      </QTd>
                      <QTd key="access_code" :props="props">
                        <div class="flex items-center">
                          <span class="font-mono mr-2">{{ props.row.access_code }}</span>
                          <QBtn flat size="sm" icon="content_copy" @click.stop="copyAccessCode(props.row.access_code)" class="text-primary dark:text-blue-400">
                            <QTooltip>Copy access code</QTooltip>
                          </QBtn>
                        </div>
                      </QTd>
                      <QTd key="public" :props="props">
                        <QBadge color="grey-8" text-color="white">
                          Private
                        </QBadge>
                      </QTd>
                      <QTd key="created_at" :props="props">
                        {{ formatDate(props.row.created_at) }}
                      </QTd>
                      <QTd key="actions" :props="props">
                        <div class="flex items-center space-x-2">
                          <QBtn size="sm" color="blue-8" icon="visibility" @click.stop="viewMapDetails(props.row)" class="action-btn" flat label="View" />
                          <QBtn size="sm" color="amber-8" icon="vpn_key" @click.stop="regenerateAccessCode(props.row.id)" class="action-btn" flat label="Regen" />
                          <QBtn size="sm" color="green-8" icon="public" @click.stop="togglePublicStatus(props.row)" class="action-btn" flat label="Public" />
                          <QBtn size="sm" color="red-8" icon="delete" @click.stop="confirmDeleteMap(props.row)" class="action-btn" flat label="Delete" />
                        </div>
                      </QTd>
                    </QTr>
                  </template>
                </QTable>
              </QTabPanel>
            </QTabPanels>
          </QCardSection>
        </QCard>
      </div>
    </div>
    
    <!-- Map Details Dialog -->
    <QDialog v-model="showMapDetailsDialog" persistent>
      <QCard style="min-width: 500px" :dark="$q.dark.isActive" class="map-detail-card">
        <QCardSection class="row items-center q-pb-none">
          <div class="text-h6 dark:text-white">Map Details</div>
          <QSpace />
          <QBtn icon="close" flat round dense v-close-popup />
        </QCardSection>

        <QCardSection v-if="selectedMap">
          <div class="q-gutter-y-md">
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Name</div>
              <div class="dark:text-white">{{ selectedMap.name }}</div>
            </div>
            
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Description</div>
              <div class="dark:text-white">{{ selectedMap.description || 'No description provided' }}</div>
            </div>
            
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Access Code</div>
              <div class="flex items-center">
                <span class="font-mono mr-2 dark:text-white">{{ selectedMap.access_code }}</span>
                <QBtn flat size="sm" icon="content_copy" @click="copyAccessCode(selectedMap.access_code)" class="text-primary dark:text-blue-400 action-btn" label="Copy" />
                <QBtn 
                  size="sm" 
                  color="amber-8" 
                  flat 
                  class="ml-2 action-btn"
                  icon="vpn_key" 
                  @click="regenerateAccessCode(selectedMap.id)"
                  label="Regenerate"
                />
              </div>
            </div>
            
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Visibility</div>
              <div class="flex items-center">
                <QBadge :color="selectedMap.is_public ? 'green-8' : 'grey-8'" text-color="white" class="mr-2">
                  {{ selectedMap.is_public ? 'Public' : 'Private' }}
                </QBadge>
                <QBtn 
                  size="sm" 
                  :color="selectedMap.is_public ? 'grey-8' : 'green-8'" 
                  flat
                  :icon="selectedMap.is_public ? 'lock' : 'public'" 
                  @click="togglePublicStatus(selectedMap)"
                  :label="selectedMap.is_public ? 'Make Private' : 'Make Public'"
                  class="action-btn"
                />
              </div>
            </div>
            
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Owner</div>
              <div class="dark:text-white">{{ selectedMap.owner ? selectedMap.owner.name : 'Unknown' }}</div>
            </div>
            
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Created</div>
              <div class="dark:text-white">{{ formatDate(selectedMap.created_at) }}</div>
            </div>
            
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Last Updated</div>
              <div class="dark:text-white">{{ formatDate(selectedMap.updated_at) }}</div>
            </div>
            
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Default View</div>
              <div v-if="selectedMap.default_view" class="dark:text-white">
                <div>Center: {{ selectedMap.default_view.center ? selectedMap.default_view.center.join(', ') : 'Not set' }}</div>
                <div>Zoom: {{ selectedMap.default_view.zoom || 'Not set' }}</div>
              </div>
              <div v-else class="dark:text-white">No default view set</div>
            </div>
            
            <div>
              <div class="text-subtitle2 dark:text-gray-300">Pins</div>
              <div class="dark:text-white">{{ selectedMap.pins ? selectedMap.pins.length : 0 }} pins on this map</div>
            </div>
          </div>
        </QCardSection>

        <QCardSection class="row justify-end q-gutter-sm">
          <QBtn flat label="Close" color="blue-8" v-close-popup class="action-btn" />
          <QBtn
            flat
            label="Delete Map"
            color="red-8"
            @click="confirmDeleteMap(selectedMap); showMapDetailsDialog = false"
            class="action-btn"
          />
        </QCardSection>
      </QCard>
    </QDialog>
  </AuthenticatedLayout>
</template>

<style scoped>
/* Add styles for dark mode compatibility */
.map-table {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.q-table--dark) {
  background-color: #2d2d2d;
}

:deep(.q-table--dark th) {
  background-color: #1d1d1d;
  color: #e0e0e0;
}

:deep(.q-table--dark td) {
  color: #e0e0e0;
}

:deep(.q-table--dark tbody tr:hover) {
  background-color: rgba(255, 255, 255, 0.07);
}

.action-btn {
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-radius: 4px !important;
  padding: 0 8px !important;
  min-height: 32px;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.action-btn .q-icon {
  margin-right: 4px;
}

.action-btn.q-btn--flat {
  background-color: rgba(0, 0, 0, 0.05) !important;
}

:deep(.dark) .action-btn.q-btn--flat {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.map-detail-card {
  border-radius: 8px;
}

:deep(.dark) .map-detail-card {
  background-color: #1d1d1d;
  color: #ffffff;
}

:deep(.dark-search-input) .q-field__native,
:deep(.dark-search-input) .q-field__prefix,
:deep(.dark-search-input) .q-field__suffix,
:deep(.dark-search-input) .q-field__input {
  color: white !important;
}

:deep(.dark) .q-field__control {
  background: #2d2d2d;
}
</style> 