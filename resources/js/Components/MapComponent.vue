<script setup>
import { onMounted, ref } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import axios from 'axios';

// Map container and instance
const mapContainer = ref(null);
const map = ref(null);
const pinsList = ref([]); // Stores the list of pins
const newPin = ref({ animalType: '', snapshotPath: '', coordinates: [] }); // For adding a new pin
const selectedPinType = ref(''); // Tracks the currently selected pin type

// Mapbox token
const mapboxToken = 'pk.eyJ1IjoiMS1heWFub24iLCJhIjoiY20ycnAzZW5pMWZpZTJpcThpeTJjdDU1NCJ9.7AVb_LJf6sOtb-QAxwR-hg';

// Fetch pins from the backend and populate the map
onMounted(() => {
  if (!mapContainer.value) return;

  mapboxgl.accessToken = mapboxToken;

  // Initialize Mapbox map
  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: 'mapbox://styles/1-ayanon/cm2rp9idm00as01qwcq9ihoyr',
    center: [121.039295, 14.631141],
    zoom: 15.5,
  });

  // Add navigation control
  map.value.addControl(new mapboxgl.NavigationControl(), 'top-right');

  // Fetch initial pins
  fetchPins();

  // Enable manual pin addition by clicking on the map
  map.value.on('click', (e) => {
    if (!selectedPinType.value) {
      alert('Please select a pin type before adding a pin.');
      return;
    }

    const { lng, lat } = e.lngLat;
    addPinManually({
      coordinates: [lng, lat],
      animalType: selectedPinType.value === 'paw' ? 'Paw' : 'CCTV',
      snapshotPath: '',
    });
  });
});

// Fetch pins from the backend
async function fetchPins() {
  try {
    // Use a relative route to fetch data
    const response = await axios.get('/api/pins');
    const pins = response.data;

    // Add each pin to the map
    pins.forEach((pin) => {
      addMarker(pin.coordinates, pin.animal_type, pin.snapshot_path);
      pinsList.value.push({
        coordinates: pin.coordinates,
        animalType: pin.animal_type,
        snapshotPath: pin.snapshot_path,
      });
    });
  } catch (error) {
    console.error('Error fetching pins:', error);
  }
}

// Add markers to the map
function addMarker(coordinates, animalType, snapshotPath) {
  const marker = document.createElement('div');
  marker.className = `custom-marker ${animalType}`;

  // Add different icons for Paw and CCTV pins
  const icon = document.createElement('i');
  if (animalType === 'Paw') {
    icon.className = 'fa-solid fa-paw'; // Font Awesome class for the paw icon
    icon.style.color = 'white'; // Optional: Change the icon color
  } else if (animalType === 'CCTV') {
    icon.className = 'fa-solid fa-video'; // Font Awesome class for the CCTV icon
    icon.style.color = 'white'; // Optional: Change the icon color
  }
  icon.style.fontSize = '24px'; // Optional: Adjust the size of the icon
  marker.appendChild(icon);

  // Add the marker to the map
  new mapboxgl.Marker(marker).setLngLat(coordinates).addTo(map.value);
}

// Add a pin manually
function addPinManually({ coordinates, animalType, snapshotPath }) {
  // Add the pin to the map
  addMarker(coordinates, animalType, snapshotPath);

  // Add the pin to the list
  pinsList.value.push({
    coordinates,
    animalType,
    snapshotPath,
  });

  console.log('New pin added:', { coordinates, animalType, snapshotPath });
}

// Set the selected pin type
function selectPinType(type) {
  selectedPinType.value = type;
  console.log(`Selected pin type: ${type}`);
}
</script>

<template>
  <div class="map-container-wrapper">
    <!-- Map Container -->
    <div class="map-container" ref="mapContainer"></div>

    <!-- Controls -->
    <div class="controls">
      <button @click="selectPinType('paw')">Add Paw Pin</button>
      <button @click="selectPinType('cctv')">Add CCTV Pin</button>
    </div>
  </div>
</template>


<style src="../../css/map.css"></style>
