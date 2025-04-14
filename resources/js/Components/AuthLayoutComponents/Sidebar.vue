<script setup>
import { ref, computed, inject, defineEmits } from 'vue';
import { Link, usePage, router } from '@inertiajs/vue3';
import { useQuasar } from 'quasar';

const drawer = ref(false);
const miniState = ref(true);
const emit = defineEmits();
const $q = useQuasar();
const isDarkMode = inject('isDarkMode', ref(true));

const { auth } = usePage().props;
const authUser = computed(() => auth.user || null);

const hasAdminAccess = computed(() => {
  return authUser.value?.permissions?.includes('manage_roles') || 
         authUser.value?.permissions?.includes('manage_users') ||
         authUser.value?.permissions?.includes('manage_referral_codes');
});

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
  localStorage.setItem('darkMode', isDarkMode.value);
  $q.dark.set(isDarkMode.value);
};

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
  <q-drawer
    v-model="drawer"
    show-if-above
    :mini="miniState"
    @mouseover="miniState = false"
    @mouseout="miniState = true"
    :width="220"
    :breakpoint="500"
    :class="['custom-drawer', { 'dark-drawer': isDarkMode }]"
    behavior="desktop"
  >
    <q-scroll-area class="fit drawer-content" :horizontal-thumb-style="{ opacity: 0 }">
      <q-list padding>
        <!-- Logo -->
        <q-item class="q-pa-md">
          <q-item-section avatar>
            <img src="/storage/images/NEWLOGO.png" class="w-10 h-10" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="text-2xl custom-text font-bold font-poppins">
              <span :class="{'dark-mode-stray': isDarkMode}">Stray</span><span :class="{'dark-mode-safe': isDarkMode, 'custom-color': !isDarkMode}">Safe</span>
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-separator class="q-my-md" :dark="isDarkMode" />

        <!-- Links -->
        <Link v-for="item in [
          { name: 'Dashboard', route: 'dashboard', icon: 'dashboard' },
          { name: 'Stray Map', route: 'map', icon: 'map' },
          { name: 'Registered Pets', route: 'registeredpets', icon: 'pets' },
          { name: 'CCTV Monitor', route: 'cctv.monitor', icon: 'videocam' }
        ]" :key="item.route" :href="route(item.route)">
          <q-item 
            clickable 
            class="GPL__drawer-item q-my-sm"
            :class="{
              'sidebar-active': route().current(item.route) && !isDarkMode,
              'sidebar-active-dark': route().current(item.route) && isDarkMode
            }"
          >
            <q-item-section avatar>
              <q-icon :name="item.icon" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.name }}</q-item-label>
            </q-item-section>
          </q-item>
        </Link>

        <!-- Admin -->
        <template v-if="hasAdminAccess">
          <q-separator class="q-my-md" />
          <Link v-for="item in [
            { name: 'Role Management', route: 'admin.roles', icon: 'admin_panel_settings' },
            { name: 'Users & Access', route: 'admin.users', icon: 'people' },
            { name: 'Referral Codes', route: 'admin.referral-codes', icon: 'qr_code' },
            { name: 'Map Management', route: 'admin.maps', icon: 'map' },
            { name: 'User Areas', route: 'user.areas', icon: 'edit_location_alt' }
          ]" :key="item.route" :href="route(item.route)">
            <q-item 
              clickable 
              class="GPL__drawer-item q-my-sm"
              :class="{
                'sidebar-active': route().current(item.route) && !isDarkMode,
                'sidebar-active-dark': route().current(item.route) && isDarkMode
              }"
            >
              <q-item-section avatar>
                <q-icon :name="item.icon" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ item.name }}</q-item-label>
              </q-item-section>
            </q-item>
          </Link>
        </template>

        <q-separator class="q-my-md" />

        <!-- Profile, Theme, Logout -->
        <Link :href="route('profile.edit')">
          <q-item clickable class="GPL__drawer-item" :class="{ 'sidebar-active-dark': route().current('profile.edit') &&  isDarkMode, 'sidebar-active': route().current('profile.edit') && !isDarkMode }">
            <q-item-section avatar>
              <q-icon name="fa-solid fa-user" />
            </q-item-section>
            <q-item-section>
              <q-item-label>Profile Page</q-item-label>
            </q-item-section>
          </q-item>
        </Link>

        <q-item clickable class="GPL__drawer-item" @click="toggleDarkMode">
          <q-item-section avatar>
            <q-icon :name="isDarkMode ? 'light_mode' : 'dark_mode'" />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ isDarkMode ? 'Light Mode' : 'Dark Mode' }}</q-item-label>
          </q-item-section>
        </q-item>

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
</template>
<style scoped>
.custom-drawer {
  background-color: var(--bg-light);
  color: var(--text-primary);
  transition: all 0.3s ease;
  box-shadow: var(--card-shadow-light);
}

.dark-drawer {
  background-color: var(--bg-dark);
  color: var(--text-primary);
}

.GPL__drawer-item {
  color: inherit;
  transition: all 0.3s ease;
  border-radius: 8px;
  margin: 4px 8px;
}
.GPL__drawer-item:hover:not(.sidebar-active):not(.sidebar-active-dark) {
  background-color: rgba(46, 139, 87, 0.1);
  transform: translateX(5px);
  box-shadow: 0 2px 4px rgba(46, 139, 87, 0.05);
}
.dark-drawer .GPL__drawer-item {
  color: var(--text-primary);
}

.dark-drawer .GPL__drawer-item:hover:not(.sidebar-active):not(.sidebar-active-dark) {
  background-color: rgba(59, 130, 246, 0.1);
  transform: translateX(5px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.05);
}
.sidebar-active {
  background-color: #2e8b57;
  color: white;
  box-shadow: 0 2px 5px rgba(46, 139, 87, 0.2);
  border-radius: 8px;
  margin: 4px 8px;
  font-weight: 600;
  transform: translateX(3px);
}

.sidebar-active-dark {
  background-color: var(--accent-dark);
  color: white;
  box-shadow: 0 2px 5px rgba(59, 130, 246, 0.2);
  border-radius: 8px;
  margin: 4px 8px;
  font-weight: 600;
  transform: translateX(3px);
}
.page-content-container {
  padding-top: 20px; /* Adds space above the content */
}

.custom-text {
    color: var(--text-primary-light); 
    font-weight: 700; 
    font-size: 1.5rem; 
    line-height: 2rem;
}
.custom-color{
    color: var(--accent-color-light);
    font-weight: bold;
}
.bg-website{
    background-color: #f5f7fa;
}
.text-brand {
    color: #2e8b57 !important;
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
    border-radius: 8px;
    box-shadow: var(--card-shadow-light);
    margin: 0 auto;
    margin-bottom: 20px;
    backdrop-filter: blur(6px);
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

.custom-drawer {
  height: 100%;
  box-shadow: var(--card-shadow-light);
}

.light-drawer {
  background-color: var(--bg-light);
}

.custom-logo {
  padding: 1.5rem;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--stroke);
}

.custom-logo img {
  height: 40px;
  filter: drop-shadow(0px 2px 4px rgba(91, 110, 225, 0.2));
  transition: all 0.3s ease;
}

.dark .custom-logo img {
  filter: drop-shadow(0px 2px 4px rgba(94, 234, 212, 0.2));
}

.dark-mode-stray {
    color: white;
    font-weight: bold;
}

.dark-mode-safe {
    color: #7dd3fc; /* Light blue color */
    font-weight: bold;
}
</style>