<script setup>
import { onMounted, ref } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import axios from 'axios';

const mapContainer = ref(null);
const map = ref(null);
const mapboxToken = 'pk.eyJ1IjoiMS1heWFub24iLCJhIjoiY20ycnAzZW5pMWZpZTJpcThpeTJjdDU1NCJ9.7AVb_LJf6sOtb-QAxwR-hg';

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

  // Fetch initial pins
  fetchPins();
});

// Function to fetch pins from the backend
async function fetchPins() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/pins');
    const pins = response.data;
    pins.forEach(pin => {
      addMarker(pin.coordinates, pin.animal_type, pin.snapshot_path);
    });
  } catch (error) {
    console.error('Error fetching pins:', error);
  }
}

// Function to add markers based on animal type
function addMarker(coordinates, animalType, snapshotPath) {
  const marker = document.createElement('div');
  marker.className = `custom-marker ${animalType}`;

  if (snapshotPath) {
    const img = document.createElement('img');
    img.src = `http://127.0.0.1:8000/${snapshotPath}`;
    img.alt = 'Animal Snapshot';
    img.style.width = '50px';
    img.style.height = '50px';
    marker.appendChild(img);
  }

  new mapboxgl.Marker(marker)
    .setLngLat(coordinates)
    .addTo(map.value);
}
</script>

<template>
  <div class="map-container-wrapper">
    <div class="map-container" ref="mapContainer"></div>
  </div>
</template>

<style src="../../css/map.css"></style>
