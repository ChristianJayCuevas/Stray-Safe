<template>
    <div>
      <h1>CCTV View</h1>
      <input type="file" @change="uploadVideo" />
      <video v-if="videoUrl" :src="videoUrl" controls autoplay></video>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  
  const videoUrl = ref(null);
  
  const uploadVideo = async (event) => {
    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('video', file);
  
    const response = await fetch('/cctv/detect', {
      method: 'POST',
      body: formData,
    });
  
    const data = await response.json();
    videoUrl.value = data.video_url;
  };
  </script>