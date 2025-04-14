<template>
    <AuthenticatedLayout>
        <Head title="Role Management" />

        <div class="cctv-monitor-container px-6 py-4">
            <!-- Header Section -->
            <div class="page-header mb-6">
                <div class="flex justify-between items-center">
                    <div class="header-title">
                        <h1 class="text-3xl font-bold font-poppins">Role Management</h1>
                        <p class="text-secondary">Manage roles and permissions for system users</p>
                    </div>
                </div>
            </div>

            <!-- Two Column Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
                <!-- Create New Role -->
                <div>
                    <q-card flat bordered class="stat-card h-full">
                        <q-card-section class="q-pa-md full-width">
                            <q-form @submit.prevent="createRole" class="q-gutter-sm">
                                <q-input
                                    filled
                                    v-model="newRole.name"
                                    label="Role Name"
                                    required
                                    stack-label
                                    dense
                                />
                                
                                <q-input
                                    filled
                                    v-model="newRole.description"
                                    label="Description"
                                    stack-label
                                    type="textarea"
                                    rows="2"
                                    dense
                                />
                                
                                <div>
                                    <div class="text-sm q-mb-sm">Select Permissions</div>
                                    <div class="permission-grid bg-opacity-10 rounded-md p-2">
                                        <q-checkbox
                                            v-for="permission in permissions"
                                            :key="permission.id"
                                            v-model="newRole.permissions"
                                            :val="permission.name"
                                            :label="permission.name"
                                            dense
                                        />
                                    </div>
                                </div>
                                
                                <div class="text-right">
                                    <q-btn 
                                        type="submit" 
                                        color="primary" 
                                        icon="add_circle" 
                                        label="Create Role" 
                                    />
                                </div>
                            </q-form>
                        </q-card-section>
                    </q-card>
                </div>
                
                <!-- User Role Assignment -->
                <div>
                    <q-card flat bordered class="stat-card h-full">
                        <q-card-section class="q-pa-md full-width">
                            <div class="user-role-list">
                                <div 
                                    v-for="user in users" 
                                    :key="user.id" 
                                    class="user-role-item q-mb-md"
                                >
                                    <div class="flex items-center gap-2 mb-2">
                                        <q-avatar color="primary" text-color="white" size="32px">
                                            {{ user.name.charAt(0) }}
                                        </q-avatar>
                                        <div>
                                            <div class="text-sm font-bold">{{ user.name }}</div>
                                            <div class="text-xs text-secondary">{{ user.email }}</div>
                                        </div>
                                    </div>
                                    
                                    <div class="flex items-center gap-2">
                                        <q-select
                                            v-model="userRoles[user.id]"
                                            :options="roles.map(role => ({ label: role.name, value: role.name }))"
                                            multiple
                                            emit-value
                                            map-options
                                            filled
                                            dense
                                            label="Assigned Roles"
                                            class="flex-grow"
                                        />
                                        <q-btn 
                                            flat 
                                            round
                                            color="primary" 
                                            icon="save" 
                                            @click="assignRoles(user)" 
                                        />
                                    </div>
                                </div>
                            </div>
                        </q-card-section>
                    </q-card>
                </div>
            </div>
            
            <!-- Existing Roles -->
            <q-card flat bordered class="stat-card">
                <q-card-section class="q-pa-md full-width">
                    <div class="roles-grid">
                        <q-card 
                            v-for="role in roles" 
                            :key="role.id" 
                            flat 
                            bordered 
                            class="role-card h-full"
                        >
                            <q-card-section class="q-pa-md full-width">
                                <div class="flex justify-between items-center">
                                    <h3 class="text-base font-bold">{{ role.name }}</h3>
                                    <div>
                                        <q-btn flat round size="sm" icon="edit" class="edit-btn" @click="editRole(role)" />
                                        <q-btn flat round size="sm" icon="delete" class="delete-btn" @click="deleteRole(role)" />
                                    </div>
                                </div>
                                <p class="role-description text-xs q-mt-md">{{ role.description }}</p>
                                
                                <q-separator class="q-my-md" />
                                
                                <div>
                                    <div class="text-sm q-mb-sm">Permissions</div>
                                    <div class="permission-chips">
                                        <q-chip
                                            v-for="permission in role.permissions"
                                            :key="permission.id"
                                            :label="permission.name"
                                            dense
                                            size="sm"
                                            class="permission-chip"
                                        />
                                    </div>
                                </div>
                            </q-card-section>
                        </q-card>
                    </div>
                </q-card-section>
            </q-card>
        </div>
    </AuthenticatedLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Head, router } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';

const props = defineProps({
    roles: Array,
    permissions: Array,
    users: Array,
});

const newRole = ref({
    name: '',
    description: '',
    permissions: [],
});

const userRoles = ref({});

const createRole = () => {
    router.post(route('admin.roles.store'), newRole.value, {
        preserveScroll: true,
        onSuccess: () => {
            newRole.value = {
                name: '',
                description: '',
                permissions: [],
            };
        },
    });
};

const editRole = (role) => {
    router.put(route('admin.roles.update', role.id), {
        name: role.name,
        description: role.description,
        permissions: role.permissions.map(p => p.name),
    }, {
        preserveScroll: true,
    });
};

const deleteRole = (role) => {
    if (confirm('Are you sure you want to delete this role?')) {
        router.delete(route('admin.roles.destroy', role.id), {
            preserveScroll: true,
        });
    }
};

const assignRoles = (user) => {
    router.post(route('admin.users.roles.assign', user.id), {
        roles: userRoles.value[user.id],
    }, {
        preserveScroll: true,
    });
};

onMounted(() => {
    // Initialize userRoles with current user roles
    props.users.forEach(user => {
        userRoles.value[user.id] = user.roles.map(role => role.name);
    });
});
</script>

<style scoped>
/* Grid layouts */
.roles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
    width: 100%;
}

.permission-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 8px;
    padding: 0.75rem;
    background-color: rgba(79, 102, 66, 0.05);
    border-radius: 6px;
}

/* Card styling */
.role-card {
    background-color: var(--card-bg, #ffffff);
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
    width: 100%;
}

.role-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.dark-mode .role-card {
    background-color: var(--dark-card-bg, #1e293b);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Full width utilities */
.full-width {
    width: 100% !important;
    max-width: 100% !important;
}

/* Permission chip styling */
.permission-chip {
    background-color: var(--accent-color, #4f6642) !important;
    color: white !important;
    font-size: 0.75rem;
    border-radius: 4px;
    padding: 2px 6px;
}

.permission-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    padding: 0.25rem 0;
}

/* Icon and button styling */
.edit-btn, .delete-btn {
    transition: transform 0.2s;
}

.edit-btn:hover, .delete-btn:hover {
    transform: scale(1.1);
}

.edit-btn {
    color: var(--accent-color, #4f6642);
}

.delete-btn {
    color: var(--danger-color, #e63946);
}

/* Text styling */
.role-description {
    color: var(--text-secondary, #64748b);
    font-size: 0.875rem;
    line-height: 1.5;
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

/* Checkbox styling */
:deep(.q-checkbox) {
    margin: 4px 0;
}

:deep(.q-checkbox__label) {
    font-size: 0.875rem;
}

/* Select styling */
:deep(.q-select) {
    margin-bottom: 1rem;
}

/* Avatar styling */
:deep(.q-avatar) {
    font-size: 0.875rem;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Modal styling */
:deep(.q-dialog__inner) {
    border-radius: 12px;
    overflow: hidden;
}

:deep(.q-card) {
    border-radius: 12px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .roles-grid {
        grid-template-columns: 1fr;
        padding: 0.5rem;
    }
    
    .permission-grid {
        grid-template-columns: 1fr;
        padding: 0.75rem;
    }
    
    .header-title h1 {
        font-size: 1.75rem;
    }
    
    .user-role-item .flex {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .user-role-item .q-select {
        width: 100%;
        margin-bottom: 8px;
    }
}
</style> 