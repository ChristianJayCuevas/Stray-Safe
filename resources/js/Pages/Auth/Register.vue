<script setup>
import GuestLayout from '@/Layouts/GuestLayout.vue';
import InputError from '@/Components/InputError.vue';
import InputLabel from '@/Components/InputLabel.vue';
import PrimaryButton from '@/Components/PrimaryButton.vue';
import TextInput from '@/Components/TextInput.vue';
import { Head, Link, useForm } from '@inertiajs/vue3';

const form = useForm({
    name: '',
    email: '',
    password: '',
    password_confirmation: '',
    referral_code: '',
});

const submit = () => {
    form.post(route('register'), {
        onFinish: () => form.reset('password', 'password_confirmation'),
    });
};
</script>

<template>
    <GuestLayout :page="'register'">
        <Head title="Register" />
        
        <h1 class="text-2xl font-bold text-[#38a3a5] mb-2">Create Account</h1>
        <p class="text-gray-600 mb-6">Join StraySafe and help stray animals find homes</p>
        
        <form @submit.prevent="submit">
            <div class="mb-4">
                <q-input
                    outlined
                    label="Name"
                    id="name"
                    type="text"
                    class="w-full"
                    v-model="form.name"
                    required
                    autofocus
                    autocomplete="name"
                    color="teal"
                    standout
                    bg-color="white"
                />
                <InputError class="mt-1" :message="form.errors.name" />
            </div>

            <div class="mb-4">
                <q-input
                    outlined
                    label="Email"
                    id="email"
                    type="email"
                    class="w-full"
                    v-model="form.email"
                    required
                    autocomplete="username"
                    color="teal"
                    standout
                    bg-color="white"
                />
                <InputError class="mt-1" :message="form.errors.email" />
            </div>

            <div class="mb-4">
                <q-input
                    outlined
                    label="Password"
                    id="password"
                    type="password"
                    class="w-full"
                    v-model="form.password"
                    required
                    autocomplete="new-password"
                    color="teal"
                    standout
                    bg-color="white"
                />
                <InputError class="mt-1" :message="form.errors.password" />
            </div>

            <div class="mb-6">
                <q-input
                    outlined
                    label="Confirm Password"
                    id="password_confirmation"
                    type="password"
                    class="w-full"
                    v-model="form.password_confirmation"
                    required
                    autocomplete="new-password"
                    color="teal"
                    standout
                    bg-color="white"
                />
                <InputError class="mt-1" :message="form.errors.password_confirmation" />
            </div>

            <div class="mb-4">
                <q-input
                    outlined
                    label="Referral Code"
                    id="referral_code"
                    type="text"
                    class="w-full"
                    v-model="form.referral_code"
                    required
                    color="teal"
                    standout
                    bg-color="white"
                />
                <InputError class="mt-1" :message="form.errors.referral_code" />
            </div>
            
            <div class="mb-6">
                <button 
                    type="submit" 
                    class="w-full bg-[#38a3a5] hover:bg-[#22577a] text-white py-2 px-4 rounded-lg transition duration-300 ease-in-out"
                >
                    Create Account
                </button>
            </div>
            
            <div class="mt-6 text-center text-sm text-gray-600">
                Already have an account? 
                <Link href="/login" class="text-[#38a3a5] hover:underline">
                    Sign in
                </Link>
            </div>
        </form>
    </GuestLayout>
</template>

<style scoped>
/* Add styles here if needed */
</style>