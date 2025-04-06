<template>
    <AuthenticatedLayout>
        <Head title="Referral Code Management" />

        <div class="cctv-monitor-container px-6 py-4">
            <!-- Header Section -->
            <div class="page-header mb-6">
                <div class="flex justify-between items-center">
                    <div class="header-title">
                        <h1 class="text-3xl font-bold">Referral Code Management</h1>
                        <p class="text-secondary">Generate and track referral codes</p>
                    </div>
                    <q-btn 
                        color="primary" 
                        label="Generate Code" 
                        icon="add"
                        @click="showGenerateModal = true" 
                    />
                </div>
            </div>

            <!-- Statistics Cards -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <q-card flat bordered class="stat-card">
                    <q-card-section>
                        <div class="flex items-center">
                            <div class="stat-icon mr-4">
                                <i class="fas fa-ticket-alt"></i>
                            </div>
                            <div>
                                <div class="text-2xl font-bold">{{ totalCodes }}</div>
                                <div class="text-sm text-secondary">Total Codes</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section>
                        <div class="flex items-center">
                            <div class="stat-icon mr-4">
                                <i class="fas fa-check-circle"></i>
                            </div>
                            <div>
                                <div class="text-2xl font-bold">{{ activeCodes }}</div>
                                <div class="text-sm text-secondary">Active Codes</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section>
                        <div class="flex items-center">
                            <div class="stat-icon mr-4">
                                <i class="fas fa-users"></i>
                            </div>
                            <div>
                                <div class="text-2xl font-bold">{{ totalRedemptions }}</div>
                                <div class="text-sm text-secondary">Total Redemptions</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section>
                        <div class="flex items-center">
                            <div class="stat-icon mr-4">
                                <i class="fas fa-calendar-alt"></i>
                            </div>
                            <div>
                                <div class="text-2xl font-bold">{{ redemptionsThisMonth }}</div>
                                <div class="text-sm text-secondary">This Month</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
            </div>
            
            <!-- Referral Codes -->
            <q-card flat bordered class="stat-card mb-6">
                <q-card-section class="q-py-sm bg-accent">
                    <h2 class="text-xl font-bold text-white">Referral Codes</h2>
                </q-card-section>
                
                <q-card-section>
                    <q-table
                        :rows="referralCodes"
                        :columns="columns"
                        row-key="id"
                        :pagination="{rowsPerPage: 10}"
                        :loading="loading"
                        flat
                        bordered
                    >
                        <template v-slot:body-cell-code="props">
                            <q-td :props="props">
                                <div class="flex items-center">
                                    <span class="code-font">{{ props.row.code }}</span>
                                    <q-btn flat round dense size="sm" icon="content_copy" @click="copyCode(props.row.code)" />
                                </div>
                            </q-td>
                        </template>
                        
                        <template v-slot:body-cell-status="props">
                            <q-td :props="props">
                                <q-badge :color="props.row.is_active ? 'positive' : 'negative'">
                                    {{ props.row.is_active ? 'Active' : 'Inactive' }}
                                </q-badge>
                            </q-td>
                        </template>
                        
                        <template v-slot:body-cell-expires_at="props">
                            <q-td :props="props">
                                {{ props.row.expires_at ? formatDate(props.row.expires_at) : 'Never' }}
                            </q-td>
                        </template>
                        
                        <template v-slot:body-cell-actions="props">
                            <q-td :props="props" class="text-center">
                                <q-btn flat round dense size="sm" color="primary" icon="edit" @click="editCode(props.row)" />
                                <q-btn flat round dense size="sm" color="warning" icon="refresh" @click="toggleStatus(props.row)" />
                                <q-btn flat round dense size="sm" color="negative" icon="delete" @click="deleteCode(props.row)" />
                            </q-td>
                        </template>
                    </q-table>
                </q-card-section>
            </q-card>
            
            <!-- Usage History -->
            <q-card flat bordered class="stat-card">
                <q-card-section class="q-py-sm bg-accent">
                    <h2 class="text-xl font-bold text-white">Recent Redemptions</h2>
                </q-card-section>
                
                <q-card-section>
                    <div v-if="redemptions.length === 0" class="text-center py-4 text-gray-500">
                        No redemptions yet
                    </div>
                    
                    <q-list v-else bordered separator>
                        <q-item v-for="redemption in redemptions" :key="redemption.id" class="redemption-item">
                            <q-item-section avatar>
                                <q-avatar>
                                    <img :src="redemption.user.avatar || 'https://via.placeholder.com/150'" />
                                </q-avatar>
                            </q-item-section>
                            
                            <q-item-section>
                                <q-item-label>{{ redemption.user.name }}</q-item-label>
                                <q-item-label caption>Used code: <span class="code-font">{{ redemption.code }}</span></q-item-label>
                            </q-item-section>
                            
                            <q-item-section side>
                                <q-item-label caption>{{ formatDate(redemption.created_at) }}</q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
            </q-card>
        </div>
        
        <!-- Generate Code Modal -->
        <q-dialog v-model="showGenerateModal" persistent>
            <q-card style="width: 500px; max-width: 90vw;">
                <q-card-section class="q-py-sm bg-accent">
                    <div class="text-xl font-bold text-white">Generate Referral Code</div>
                </q-card-section>
                
                <q-form @submit.prevent="generateCode">
                    <q-card-section>
                        <div class="q-gutter-md">
                            <q-input
                                v-model="newCode.description"
                                label="Description / Purpose"
                                filled
                                required
                            />
                            
                            <q-input
                                v-model="newCode.code"
                                label="Custom Code (Leave blank for auto-generation)"
                                filled
                                hint="Minimum 6 characters, alphanumeric only"
                            />
                            
                            <q-input
                                v-model="newCode.max_uses"
                                label="Maximum Uses (0 for unlimited)"
                                filled
                                type="number"
                                required
                            />
                            
                            <q-input
                                v-model="newCode.expires_at"
                                label="Expiration Date (Optional)"
                                filled
                                type="date"
                            />
                        </div>
                    </q-card-section>
                    
                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" color="negative" v-close-popup />
                        <q-btn type="submit" label="Generate" color="primary" />
                    </q-card-actions>
                </q-form>
            </q-card>
        </q-dialog>
        
        <!-- Edit Code Modal -->
        <q-dialog v-model="showEditModal" persistent>
            <q-card style="width: 500px; max-width: 90vw;">
                <q-card-section class="q-py-sm bg-accent">
                    <div class="text-xl font-bold text-white">Edit Referral Code</div>
                </q-card-section>
                
                <q-form @submit.prevent="updateCode">
                    <q-card-section>
                        <div class="q-gutter-md">
                            <q-input
                                v-model="editingCode.description"
                                label="Description / Purpose"
                                filled
                                required
                            />
                            
                            <q-input
                                v-model="editingCode.max_uses"
                                label="Maximum Uses (0 for unlimited)"
                                filled
                                type="number"
                                required
                            />
                            
                            <q-input
                                v-model="editingCode.expires_at"
                                label="Expiration Date (Optional)"
                                filled
                                type="date"
                            />
                            
                            <q-toggle
                                v-model="editingCode.is_active"
                                label="Code is active"
                            />
                        </div>
                    </q-card-section>
                    
                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" color="negative" v-close-popup />
                        <q-btn type="submit" label="Update" color="primary" />
                    </q-card-actions>
                </q-form>
            </q-card>
        </q-dialog>
    </AuthenticatedLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Head, router } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';

const props = defineProps({
    referralCodes: Array,
    redemptions: Array,
});

// Table columns
const columns = [
    { name: 'code', align: 'left', label: 'Code', field: 'code' },
    { name: 'description', align: 'left', label: 'Description', field: 'description' },
    { name: 'status', align: 'center', label: 'Status', field: 'is_active' },
    { name: 'used', align: 'center', label: 'Used / Max', field: row => `${row.usage_count} / ${row.max_uses || '∞'}` },
    { name: 'expires_at', align: 'left', label: 'Expires', field: 'expires_at' },
    { name: 'actions', align: 'center', label: 'Actions', field: 'actions' },
];

// Reactive state
const loading = ref(false);
const showGenerateModal = ref(false);
const showEditModal = ref(false);

// New code form data
const newCode = ref({
    code: '',
    description: '',
    max_uses: 0,
    expires_at: null
});

// Edit code form data
const editingCode = ref({
    id: null,
    code: '',
    description: '',
    max_uses: 0,
    expires_at: null,
    is_active: true
});

// Statistics
const totalCodes = computed(() => props.referralCodes?.length || 0);
const activeCodes = computed(() => props.referralCodes?.filter(code => code.is_active).length || 0);
const totalRedemptions = computed(() => props.redemptions?.length || 0);

const redemptionsThisMonth = computed(() => {
    if (!props.redemptions) return 0;
    
    const now = new Date();
    const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    
    return props.redemptions.filter(r => {
        const redeemDate = new Date(r.created_at);
        return redeemDate >= firstDayOfMonth;
    }).length;
});

// Methods
const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
};

const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    // Could add a toast notification here
};

const generateCode = () => {
    loading.value = true;
    router.post(route('admin.referral-codes.store'), newCode.value, {
        onSuccess: () => {
            showGenerateModal.value = false;
            newCode.value = {
                code: '',
                description: '',
                max_uses: 0,
                expires_at: null
            };
            loading.value = false;
        },
        onError: () => {
            loading.value = false;
        }
    });
};

const editCode = (code) => {
    editingCode.value = {
        id: code.id,
        code: code.code,
        description: code.description,
        max_uses: code.max_uses,
        expires_at: code.expires_at,
        is_active: code.is_active
    };
    showEditModal.value = true;
};

const updateCode = () => {
    loading.value = true;
    router.put(route('admin.referral-codes.update', editingCode.value.id), editingCode.value, {
        onSuccess: () => {
            showEditModal.value = false;
            loading.value = false;
        },
        onError: () => {
            loading.value = false;
        }
    });
};

const toggleStatus = (code) => {
    if (confirm(`Are you sure you want to ${code.is_active ? 'deactivate' : 'activate'} this code?`)) {
        router.patch(route('admin.referral-codes.toggle-status', code.id));
    }
};

const deleteCode = (code) => {
    if (confirm(`Are you sure you want to delete the referral code: ${code.code}?`)) {
        router.delete(route('admin.referral-codes.destroy', code.id));
    }
};

onMounted(() => {
    // Any initialization if needed
});
</script>

<style scoped>
/* Card styling */
.stat-card {
    background-color: var(--card-bg, #d4d8bd);
    color: var(--text-primary);
}

.dark-mode .stat-card {
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

/* Table styling */
:deep(.q-table__card) {
    background-color: transparent;
}

:deep(.q-table thead tr) {
    background-color: rgba(79, 102, 66, 0.1);
}

:deep(.q-table tbody tr:hover) {
    background-color: rgba(79, 102, 66, 0.05);
}

/* Code font styling */
.code-font {
    font-family: monospace;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Text styling */
.text-secondary {
    color: var(--text-secondary, #64748b);
}

/* Form field colors */
:deep(.q-field__label) {
    color: var(--text-secondary, #64748b) !important;
}

:deep(.q-field__native), :deep(.q-field__input) {
    color: var(--text-primary, #1e293b) !important;
}

.dark-mode :deep(.q-field__native), .dark-mode :deep(.q-field__input) {
    color: var(--text-primary, #e2e8f0) !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
    }
}
</style> 