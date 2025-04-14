<script setup>
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import DeleteUserForm from './Partials/DeleteUserForm.vue';
import UpdatePasswordForm from './Partials/UpdatePasswordForm.vue';
import UpdateProfileInformationForm from './Partials/UpdateProfileInformationForm.vue';
import { Head } from '@inertiajs/vue3';
import { ref, inject } from 'vue';
import '../../../css/profile.css';

// Get the global dark mode state from the AuthenticatedLayout
const isDarkMode = inject('isDarkMode', ref(false));

defineProps({
    mustVerifyEmail: {
        type: Boolean,
    },
    status: {
        type: String,
    },
});
</script>

<template>
    <Head title="Profile" />

    <AuthenticatedLayout>
        <!-- Standardized Header Section -->
        <div class="page-header mx-6 mt-6 mb-6">
            <div class="flex justify-between items-center">
                <div class="header-title">
                    <h1 class="text-3xl font-bold font-poppins">Profile Settings</h1>
                    <p class="text-gray-600 dark:text-gray-400">Manage your account settings and preferences</p>
                </div>
            </div>
        </div>

        <div class="py-6 px-6">
            <div class="mx-auto max-w-7xl space-y-6">
                <div class="theme-card">
                    <div class="p-6">
                        <h2 class="section-title">
                            Profile Information
                        </h2>
                        <p class="section-description">
                            Update your account's profile information and email address.
                        </p>
                        <UpdateProfileInformationForm
                            :must-verify-email="mustVerifyEmail"
                            :status="status"
                            class="max-w-xl"
                        />
                    </div>
                </div>

                <div class="theme-card">
                    <div class="p-6">
                        <h2 class="section-title">
                            Update Password
                        </h2>
                        <p class="section-description">
                            Ensure your account is using a long, random password to stay secure.
                        </p>
                        <UpdatePasswordForm class="max-w-xl" />
                    </div>
                </div>

                <div class="theme-card">
                    <div class="p-6">
                        <h2 class="section-title">
                            Delete Account
                        </h2>
                        <p class="section-description">
                            Once your account is deleted, all of its resources and data will be permanently deleted.
                        </p>
                        <DeleteUserForm class="max-w-xl" />
                    </div>
                </div>
            </div>
        </div>
    </AuthenticatedLayout>
</template>

<style>
.theme-card {
    background-color: var(--card-bg, #d4d8bd) !important;
    border-radius: 15px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.dark-mode .theme-card {
    background-color: var(--dark-card-bg, #1e293b) !important;
    border: 1px solid var(--dark-border-color, #4a5568);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}
</style>
