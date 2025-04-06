<template>
    <AuthenticatedLayout>
        <Head title="Role Management" />

        <div class="cctv-monitor-container px-6 py-4">
            <!-- Header Section -->
            <div class="page-header mb-6">
                <div class="flex justify-between items-center">
                    <div class="header-title">
                        <h1 class="text-3xl font-bold">Role Management</h1>
                        <p class="text-secondary">Manage roles and permissions for system users</p>
                    </div>
                </div>
            </div>

            <!-- Two Column Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <!-- Create New Role -->
                <div>
                    <q-card flat bordered class="stat-card h-full">
                        <q-card-section class="q-py-sm bg-accent">
                            <h2 class="text-xl font-bold text-white">Create New Role</h2>
                        </q-card-section>
                        
                        <q-card-section>
                            <q-form @submit.prevent="createRole" class="q-gutter-md">
                                <q-input
                                    filled
                                    v-model="newRole.name"
                                    label="Role Name"
                                    required
                                    stack-label
                                />
                                
                                <q-input
                                    filled
                                    v-model="newRole.description"
                                    label="Description"
                                    stack-label
                                    type="textarea"
                                    rows="2"
                                />
                                
                                <div>
                                    <div class="text-subtitle1 q-mb-sm">Select Permissions</div>
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
                        <q-card-section class="q-py-sm bg-accent">
                            <h2 class="text-xl font-bold text-white">User Role Assignment</h2>
                        </q-card-section>
                        
                        <q-card-section>
                            <div class="user-role-list">
                                <div 
                                    v-for="user in users" 
                                    :key="user.id" 
                                    class="user-role-item q-mb-md"
                                >
                                    <div class="flex items-center gap-3 mb-2">
                                        <q-avatar color="primary" text-color="white">
                                            {{ user.name.charAt(0) }}
                                        </q-avatar>
                                        <div>
                                            <div class="text-weight-bold">{{ user.name }}</div>
                                            <div class="text-caption">{{ user.email }}</div>
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
                <q-card-section class="q-py-sm bg-accent">
                    <h2 class="text-xl font-bold text-white">Existing Roles</h2>
                </q-card-section>
                
                <q-card-section>
                    <div class="roles-grid">
                        <q-card 
                            v-for="role in roles" 
                            :key="role.id" 
                            flat 
                            bordered 
                            class="role-card h-full"
                        >
                            <q-card-section class="q-pb-xs">
                                <div class="flex justify-between items-center">
                                    <h3 class="text-lg font-bold">{{ role.name }}</h3>
                                    <div>
                                        <q-btn flat round size="sm" icon="edit" class="edit-btn" @click="editRole(role)" />
                                        <q-btn flat round size="sm" icon="delete" class="delete-btn" @click="deleteRole(role)" />
                                    </div>
                                </div>
                                <p class="role-description q-mt-sm">{{ role.description }}</p>
                            </q-card-section>
                            
                            <q-separator />
                            
                            <q-card-section>
                                <div class="text-weight-medium q-mb-xs">Permissions</div>
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
/* Grid layouts for each section */
.roles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
}

.permission-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 8px;
}

.permission-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

/* Card styling */
.role-card {
    transition: transform 0.2s;
    background-color: var(--card-bg, #d4d8bd);
}

.role-card:hover {
    transform: translateY(-2px);
}

.dark-mode .role-card {
    background-color: var(--dark-card-bg, #1e293b);
}

/* Card header style */
.bg-accent {
    background-color: var(--accent-color, #4f6642);
}

/* Permission chip styling */
.permission-chip {
    background-color: var(--accent-color, #4f6642) !important;
    color: white !important;
    font-size: 0.75rem;
}

/* Icon and button styling */
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
}

/* Form field colors - ensure visibility in both modes */
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
    .roles-grid {
        grid-template-columns: 1fr;
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