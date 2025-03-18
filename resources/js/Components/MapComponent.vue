<script setup>
import { onMounted, ref, inject } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import axios from 'axios';

// Get the global dark mode state
const isDarkMode = inject('isDarkMode', ref(false));

// Map container and instance
const mapContainer = ref(null);
const map = ref(null);
const pinsList = ref([]); // Stores the list of pins

// Mapbox token
const mapboxToken = 'pk.eyJ1IjoiMS1heWFub24iLCJhIjoiY20ycnAzZW5pMWZpZTJpcThpeTJjdDU1NCJ9.7AVb_LJf6sOtb-QAxwR-hg';

// Fetch pins from the backend and populate the map
onMounted(() => {
  if (!mapContainer.value) return;

  mapboxgl.accessToken = mapboxToken;

  // Initialize Mapbox map
  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: isDarkMode.value ? 'mapbox://styles/mapbox/dark-v10' : 'mapbox://styles/1-ayanon/cm2rp9idm00as01qwcq9ihoyr',
    center: [121.039295, 14.631141],
    zoom: 15.5,
  });

  // Add navigation control
  map.value.addControl(new mapboxgl.NavigationControl(), 'top-right');

  // Fetch initial pins
  fetchPins();
});

// Fetch pins from the backend
async function fetchPins() {
  try {
    // Use a relative route to fetch data
    const response = await axios.get('/api/pins');
    const pins = response.data;

    // Add each pin to the map
    pins.forEach((pin) => {
      addMarker(pin.coordinates, pin.animal_type);
      pinsList.value.push({
        coordinates: pin.coordinates,
        animalType: pin.animal_type
      });
    });
  } catch (error) {
    console.error('Error fetching pins:', error);
  }
}

// Add markers to the map
function addMarker(coordinates, animalType) {
  // Create a custom marker element
  const marker = document.createElement('div');
  marker.className = 'custom-marker';
  
  // Set different colors based on animal type
  if (animalType === 'Dog') {
    marker.style.backgroundColor = '#38a3a5'; // Dog color
  } else if (animalType === 'Cat') {
    marker.style.backgroundColor = '#57cc99'; // Cat color
  } else {
    marker.style.backgroundColor = '#4f6642'; // Default color
  }

  // Add the marker to the map
  new mapboxgl.Marker(marker).setLngLat(coordinates).addTo(map.value);
}
</script>

<template>
  <div class="map-container-wrapper">
    <!-- Map Container -->
    <div class="map-container" ref="mapContainer"></div>
  </div>
</template>

<style>
/* Map container styles */
.map-container-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  margin-bottom: 0px;
  height: 80vh;
  position: relative;
}

.map-container {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

/* Marker styles */
.custom-marker {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
  border: 2px solid white;
  transition: transform 0.2s ease;
}

.custom-marker:hover {
  transform: scale(1.2);
  cursor: pointer;
}
</style>
