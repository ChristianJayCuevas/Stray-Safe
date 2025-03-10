<script setup>
import Checkbox from '@/Components/Checkbox.vue';
import GuestLayout from '@/Layouts/GuestLayout.vue';
import InputError from '@/Components/InputError.vue';
import InputLabel from '@/Components/InputLabel.vue';
import PrimaryButton from '@/Components/PrimaryButton.vue';
import TextInput from '@/Components/TextInput.vue';
import { Head, Link, useForm } from '@inertiajs/vue3';
import GoogleIcon from '@/Icons/GoogleIcon.vue';

defineProps({
    canResetPassword: {
        type: Boolean,
    },
    status: {
        type: String,
    },
});

const form = useForm({
    email: '',
    password: '',
    remember: false,
});

const submit = () => {
    form.post(route('login'), {
        onFinish: () => form.reset('password'),
    });
};
</script>

<template>
    <GuestLayout :page="'login'">
        <Head title="Log in" />

        <div v-if="status" class="mb-4 text-sm font-medium text-green-600">
            {{ status }}
        </div>

        <h1 class="text-2xl font-bold text-[#38a3a5] mb-2">Welcome Back</h1>
        <p class="text-gray-600 mb-6">Sign in to your account to continue</p>

        <form @submit.prevent="submit">
            <div class="mb-4">
                <q-input 
                    outlined 
                    label="Email" 
                    id="email" 
                    type="email" 
                    class="w-full" 
                    v-model="form.email" 
                    required 
                    autofocus
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
                    autocomplete="current-password" 
                    color="teal"
                    standout
                    bg-color="white"
                />
                <InputError class="mt-1" :message="form.errors.password" />
            </div>

            <div class="flex justify-between items-center mb-6">
                <label class="flex items-center">
                    <Checkbox name="remember" v-model:checked="form.remember" class="accent-[#38a3a5]" />
                    <span class="ml-2 text-sm text-gray-600">
                        Remember me
                    </span>
                </label>
                <Link 
                    v-if="canResetPassword" 
                    :href="route('password.request')"
                    class="text-sm text-[#38a3a5] hover:underline"
                >
                    Forgot password?
                </Link>
            </div>

            <div class="mb-6">
                <button 
                    type="submit" 
                    class="w-full bg-[#38a3a5] hover:bg-[#22577a] text-white py-2 px-4 rounded-lg transition duration-300 ease-in-out"
                >
                    Sign In
                </button>
            </div>

            <div class="relative mb-6">
                <div class="absolute inset-0 flex items-center">
                    <div class="w-full border-t border-gray-300"></div>
                </div>
                <div class="relative flex justify-center text-sm">
                    <span class="px-2 bg-white text-gray-500">Or continue with</span>
                </div>
            </div>

            <button 
                type="button"
                class="w-full flex items-center justify-center gap-2 border border-gray-300 rounded-lg py-2 px-4 bg-white hover:bg-gray-50 transition duration-300 ease-in-out"
            >
                <GoogleIcon />
                <span>Sign in with Google</span>
            </button>

            <div class="mt-6 text-center text-sm text-gray-600">
                Don't have an account? 
                <Link href="/register" class="text-[#38a3a5] hover:underline">
                    Create account
                </Link>
            </div>
        </form>
    </GuestLayout>
</template>
<style scoped>
/* Add styles here if needed */
</style>