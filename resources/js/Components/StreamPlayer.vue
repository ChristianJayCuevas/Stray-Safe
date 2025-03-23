<template>
  <div class="stream-player-container">
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading stream...</p>
    </div>
    <div v-if="error" class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75 text-white p-4">
      <div class="text-center">
        <div class="text-red-500 mb-2">{{ error }}</div>
        <button 
          @click="retryWithAlternativeMethod" 
          class="bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded text-sm"
        >
          Try Alternative Method
        </button>
        <button 
          @click="initializePlayer" 
          class="bg-blue-500 hover:bg-blue-600 text-white py-1 px-3 rounded text-sm ml-2"
        >
          Retry
        </button>
      </div>
    </div>
    <!-- Use video element for all streams -->
    <video 
      ref="videoElement" 
      class="stream-video" 
      :class="{ hidden: loading || error }"
      playsinline
      :muted="muted"
      :autoplay="autoplay"
    ></video>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import Hls from 'hls.js';
import axios from 'axios';

export default {
  name: 'StreamPlayer',
  props: {
    streamUrl: {
      type: String,
      required: true
    },
    username: {
      type: String,
      default: 'user' // Default username for the stream
    },
    password: {
      type: String,
      default: 'Straysafeteam3' // Default password for the stream
    },
    autoplay: {
      type: Boolean,
      default: true
    },
    muted: {
      type: Boolean,
      default: true
    }
  },
  emits: ['stream-ready', 'stream-error'],
  setup(props, { emit }) {
    const videoElement = ref(null);
    const hls = ref(null);
    const loading = ref(true);
    const error = ref(null);
    
    // Check if the stream is a Flask video stream
    const isFlaskVideoStream = computed(() => {
      return props.streamUrl.includes('/video/') && 
             (props.streamUrl.includes('localhost:5000') || 
              props.streamUrl.includes('127.0.0.1:5000') || 
              props.streamUrl.includes('192.168.1.24:5000'));
    });

    // Check if the stream is an HLS stream
    const isHlsStream = computed(() => {
      return props.streamUrl.includes('.m3u8') || props.streamUrl.includes('/hls/');
    });

    // Function to get HLS URL from video endpoint
    const getHlsUrl = async (videoUrl) => {
      try {
        const response = await axios.get(videoUrl);
        if (response.data && response.data.hls_url) {
          // Convert relative URL to absolute URL if needed
          let hlsUrl = response.data.hls_url;
          if (hlsUrl.startsWith('/')) {
            const baseUrl = new URL(videoUrl);
            hlsUrl = `${baseUrl.protocol}//${baseUrl.host}${hlsUrl}`;
          }
          return hlsUrl;
        }
        throw new Error('No HLS URL found in response');
      } catch (err) {
        console.error('Error getting HLS URL:', err);
        throw err;
      }
    };

    // Function to initialize HLS player
    const initializeHls = (url) => {
      // Clean up existing HLS instance if any
      if (hls.value) {
        hls.value.destroy();
        hls.value = null;
      }
      
      // Check if HLS.js is supported
      if (Hls.isSupported()) {
        console.log('Using HLS.js for stream:', url);
        hls.value = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
          backBufferLength: 90
        });
        
        hls.value.attachMedia(videoElement.value);
        hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
          console.log('HLS media attached');
          hls.value.loadSource(url);
          
          hls.value.on(Hls.Events.MANIFEST_PARSED, () => {
            console.log('HLS manifest parsed');
            videoElement.value.play().catch(e => {
              console.warn('Auto-play failed:', e);
              // Some browsers require user interaction before playing
            });
            loading.value = false;
            emit('stream-ready');
          });
        });
        
        hls.value.on(Hls.Events.ERROR, (event, data) => {
          if (data.fatal) {
            console.error('Fatal HLS error:', data);
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                console.log('Network error, trying to recover...');
                hls.value.startLoad();
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                console.log('Media error, trying to recover...');
                hls.value.recoverMediaError();
                break;
              default:
                error.value = `HLS playback error: ${data.details}`;
                emit('stream-error', error.value);
                break;
            }
          }
        });
      } else if (videoElement.value.canPlayType('application/vnd.apple.mpegurl')) {
        // For Safari and iOS devices which have built-in HLS support
        console.log('Using native HLS support for stream:', url);
        videoElement.value.src = url;
        videoElement.value.addEventListener('loadedmetadata', () => {
          videoElement.value.play().catch(e => {
            console.warn('Auto-play failed:', e);
          });
          loading.value = false;
          emit('stream-ready');
        });
        
        videoElement.value.addEventListener('error', () => {
          error.value = 'Error loading video stream';
          emit('stream-error', error.value);
        });
      } else {
        error.value = 'HLS is not supported in this browser';
        emit('stream-error', error.value);
      }
    };

    // Function to initialize player
    const initializePlayer = async () => {
      loading.value = true;
      error.value = null;

      try {
        if (isFlaskVideoStream.value) {
          console.log('Flask video stream detected, fetching HLS URL');
          const hlsUrl = await getHlsUrl(props.streamUrl);
          console.log('Using HLS URL:', hlsUrl);
          initializeHls(hlsUrl);
        } else if (isHlsStream.value) {
          console.log('Direct HLS stream detected');
          initializeHls(props.streamUrl);
        } else {
          // For direct video streams (not HLS)
          console.log('Direct video stream detected');
          videoElement.value.src = props.streamUrl;
          videoElement.value.addEventListener('loadedmetadata', () => {
            videoElement.value.play().catch(e => {
              console.warn('Auto-play failed:', e);
            });
            loading.value = false;
            emit('stream-ready');
          });
          
          videoElement.value.addEventListener('error', () => {
            error.value = 'Error loading video stream';
            emit('stream-error', error.value);
          });
        }
      } catch (err) {
        console.error('Error initializing player:', err);
        error.value = `Failed to initialize player: ${err.message}`;
        emit('stream-error', error.value);
      }
    };

    // Function to retry with alternative method
    const retryWithAlternativeMethod = () => {
      error.value = null;
      loading.value = true;
      
      // Try with a different approach
      if (isFlaskVideoStream.value || isHlsStream.value) {
        // If we were using HLS, try direct video
        const directUrl = props.streamUrl.replace('/video/', '/video/direct/');
        videoElement.value.src = directUrl;
        videoElement.value.addEventListener('loadedmetadata', () => {
          videoElement.value.play().catch(e => {
            console.warn('Auto-play failed:', e);
          });
          loading.value = false;
          emit('stream-ready');
        });
        
        videoElement.value.addEventListener('error', () => {
          error.value = 'Error loading video stream with alternative method';
          emit('stream-error', error.value);
        });
      } else {
        // If we were using direct video, try HLS
        initializeHls(props.streamUrl.replace('.mp4', '.m3u8'));
      }
    };

    // Initialize on mount
    onMounted(() => {
      console.log('StreamPlayer mounted with URL:', props.streamUrl);
      initializePlayer();
    });
    
    // Clean up on unmount
    onUnmounted(() => {
      if (hls.value) {
        hls.value.destroy();
        hls.value = null;
      }
    });
    
    // Watch for changes to the streamUrl
    watch(() => props.streamUrl, (newUrl, oldUrl) => {
      if (newUrl !== oldUrl) {
        console.log('Stream URL changed, reinitializing player');
        initializePlayer();
      }
    });
    
    return {
      videoElement,
      loading,
      error,
      isFlaskVideoStream,
      isHlsStream,
      initializePlayer,
      retryWithAlternativeMethod
    };
  }
};
</script>

<style scoped>
.stream-player-container {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #000;
  overflow: hidden;
}

.stream-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background-color: #000;
}

.loading-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  z-index: 10;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top: 4px solid white;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.hidden {
  display: none;
}
</style>
