<template>
    <AuthenticatedLayout>
        <Head title="User Management" />

        <div class="cctv-monitor-container px-6 py-4">
            <!-- Header Section -->
            <div class="page-header mb-6">
                <div class="flex justify-between items-center">
                    <div class="header-title">
                        <h1 class="text-3xl font-bold font-poppins">User Management</h1>
                        <p class="text-secondary">Create and manage system users</p>
                    </div>
                    <q-btn 
                        color="primary" 
                        label="Create User" 
                        icon="add"
                        @click="showCreateUserModal = true" 
                    />
                </div>
            </div>

            <!-- Users Grid -->
            <q-card flat bordered class="stat-card mb-4">
                <q-card-section class="q-pa-md full-width">
                    <div class="users-grid">
                        <q-card 
                            v-for="user in users" 
                            :key="user.id" 
                            flat 
                            bordered 
                            class="user-card h-full"
                        >
                            <q-card-section class="q-pa-md full-width">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center gap-2">
                                        <q-avatar color="primary" text-color="white" size="36px">
                                            {{ user.name.charAt(0) }}
                                        </q-avatar>
                                        <div>
                                            <h3 class="text-base font-bold">{{ user.name }}</h3>
                                            <p class="user-email text-xs">{{ user.email }}</p>
                                        </div>
                                    </div>
                                    <div>
                                        <q-btn flat round size="sm" icon="edit" class="edit-btn" @click="editUser(user)" />
                                        <q-btn flat round size="sm" icon="delete" class="delete-btn" @click="deleteUser(user)" />
                                    </div>
                                </div>
                                
                                <q-separator class="q-my-md" />
                                
                                <div class="grid grid-cols-2 gap-4">
                                    <div>
                                        <div class="text-xs font-medium text-gray-500">User Type</div>
                                        <div class="text-sm">{{ user.user_type || 'Standard User' }}</div>
                                    </div>
                                    <div>
                                        <div class="text-xs font-medium text-gray-500">Status</div>
                                        <div class="text-sm">
                                            <q-badge :color="user.email_verified_at ? 'positive' : 'warning'">
                                                {{ user.email_verified_at ? 'Verified' : 'Unverified' }}
                                            </q-badge>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="q-mt-md">
                                    <div class="text-xs font-medium text-gray-500 mb-2">Roles</div>
                                    <div class="permission-chips">
                                        <q-chip
                                            v-for="role in user.roles"
                                            :key="role.id"
                                            :label="role.name"
                                            dense
                                            size="sm"
                                            class="role-chip"
                                        />
                                        <span v-if="!user.roles || user.roles.length === 0" class="text-xs italic text-gray-500">
                                            No roles assigned
                                        </span>
                                    </div>
                                </div>
                                
                                <q-card-actions align="right" class="q-mt-md">
                                    <q-btn flat color="primary" label="Manage Roles" @click="manageUserRoles(user)" />
                                </q-card-actions>
                            </q-card-section>
                        </q-card>
                    </div>
                </q-card-section>
            </q-card>
        </div>
        
        <!-- Create User Modal -->
        <q-dialog v-model="showCreateUserModal" persistent>
            <q-card style="width: 500px; max-width: 90vw;">
                <q-card-section class="q-py-sm bg-accent">
                    <div class="text-xl font-bold text-white">Create New User</div>
                </q-card-section>
                
                <q-form @submit.prevent="createUser">
                    <q-card-section>
                        <div class="q-gutter-md">
                            <q-input
                                v-model="newUser.name"
                                label="Full Name"
                                filled
                                required
                            />
                            
                            <q-input
                                v-model="newUser.email"
                                label="Email Address"
                                filled
                                type="email"
                                required
                            />
                            
                            <q-input
                                v-model="newUser.password"
                                label="Password"
                                filled
                                type="password"
                                required
                            />
                            
                            <q-input
                                v-model="newUser.password_confirmation"
                                label="Confirm Password"
                                filled
                                type="password"
                                required
                            />
                            
                            <q-select
                                v-model="newUser.roles"
                                :options="availableRoles"
                                label="Assign Roles"
                                filled
                                multiple
                                emit-value
                                map-options
                            />
                        </div>
                    </q-card-section>
                    
                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" color="negative" v-close-popup />
                        <q-btn type="submit" label="Create User" color="primary" />
                    </q-card-actions>
                </q-form>
            </q-card>
        </q-dialog>
        
        <!-- Edit User Modal -->
        <q-dialog v-model="showEditUserModal" persistent>
            <q-card style="width: 500px; max-width: 90vw;">
                <q-card-section class="q-py-sm bg-accent">
                    <div class="text-xl font-bold text-white">Edit User</div>
                </q-card-section>
                
                <q-form @submit.prevent="updateUser">
                    <q-card-section>
                        <div class="q-gutter-md">
                            <q-input
                                v-model="editingUser.name"
                                label="Full Name"
                                filled
                                required
                            />
                            
                            <q-input
                                v-model="editingUser.email"
                                label="Email Address"
                                filled
                                type="email"
                                required
                            />
                            
                            <q-input
                                v-model="editingUser.password"
                                label="New Password (Leave blank to keep current)"
                                filled
                                type="password"
                            />
                            
                            <q-input
                                v-model="editingUser.password_confirmation"
                                label="Confirm New Password"
                                filled
                                type="password"
                            />
                            
                            <q-checkbox
                                v-model="editingUser.is_verified"
                                label="Mark Email as Verified"
                            />
                        </div>
                    </q-card-section>
                    
                    <q-card-actions align="right">
                        <q-btn flat label="Cancel" color="negative" v-close-popup />
                        <q-btn type="submit" label="Update User" color="primary" />
                    </q-card-actions>
                </q-form>
            </q-card>
        </q-dialog>
    </AuthenticatedLayout>
</template>

<script setup>
import { ref } from 'vue';
import { Head, router } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';

const props = defineProps({
    users: Array,
    roles: Array,
});

// Available roles for dropdowns
const availableRoles = ref(
    props.roles.map(role => ({
        label: role.name,
        value: role.id
    }))
);

// User creation state
const showCreateUserModal = ref(false);
const newUser = ref({
    name: '',
    email: '',
    password: '',
    password_confirmation: '',
    roles: []
});

// User editing state
const showEditUserModal = ref(false);
const editingUser = ref({
    id: null,
    name: '',
    email: '',
    password: '',
    password_confirmation: '',
    is_verified: false
});

// Create a new user
const createUser = () => {
    router.post(route('admin.users.store'), newUser.value, {
        onSuccess: () => {
            showCreateUserModal.value = false;
            newUser.value = {
                name: '',
                email: '',
                password: '',
                password_confirmation: '',
                roles: []
            };
        },
    });
};

// Edit user modal
const editUser = (user) => {
    editingUser.value = {
        id: user.id,
        name: user.name,
        email: user.email,
        password: '',
        password_confirmation: '',
        is_verified: !!user.email_verified_at
    };
    showEditUserModal.value = true;
};

// Update an existing user
const updateUser = () => {
    router.put(route('admin.users.update', editingUser.value.id), {
        name: editingUser.value.name,
        email: editingUser.value.email,
        password: editingUser.value.password,
        password_confirmation: editingUser.value.password_confirmation,
        is_verified: editingUser.value.is_verified,
    }, {
        onSuccess: () => {
            showEditUserModal.value = false;
        },
    });
};

// Delete a user
const deleteUser = (user) => {
    if (confirm(`Are you sure you want to delete ${user.name}?`)) {
        router.delete(route('admin.users.destroy', user.id));
    }
};

// Redirect to roles management for this user
const manageUserRoles = (user) => {
    router.visit(route('admin.roles.index', { user: user.id }));
};
</script>

<style scoped>
/* Grid layouts */
.users-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
    width: 100%;
}

/* Card styling */
.user-card {
    background-color: var(--card-bg, #ffffff);
    border-radius: 12px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
    width: 100%;
}

.user-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
}

.dark-mode .user-card {
    background-color: var(--dark-card-bg, #1e293b);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Full width utilities */
.full-width {
    width: 100% !important;
    max-width: 100% !important;
}

/* Avatar styling */
:deep(.q-avatar) {
    font-size: 1rem;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Role chip styling */
.role-chip {
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

/* Button styling */
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
.user-email {
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

/* Badge styling */
:deep(.q-badge) {
    border-radius: 6px;
    padding: 4px 8px;
    font-weight: 500;
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
    .users-grid {
        grid-template-columns: 1fr;
        padding: 0.5rem;
    }
    
    .header-title h1 {
        font-size: 1.75rem;
    }
    
    .permission-chips {
        gap: 4px;
    }
}
</style> 