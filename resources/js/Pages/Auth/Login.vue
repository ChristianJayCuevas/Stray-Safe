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
        <p class="title mb-3">Login</p>
        <p class="message mb-3">Welcome back user </p>

        <form @submit.prevent="submit">
            <div>
                <q-input outlined label="Email" id="email" type="email" class="mt-1 block w-full dark:bg-white" v-model="form.email" required autofocus
                    autocomplete="username" />

                <InputError class="mt-2" :message="form.errors.email" />
            </div>

            <div class="mt-4">
                <q-input outlined label="Password" id="password" type="password" class="mt-1 block dark:bg-white dark:color-black w-full" v-model="form.password" required
                    autocomplete="current-password" />

                <InputError class="mt-2" :message="form.errors.password" />
            </div>

            <div class="mt-4 flex flex-row justify-between items-center">
                <label class="flex items-center">
                    <Checkbox name="remember" v-model:checked="form.remember" />
                    <span class="ms-2 text-sm text-gray-600 dark:text-gray-400">
                        Remember me
                    </span>
                </label>
                <Link v-if="canResetPassword" :href="route('password.request')"
                    class="rounded-md text-sm text-gray-600 underline hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 dark:text-gray-400 dark:hover:text-gray-100 dark:focus:ring-offset-gray-800">
                Forgot your password?
                </Link>
            </div>

            <div class="mt-4 flex flex-col items-center justify-center">
                <q-btn push rounded class="submit" size="lg" type="submit">Login</q-btn>
            </div>
            <div class="signin mt-3">
                <span>Don't have an account? </span>
                <Link href="/register" class="text-blue-500 hover:text-blue-700">Sign Up</Link>
            </div>
            <div class="signin mt-3 content__or-text">
                <span></span>
                <span>OR</span>
                <span></span>
            </div>
            <button class="btn google">
                <GoogleIcon />
                <span>Sign in with Google</span>

            </button>
        </form>
    </GuestLayout>
</template>
<style scoped>
.content__or-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  text-transform: uppercase;
  font-size: 13px;
  column-gap: 18px;
  margin-top: 18px;
}

.content__or-text span:nth-child(3),
.content__or-text span:nth-child(1) {
  display: block;
  width: 100%;
  height: 1px;
  background-color: rgb(219, 219, 219);
}

.form {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-width: 350px;
    background: rgba(79, 102, 66, 0.2);
    padding: 20px;
    border-radius: 20px;
    position: relative;
}

.title {
    font-size: 28px;
    color: #38a3a5;
    font-weight: 600;
    letter-spacing: -1px;
    position: relative;
    display: flex;
    align-items: center;
    padding-left: 30px;
}

.title::before,
.title::after {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    border-radius: 50%;
    left: 0px;
    background-color: #38a3a5;
}

.title::before {
    width: 18px;
    height: 18px;
    background-color: #38a3a5;
}

.title::after {
    width: 18px;
    height: 18px;
    animation: pulse 1s linear infinite;
}

.message,
.signin {
    color: rgba(88, 87, 87, 0.822);
    font-size: 14px;
}

.signin {
    text-align: center;
}

.signin a {
    color: #38a3a5;
}

.signin a:hover {
    text-decoration: underline #38a3a5;
}

.flex {
    display: flex;
    gap: 6px;
}

.form label {
    position: relative;
}

.form label .input {
    width: 100%;
    padding: 10px 10px 20px 10px;
    outline: 0;
    border: 1px solid rgba(105, 105, 105, 0.397);
    border-radius: 10px;
}

.form label .input+span {
    position: absolute;
    left: 10px;
    top: 15px;
    color: grey;
    font-size: 0.9em;
    cursor: text;
    transition: 0.3s ease;
}

.form label .input:placeholder-shown+span {
    top: 15px;
    font-size: 0.9em;
}

.form label .input:focus+span,
.form label .input:valid+span {
    top: 30px;
    font-size: 0.7em;
    font-weight: 600;
}

.form label .input:valid+span {
    color: green;
}

.submit {
    border: none;
    outline: none;
    background-color: #38a3a5;
    padding: 10px;
    border-radius: 10px;
    color: #fff;
    font-size: 16px;
    width: 100%;
    transform: .3s ease;
}

.submit:hover {
    background-color: #22577a;
}

@keyframes pulse {
    from {
        transform: scale(0.9);
        opacity: 1;
    }

    to {
        transform: scale(1.8);
        opacity: 0;
    }
}
.btn {
  margin-top: 10px;
  width: 100%;
  height: 50px;
  border-radius: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 500;
  gap: 10px;
  border: 1px solid #ededef;
  background-color: white;
  cursor: pointer;
  transition: 0.2s ease-in-out;
}

.btn:hover {
  border: 1px solid #2d79f3;
  ;
}

</style>