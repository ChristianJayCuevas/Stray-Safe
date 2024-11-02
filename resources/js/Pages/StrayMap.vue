<script setup>
import Map from '@/Components/MapComponent.vue';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
</script>
<template>
    <AuthenticatedLayout>
        <div class="text-container-normal">
            <p class="text-title">Barangay Sacred Heart</p>
        </div>
        <div>
            <Map />
        </div>
    </AuthenticatedLayout>
</template>
<style src="../../css/text.css"></style>