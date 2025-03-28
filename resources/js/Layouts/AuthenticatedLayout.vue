<script setup>
import { ref, computed, onMounted, defineEmits, provide, watch } from "vue";
import { Link, usePage, router } from "@inertiajs/vue3";
import { Head, useForm } from "@inertiajs/vue3";
import { useQuasar } from 'quasar';

//FilePond imports for multiple file upload
import vueFilePond from "vue-filepond";
import FilePondPluginImagePreview from "filepond-plugin-image-preview";
import 'filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css';
import 'filepond/dist/filepond.min.css';

//Create an Instance of FilePond
const FilePond = vueFilePond(FilePondPluginImagePreview);

const { auth } = usePage().props;
const authUser = computed(() => auth.user || null);
console.log("auth.user:", auth.user);

const drawer = ref(false);
const miniState = ref(true);
const thepost = ref(false);
const leftDrawerOpen = ref(false);
const search = ref('');
const filteredResults = ref({ posts: [], users: [] });
const $q = useQuasar();

// Dark mode state
const isDarkMode = ref(localStorage.getItem('darkMode') === 'true');

// Initialize dark mode on component mount
onMounted(() => {
  applyDarkMode(isDarkMode.value);
});

// Toggle dark mode
function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value;
  localStorage.setItem('darkMode', isDarkMode.value);
  applyDarkMode(isDarkMode.value);
}

// Apply dark mode to Quasar and body
function applyDarkMode(isDark) {
  $q.dark.set(isDark);
  
  // Apply dark mode class to body for global CSS variables
  if (isDark) {
    document.body.classList.add('dark-mode');
  } else {
    document.body.classList.remove('dark-mode');
  }
}

// Watch for dark mode changes to ensure consistency
watch(isDarkMode, (newValue) => {
  applyDarkMode(newValue);
});

// Provide dark mode state to child components
provide('isDarkMode', isDarkMode);

function submitLogout() {
    Inertia.post(route("logout"));
}

function toggleLeftDrawer() {
    leftDrawerOpen.value = !leftDrawerOpen.value;
}

// Perform search
const emit = defineEmits();

const updateSearch = () => {
    emit('search-updated', search.value);
};

const clearSearch = () => {
    search.value = '';
    emit('search-updated', search.value);
};
const uploader = ref(null);
const form = useForm({
    title: "",
    description: "",
    image_url: [],
});

const errorMessage = ref("");

function handleFilePondRevert(uniqueId, load, error){
    form.image_url = form.image_url.filter((image) => image !== uniqueId);
    router.delete('/revert/' + uniqueId);
    load();
}

function handleFilePondLoad(response){
    form.image_url.push(response); 
    return response;
}

const submit = () => {
    errorMessage.value = ""; // Clear any previous error messages

    // Print the form data for debugging purposes
    console.log("Form Data:", {
        title: form.title,
        description: form.description,
        image_url: form.image_url,
    });

    // Check if all required fields are filled
    if (!form.title || !form.description || !form.image_url) {
        errorMessage.value = "Image, Title and Description are required.";
        return;
    }

    form.post(route("post.uploadPost"), {
        onSuccess: () => {
            // Handle successful form submission
            console.log("Form submitted successfully!");
            localStorage.setItem('notification', 'successPost');
            window.location.reload();
        },
        onError: (errors) => {
            // Handle errors from the server
            console.error("Form submission error:", errors);
            errorMessage.value = "An error occurred while submitting the form.";
        },
    });
};

// Handle logout with confirmation
const handleLogout = () => {
  $q.dialog({
    title: 'Confirm Logout',
    message: 'Are you sure you want to logout?',
    cancel: true,
    persistent: true
  }).onOk(() => {
    router.post(route('logout'));
  });
};

</script>
<template>
    <div :class="{'bg-website': !isDarkMode, 'bg-dark': isDarkMode}">
      <q-layout view="hHh lpR fFf">
        <q-drawer
          v-model="drawer"
          show-if-above
          :mini="miniState"
          @mouseover="miniState = false"
          @mouseout="miniState = true"
          :width="220"
          :breakpoint="500"
          :class="['custom-drawer', {'dark-drawer': isDarkMode}]"
          behavior="desktop"
        >
          <q-scroll-area class="fit drawer-content" :horizontal-thumb-style="{ opacity: 0 }">
            <q-list padding>
            <!-- Logo and Name -->
            <q-item class="q-pa-md">
              <q-item-section avatar>
                <img src="/storage/images/NEWLOGO.png" alt="Logo" class="w-10 h-10" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="text-2xl custom-text font-bold font-poppins">Stray<span class="custom-color">Safe</span></q-item-label>
              </q-item-section>
            </q-item>
            <q-separator class="q-my-md" :dark="isDarkMode" />
  
              <!-- Navigation Links -->
              <Link :href="route('dashboard')">
                <q-item 
                  clickable 
                  class="GPL__drawer-item q-my-sm" 
                  :class="{ 'sidebar-active': route().current('dashboard') && !isDarkMode, 'sidebar-active-dark': route().current('dashboard') && isDarkMode }"
                >
                  <q-item-section avatar>
                    <q-icon name="dashboard" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Dashboard</q-item-label>
                  </q-item-section>
                </q-item>
              </Link>
  
              <Link :href="route('map')">
                <q-item 
                  clickable 
                  class="GPL__drawer-item q-my-sm" 
                  :class="{ 'sidebar-active': route().current('map') && !isDarkMode, 'sidebar-active-dark': route().current('map') && isDarkMode }"
                >
                  <q-item-section avatar>
                    <q-icon name="map" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Stray Map</q-item-label>
                  </q-item-section>
                </q-item>
              </Link>
  
              <Link :href="route('registeredpets')">
                <q-item 
                  clickable 
                  class="GPL__drawer-item q-my-sm" 
                  :class="{ 'sidebar-active': route().current('registeredpets') && !isDarkMode, 'sidebar-active-dark': route().current('registeredpets') && isDarkMode }"
                >
                  <q-item-section avatar>
                    <q-icon name="pets" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Registered Pets</q-item-label>
                  </q-item-section>
                </q-item>
              </Link>
  
              <Link :href="route('cctv.monitor')">
                <q-item 
                  clickable 
                  class="GPL__drawer-item q-my-sm" 
                  :class="{ 'sidebar-active': route().current('cctv.monitor') && !isDarkMode, 'sidebar-active-dark': route().current('cctv.monitor') && isDarkMode }"
                >
                  <q-item-section avatar>
                    <q-icon name="videocam" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>CCTV Monitor</q-item-label>
                  </q-item-section>
                </q-item>
              </Link>
              <q-separator class="q-my-md" />
  
              <Link :href="route('profile.edit')">
                <q-item clickable class="GPL__drawer-item" :active="route().current('profile.edit')" :active-class="isDarkMode ? 'sidebar-active-dark' : 'sidebar-active'">
                  <q-item-section avatar>
                    <q-icon name="fa-solid fa-user" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>Profile Page</q-item-label>
                  </q-item-section>
                </q-item>
              </Link>

              <!-- Dark Mode Toggle -->
              <q-item clickable class="GPL__drawer-item" @click="toggleDarkMode">
                <q-item-section avatar>
                  <q-icon :name="isDarkMode ? 'light_mode' : 'dark_mode'" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ isDarkMode ? 'Light Mode' : 'Dark Mode' }}</q-item-label>
                </q-item-section>
              </q-item>

              <!-- Replace the Link component with q-item for logout -->
              <q-item clickable class="GPL__drawer-item" @click="handleLogout">
                <q-item-section avatar>
                  <q-icon name="logout" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Logout</q-item-label>
                </q-item-section>
              </q-item>
   
  
            </q-list>
          </q-scroll-area>
        </q-drawer>
  
        <q-page-container :class="['page-content-container', {'dark-page': isDarkMode}]">
          <slot :search="search" />
        </q-page-container>
      </q-layout>
    </div>
  </template>
<style scoped>
.custom-drawer {
  background-color: var(--bg-light);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.dark-drawer {
  background-color: var(--bg-dark);
  color: var(--text-primary);
}

.GPL__drawer-item {
  color: inherit;
  transition: all 0.3s ease;
}

.dark-drawer .GPL__drawer-item {
  color: var(--text-primary);
}

.dark-drawer .GPL__drawer-item:hover {
  background-color: var(--bg-secondary);
}

.sidebar-active {
  background-color: var(--accent-light);
  color: white;
}

.sidebar-active-dark {
  background-color: var(--accent-dark);
  color: var(--text-primary);
}

.page-content-container {
  padding-top: 20px; /* Adds space above the content */
}

.custom-text {
    color: var(--surface-900); 
    font-weight: 700; 
    font-size: 1.5rem; 
    line-height: 2rem;
}
.custom-color{
    color: #4f6642;
}
.bg-website{
    background-color: #F5F5DC;
}
.text-brand {
    color: #a2aa33 !important;
}
.bg-navbar {
    background: white !important;
}

.bg-buttons {
    background: #efd6d5 !important;
}

.bg-base-200 {
    background-color: #f5f5f5;
}

.file-input {
    width: 100%;
    max-width: 500px;
}

.max-w-full {
    max-width: 90%;
}

.max-w-half {
    max-width: 50%;
}


.shadow-lg {
    box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
}

.p-10 {
    padding: 2.5rem;
}

.p-8 {
    padding: 2rem;
}

.instagram-card-2 {
    width: 90vh;
    border: 1px solid #ddd;
    border-radius: 10px;
    box-shadow: 12px 17px 51px rgba(0, 0, 0, 0.22);
    margin: 0 auto;
    margin-bottom: 20px;
    backdrop-filter: blur(6px);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.5s;
    user-select: none;
    font-weight: bolder;
    color: black;
    background: white;
    font-family: "Poppins", sans-serif;
}

/* Dark mode styles */
.bg-dark {
  background-color: #121212;
}

.dark-drawer {
  background-color: var(--bg-dark);
  color: var(--text-primary);
}

.dark-page {
  background-color: #121212;
}

/* Ensure the content inside the drawer does not break the rounded corners */
.drawer-content {
  border-radius: inherit;
  overflow: hidden;
}

.drawer-content:not(.dark-drawer) {
  background: var(--bg-light) !important;
}

.dark-drawer .drawer-content {
  background: var(--bg-dark) !important;
}

/* Dark mode overrides for Quasar components */
.body--dark .q-drawer {
  background-color: var(--bg-dark);
}

.body--dark .q-item {
  color: var(--text-primary);
}

.body--dark .q-separator {
  background-color: var(--bg-secondary);
}

.body--dark .q-card {
  background-color: var(--bg-dark);
}
</style>
