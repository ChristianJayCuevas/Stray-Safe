<script setup>
import { onMounted, ref } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css'; // Ensure mapbox styles load

const mapContainer = ref(null);
const map = ref(null);

// Replace with your Mapbox access token
const mapboxToken = 'pk.eyJ1IjoiMS1heWFub24iLCJhIjoiY20ycnAzZW5pMWZpZTJpcThpeTJjdDU1NCJ9.7AVb_LJf6sOtb-QAxwR-hg';

// Initialize map on mount
onMounted(() => {
  if (!mapContainer.value) return;

  mapboxgl.accessToken = mapboxToken;
  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: 'mapbox://styles/1-ayanon/cm2rp9idm00as01qwcq9ihoyr', // You can use different styles here
    center: [121.039295, 14.631141], // Set your default map center (e.g., Manila, Philippines)
    zoom: 15,
  });

  // Add navigation control (zoom buttons) to the map
  map.value.addControl(new mapboxgl.NavigationControl(), 'top-right');

  // Add marker
  addMarker([120.9822, 14.6042], 'custom-marker');
});

// Function to add a custom marker
function addMarker(coordinates, className) {
  const marker = document.createElement('div');
  marker.className = className;
  
  // Marker properties and event listener
  new mapboxgl.Marker(marker)
    .setLngLat(coordinates)
    .addTo(map.value);
}
</script>
<template>
    <div class="map-container" ref="mapContainer"></div>
  </template>
<style src="../../css/map.css"></style>