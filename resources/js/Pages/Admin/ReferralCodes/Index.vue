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
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <q-card flat bordered class="stat-card">
                    <q-card-section class="q-pa-sm">
                        <div class="flex items-center">
                            <div class="stat-icon mr-3">
                                <i class="fas fa-ticket-alt"></i>
                            </div>
                            <div>
                                <div class="text-xl font-bold">{{ totalCodes }}</div>
                                <div class="text-xs text-secondary">Total Codes</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section class="q-pa-sm">
                        <div class="flex items-center">
                            <div class="stat-icon mr-3">
                                <i class="fas fa-check-circle"></i>
                            </div>
                            <div>
                                <div class="text-xl font-bold">{{ activeCodes }}</div>
                                <div class="text-xs text-secondary">Active Codes</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section class="q-pa-sm">
                        <div class="flex items-center">
                            <div class="stat-icon mr-3">
                                <i class="fas fa-users"></i>
                            </div>
                            <div>
                                <div class="text-xl font-bold">{{ totalRedemptions }}</div>
                                <div class="text-xs text-secondary">Total Redemptions</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
                
                <q-card flat bordered class="stat-card">
                    <q-card-section class="q-pa-sm">
                        <div class="flex items-center">
                            <div class="stat-icon mr-3">
                                <i class="fas fa-calendar-alt"></i>
                            </div>
                            <div>
                                <div class="text-xl font-bold">{{ redemptionsThisMonth }}</div>
                                <div class="text-xs text-secondary">This Month</div>
                            </div>
                        </div>
                    </q-card-section>
                </q-card>
            </div>
            
            <!-- Referral Codes -->
            <q-card flat bordered class="stat-card mb-6">
                <q-card-section class="q-pa-md full-width">
                    <q-table
                        :rows="safeReferralCodes"
                        :columns="columns"
                        row-key="id"
                        :pagination="{rowsPerPage: 10}"
                        :loading="loading"
                        flat
                        bordered
                        class="my-sticky-header-table full-width"
                        style="width: 100%"
                        table-class="w-full"
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
                <q-card-section class="q-pa-md full-width">
                    <div v-if="safeRedemptions.length === 0" class="text-center py-4 text-gray-500">
                        No redemptions yet
                    </div>
                    
                    <q-list v-else bordered separator class="full-width redemption-list">
                        <q-item v-for="redemption in safeRedemptions" :key="redemption.id" class="redemption-item">
                            <q-item-section avatar>
                                <q-avatar>
                                    <img :src="redemption.user?.avatar || 'https://via.placeholder.com/150'" />
                                </q-avatar>
                            </q-item-section>
                            
                            <q-item-section>
                                <q-item-label>{{ redemption.user?.name || 'Unknown User' }}</q-item-label>
                                <q-item-label caption>Used code: <span class="code-font">{{ redemption.code || '-' }}</span></q-item-label>
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
import { ref, computed, onMounted, watch } from 'vue';
import { Head, router, usePage } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import axios from 'axios';
import { useQuasar } from 'quasar';

const q = useQuasar();
const page = usePage();

const props = defineProps({
    referralCodes: {
        type: Array,
        default: () => []
    },
    redemptions: {
        type: Array,
        default: () => []
    },
    flash: {
        type: Object,
        default: () => ({})
    }
});

// Watch for flash messages from the server
watch(() => page.props.flash, (newFlash) => {
    if (newFlash?.success) {
        q.notify({
            type: 'positive',
            message: newFlash.success,
            position: 'top',
            timeout: 3000
        });
    }
    
    if (newFlash?.error) {
        q.notify({
            type: 'negative',
            message: newFlash.error,
            position: 'top',
            timeout: 3000
        });
    }
}, { immediate: true });

// Table columns
const columns = [
    { name: 'code', align: 'left', label: 'Code', field: 'code', style: 'width: 20%' },
    { name: 'description', align: 'left', label: 'Description', field: 'description', style: 'width: 35%' },
    { name: 'status', align: 'center', label: 'Status', field: 'is_active', style: 'width: 10%' },
    { name: 'used', align: 'center', label: 'Used / Max', field: row => `${row.usage_count || 0} / ${row.max_uses || '∞'}`, style: 'width: 15%' },
    { name: 'expires_at', align: 'left', label: 'Expires', field: 'expires_at', style: 'width: 10%' },
    { name: 'actions', align: 'center', label: 'Actions', field: 'actions', style: 'width: 10%' },
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

// Ensure referral codes and redemptions are always arrays
const safeReferralCodes = computed(() => props.referralCodes || []);
const safeRedemptions = computed(() => props.redemptions || []);

// Statistics with null checks
const totalCodes = computed(() => safeReferralCodes.value.length);
const activeCodes = computed(() => safeReferralCodes.value.filter(code => code?.is_active).length);
const totalRedemptions = computed(() => safeRedemptions.value.length);

const redemptionsThisMonth = computed(() => {
    if (!safeRedemptions.value.length) return 0;
    
    const now = new Date();
    const firstDayOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    
    return safeRedemptions.value.filter(r => {
        if (!r?.created_at) return false;
        const redeemDate = new Date(r.created_at);
        return redeemDate >= firstDayOfMonth;
    }).length;
});

// Methods
const formatDate = (dateString) => {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    } catch (e) {
        console.error('Error formatting date:', e);
        return '-';
    }
};

const copyCode = (code) => {
    if (!code) return;
    
    navigator.clipboard.writeText(code)
        .then(() => {
            // Could add a toast notification here
            console.log('Code copied to clipboard');
        })
        .catch(err => {
            console.error('Could not copy code:', err);
        });
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
        onError: (errors) => {
            console.error('Error generating code:', errors);
            loading.value = false;
            
            // Display validation errors
            Object.keys(errors).forEach(field => {
                q.notify({
                    type: 'negative',
                    message: errors[field],
                    position: 'top'
                });
            });
        },
        preserveScroll: true
    });
};

const editCode = (code) => {
    if (!code) return;
    
    editingCode.value = {
        id: code.id,
        code: code.code || '',
        description: code.description || '',
        max_uses: code.max_uses || 0,
        expires_at: code.expires_at || null,
        is_active: Boolean(code.is_active)
    };
    showEditModal.value = true;
};

const updateCode = () => {
    if (!editingCode.value.id) return;
    
    loading.value = true;
    router.put(route('admin.referral-codes.update', editingCode.value.id), editingCode.value, {
        onSuccess: () => {
            showEditModal.value = false;
            loading.value = false;
        },
        onError: (errors) => {
            console.error('Error updating code:', errors);
            loading.value = false;
            
            // Display validation errors
            Object.keys(errors).forEach(field => {
                q.notify({
                    type: 'negative',
                    message: errors[field],
                    position: 'top'
                });
            });
        },
        preserveScroll: true
    });
};

const toggleStatus = (code) => {
    if (!code?.id) return;
    
    if (confirm(`Are you sure you want to ${code.is_active ? 'deactivate' : 'activate'} this code?`)) {
        loading.value = true;
        router.patch(route('admin.referral-codes.toggle-status', code.id), {}, {
            onSuccess: () => {
                loading.value = false;
            },
            onError: (errors) => {
                console.error('Error toggling status:', errors);
                loading.value = false;
                q.notify({
                    type: 'negative',
                    message: 'Failed to update status',
                    position: 'top'
                });
            },
            preserveScroll: true
        });
    }
};

const deleteCode = (code) => {
    if (!code?.id || !code?.code) return;
    
    if (confirm(`Are you sure you want to delete the referral code: ${code.code}?`)) {
        loading.value = true;
        router.delete(route('admin.referral-codes.destroy', code.id), {
            onSuccess: () => {
                loading.value = false;
            },
            onError: (errors) => {
                console.error('Error deleting code:', errors);
                loading.value = false;
                q.notify({
                    type: 'negative',
                    message: 'Failed to delete code',
                    position: 'top'
                });
            },
            preserveScroll: true
        });
    }
};

onMounted(() => {
    // Verify CSRF token is available
    const token = document.querySelector('meta[name="csrf-token"]');
    console.log('CSRF Token available:', !!token);
    if (token) {
        console.log('CSRF Token:', token.getAttribute('content'));
    }
    
    // Verify axios is configured with CSRF
    console.log('Axios headers:', window.axios.defaults.headers.common);
});
</script>

<style scoped>
/* Card styling */
.stat-card {
    background-color: var(--card-bg, #ffffff);
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
    width: 100%;
}

.stat-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.dark-mode .stat-card {
    background-color: var(--dark-card-bg, #1e293b);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Card header style */
.bg-accent {
    background-color: var(--accent-color, #4f6642);
    border-radius: 8px 8px 0 0;
    padding: 1rem;
}

/* Icon styling */
.stat-icon {
    background-color: var(--accent-color, #4f6642);
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Table styling */
:deep(.q-table__card) {
    background-color: transparent;
    box-shadow: none;
    height: 100%;
    width: 100%;
}

:deep(.q-table) {
    height: 100%;
    width: 100%;
}

:deep(.q-table__container) {
    width: 100%;
    margin: 0 !important;
}

:deep(.q-table__top),
:deep(.q-table__bottom),
:deep(.q-table__middle) {
    padding: 0 !important;
}

:deep(.q-virtual-scroll__content) {
    width: 100% !important;
}

:deep(.q-table__grid-content) {
    width: 100% !important;
    padding: 0 !important;
}

:deep(.q-table thead tr) {
    background-color: rgba(79, 102, 66, 0.05);
}

:deep(.q-table tbody tr:hover) {
    background-color: rgba(79, 102, 66, 0.05);
}

:deep(.q-table td) {
    padding: 8px 16px;
}

:deep(.q-table th) {
    padding: 8px 16px;
}

/* Code font styling */
.code-font {
    font-family: 'Fira Code', monospace;
    font-weight: 600;
    letter-spacing: 0.5px;
    color: var(--accent-color, #4f6642);
}

/* Text styling */
.text-secondary {
    color: var(--text-secondary, #64748b);
    font-size: 0.875rem;
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

/* Button styling */
:deep(.q-btn) {
    border-radius: 8px;
    font-weight: 500;
}

:deep(.q-btn--flat) {
    box-shadow: none;
}

:deep(.q-btn--round) {
    border-radius: 50%;
}

/* Badge styling */
:deep(.q-badge) {
    border-radius: 6px;
    padding: 4px 8px;
    font-weight: 500;
}

/* List styling */
:deep(.q-list) {
    border-radius: 8px;
    height: 100%;
    width: 100%;
    padding: 0 !important;
    margin: 0 !important;
}

:deep(.q-item) {
    border-radius: 8px;
    margin-bottom: 2px;
    padding: 8px 12px;
}

:deep(.q-item:hover) {
    background-color: rgba(79, 102, 66, 0.05);
}

:deep(.q-item-section) {
    padding: 0 8px;
}

/* Redemption item styling */
.redemption-item {
    width: 100%;
}

/* Full width utilities */
.full-width {
    width: 100% !important;
    max-width: 100% !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .grid {
        grid-template-columns: 1fr;
    }
    
    .stat-icon {
        width: 40px;
        height: 40px;
        font-size: 1.25rem;
    }
    
    .header-title h1 {
        font-size: 1.75rem;
    }
}

/* Table specific styling */
.my-sticky-header-table {
    /* height or max-height is important */
    max-height: 600px;
}

/* This will make the table go to full width */
:deep(.q-table__container) table {
    width: 100% !important;
}

:deep(th), :deep(td) {
    white-space: normal;
    padding: 8px;
}

:deep(th) {
    position: sticky;
    top: 0;
    opacity: 1;
    z-index: 10;
    background: #f5f5f5;
}

.redemption-list {
    width: 100% !important;
    display: block;
}

:deep(.q-item) {
    width: 100%;
    margin: 0;
    padding: 10px;
}
</style> 