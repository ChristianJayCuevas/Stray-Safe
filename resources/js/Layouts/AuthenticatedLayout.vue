<script setup>
import { ref, computed, onMounted, defineEmits, provide, watch } from "vue";
import { Link, usePage, router } from "@inertiajs/vue3";
import { useQuasar } from 'quasar';
import Sidebar from '@/Components/AuthLayoutComponents/Sidebar.vue';
const { auth } = usePage().props;
const authUser = computed(() => auth.user || null);
console.log("auth.user:", auth.user);
console.log("User Permissions:", authUser.value?.permissions);
console.log("User Roles:", authUser.value?.roles);

const drawer = ref(false);
const miniState = ref(true);
const search = ref('');
const $q = useQuasar();

const isDarkMode = ref(localStorage.getItem('darkMode') === 'true' || localStorage.getItem('darkMode') === null);

onMounted(() => {
  // If darkMode isn't set in localStorage yet, set it to true (default)
  if (localStorage.getItem('darkMode') === null) {
    localStorage.setItem('darkMode', 'true');
  }
  applyDarkMode(isDarkMode.value);
});

function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value;
  localStorage.setItem('darkMode', isDarkMode.value);
  applyDarkMode(isDarkMode.value);
}

function applyDarkMode(isDark) {
  $q.dark.set(isDark);
  
  if (isDark) {
    document.body.classList.add('dark-mode');
  } else {
    document.body.classList.remove('dark-mode');
  }
}

watch(isDarkMode, (newValue) => {
  applyDarkMode(newValue);
});

provide('isDarkMode', isDarkMode);

const emit = defineEmits();

const handleLogout = () => {
  $q.dialog({
    title: 'Confirm Logout',
    message: 'Are you sure you want to logout?',
    cancel: true,
    persistent: true
  }).onOk(() => {
    router.post(route('logout'));
  }).onCancel(() => {
    console.log('Logout cancelled');
  });
};

const hasAdminAccess = computed(() => {
  return authUser.value?.permissions?.includes('manage_roles') || 
         authUser.value?.permissions?.includes('manage_users') ||
         authUser.value?.permissions?.includes('manage_referral_codes');
});
</script>
<template>
    <div :class="{'bg-website': !isDarkMode, 'bg-dark': isDarkMode}">
      <q-layout view="hHh lpR fFf">
        <Sidebar />
  
        <q-page-container :class="['page-content-container', {'dark-page': isDarkMode}]">
          <slot :search="search" />
        </q-page-container>
      </q-layout>
    </div>
  </template>
<style scoped>
.page-content-container {
  padding-top: 20px;
}

</style>
