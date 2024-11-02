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
    style: 'mapbox://styles/1-ayanon/cm2rp9idm00as01qwcq9ihoyr',
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
  <div class="map-container-wrapper">
    <div class="map-container" ref="mapContainer"></div>

    <!-- Pill Buttons for Pin Selection -->
    <div class="pin-selector">
      <button @click="selectPin('camera')" :class="{ active: selectedPin === 'camera' }">
        <q-icon name="videocam"></q-icon>
      </button>
      <button @click="selectPin('dog')" :class="{ active: selectedPin === 'dog' }">
        <q-icon name="pets"></q-icon>
      </button>
      <button @click="selectPin('cat')" :class="{ active: selectedPin === 'cat' }">
        <q-icon name="pets"></q-icon>
      </button>
    </div>
  </div>
</template>

<style src="../../css/map.css"></style>