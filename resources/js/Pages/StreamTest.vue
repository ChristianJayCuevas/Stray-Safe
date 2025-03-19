<template>
  <div>
    <Head title="Stream Test" />
    <AuthenticatedLayout>
      <template #header>
        <h2 class="font-semibold text-xl text-gray-800 dark:text-gray-200 leading-tight">
          Stream Test
        </h2>
      </template>

      <div class="py-12">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
          <div class="bg-white dark:bg-gray-800 overflow-hidden shadow-sm sm:rounded-lg">
            <div class="p-6 text-gray-900 dark:text-gray-100">
              <h3 class="text-lg font-semibold mb-4">HLS Stream Test</h3>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div class="mb-2 font-medium">AI Camera Stream</div>
                  <div class="stream-container">
                    <StreamPlayer 
                      stream-url="/stream/ai_cam1/index.m3u8"
                      @stream-ready="onStreamReady"
                      @stream-error="onStreamError"
                    />
                  </div>
                </div>
              </div>

              <div class="mt-6">
                <h4 class="font-medium mb-2">Stream Information</h4>
                <div class="bg-gray-100 dark:bg-gray-700 p-4 rounded">
                  <p><strong>Original Stream URL:</strong> http://20.195.42.135:8888/ai_cam1/index.m3u8</p>
                  <p><strong>Proxied Stream URL:</strong> /stream/ai_cam1/index.m3u8</p>
                  <p><strong>Authentication:</strong> Handled by Laravel proxy</p>
                  <p><strong>Status:</strong> {{ streamStatus }}</p>
                </div>
              </div>

              <div class="mt-6">
                <h4 class="font-medium mb-2">Direct Video Test</h4>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  This is a direct video element with the proxied URL to test native browser playback.
                </p>
                <video 
                  src="/stream/ai_cam1/index.m3u8" 
                  controls 
                  autoplay 
                  muted 
                  class="w-full h-48 bg-black"
                ></video>
              </div>

              <div class="mt-6">
                <button 
                  @click="openStreamInBrowser" 
                  class="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded mr-2"
                >
                  Open Stream in Browser
                </button>
                
                <a 
                  href="/stream/ai_cam1/index.m3u8" 
                  target="_blank"
                  class="bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded"
                >
                  Test Direct URL
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AuthenticatedLayout>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Head } from '@inertiajs/vue3';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout.vue';
import StreamPlayer from '@/Components/StreamPlayer.vue';

const streamStatus = ref('Loading...');

function onStreamReady() {
  console.log('Stream is ready to play');
  streamStatus.value = 'Stream is playing';
}

function onStreamError(error) {
  console.error('Stream error:', error);
  streamStatus.value = `Error: ${error}`;
}

function openStreamInBrowser() {
  // Open the stream URL in a new browser tab
  window.open('/stream/ai_cam1/index.m3u8', '_blank');
}
</script>

<style scoped>
.stream-container {
  width: 100%;
  height: 400px;
  background-color: #000;
  border-radius: 8px;
  overflow: hidden;
}
</style>
