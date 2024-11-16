<template>
  <div>
    <video ref="video" muted autoplay style="width: 100%; height: auto;"></video>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Hls from 'hls.js';

const video = ref(null);

onMounted(() => {
  const hlsUrl = '/hls/stream.m3u8';

  if (Hls.isSupported()) {
    const hls = new Hls();
    hls.loadSource(hlsUrl);
    hls.attachMedia(video.value);
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      video.value.play();
    });
  } else if (video.value.canPlayType('application/vnd.apple.mpegurl')) {
    // Fallback for Safari
    video.value.src = hlsUrl;
    video.value.addEventListener('loadedmetadata', () => {
      video.value.play();
    });
  }
});
</script>

<style scoped>
video {
  max-width: 100%;
  border: 1px solid #ddd;
}
</style>