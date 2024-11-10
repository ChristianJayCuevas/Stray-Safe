<script setup>
import { onMounted, ref } from 'vue';

import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

const mapContainer = ref(null);
const map = ref(null);

const mapboxToken = 'pk.eyJ1IjoiMS1heWFub24iLCJhIjoiY20ycnAzZW5pMWZpZTJpcThpeTJjdDU1NCJ9.7AVb_LJf6sOtb-QAxwR-hg';
const selectedPin = ref('camera'); // Default pin type

// Initialize the map
onMounted(() => {
  if (!mapContainer.value) return;

  mapboxgl.accessToken = mapboxToken;
  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: 'mapbox://styles/1-ayanon/cm31ddt3r00ik01pqen9682zc',
    center: [121.039295, 14.631141],
    zoom: 15.5,
  });

  map.value.addControl(new mapboxgl.NavigationControl(), 'top-right');
});

// Function to add markers based on selected pin type
function addMarker(coordinates) {
  const marker = document.createElement('div');
  marker.className = `custom-marker ${selectedPin.value}`;

  new mapboxgl.Marker(marker)
    .setLngLat(coordinates)
    .addTo(map.value);
}

// Function to handle pin type selection
function selectPin(type) {
  selectedPin.value = type;
}

</script>

<template>
    <div class="heat-map-container-wrapper">
        <div class="heat-map-container" ref="mapContainer"></div>
    </div>
</template>

<style src="../../css/map.css"></style>