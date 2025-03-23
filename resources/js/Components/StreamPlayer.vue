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
import { ref, onMounted, onUnmounted, watch } from 'vue';
import Hls from 'hls.js';

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

    // Function to get proxied stream URL
    const getProxiedUrl = (url) => {
      // If the URL is already a Flask server URL, return it as is
      if (url.includes('/video/') || url.includes('localhost:5000') || url.includes('127.0.0.1:5000')) {
        console.log('Using direct Flask video URL:', url);
        return url;
      }
      
      // Check if this is already a local URL
      if (url.includes('/stream/')) {
        return url;
      }
      
      // Convert external URL to our proxy URL
      // Example: http://20.195.42.135:8888/ai_cam1/index.m3u8 -> /stream/ai_cam1/index.m3u8
      const urlParts = url.split('://');
      if (urlParts.length < 2) return url;
      
      const hostAndPath = urlParts[1].split('/');
      if (hostAndPath.length < 2) return url;
      
      // Remove the host (e.g., 20.195.42.135:8888) and join the rest
      const pathParts = hostAndPath.slice(1);
      return `/stream/${pathParts.join('/')}`;
    };

    // Function to initialize HLS player
    const initializePlayer = () => {
      loading.value = true;
      error.value = null;

      if (!videoElement.value) {
        error.value = 'Video element not found';
        loading.value = false;
        emit('stream-error', error.value);
        return;
      }

      // Clean up existing HLS instance if any
      if (hls.value) {
        hls.value.destroy();
        hls.value = null;
      }
      
      // Get the proxied URL
      const proxiedUrl = getProxiedUrl(props.streamUrl);
      console.log(`Using stream URL: ${proxiedUrl}`);
      
      // For local Flask server, we don't need authentication
      const isLocalFlaskUrl = proxiedUrl.includes('localhost:5000') || 
                              proxiedUrl.includes('127.0.0.1:5000') || 
                              proxiedUrl.includes('/video/');
      
      if (!isLocalFlaskUrl) {
        // Log authentication details for non-local streams
        console.log(`Authentication: username=${props.username}, password=${props.password}`);
      }

      // Check if the URL is a direct video stream (not HLS)
      const isDirectVideoStream = proxiedUrl.includes('/video/');
      
      // If it's a direct video stream from Flask, use the video element directly
      if (isDirectVideoStream && videoElement.value) {
        try {
          console.log('Using direct video stream from Flask');
          videoElement.value.src = proxiedUrl;
          videoElement.value.addEventListener('loadeddata', () => {
            loading.value = false;
            emit('stream-ready');
          });
          
          videoElement.value.addEventListener('error', (e) => {
            error.value = `Video playback error: ${e.message || 'Stream not available'}`;
            loading.value = false;
            emit('stream-error', error.value);
          });
          
          return;
        } catch (e) {
          console.error('Error setting up direct video stream:', e);
          // Fall back to HLS if direct stream fails
        }
      }

      // Check if HLS.js is supported
      if (!Hls.isSupported()) {
        // Try native playback with authentication
        if (videoElement.value.canPlayType('application/vnd.apple.mpegurl')) {
          videoElement.value.src = proxiedUrl;
          
          videoElement.value.addEventListener('loadedmetadata', () => {
            loading.value = false;
            emit('stream-ready');
          });
          
          videoElement.value.addEventListener('error', (e) => {
            error.value = `Native playback error: ${e.message || 'Authentication failed or stream not available'}`;
            loading.value = false;
            emit('stream-error', error.value);
          });
        } else {
          error.value = 'HLS is not supported in this browser';
          loading.value = false;
          emit('stream-error', error.value);
        }
        return;
      }

      // Configure HLS.js
      const hlsConfig = {
        debug: false,
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90,
        // No need for authentication headers as our proxy handles that
      };

      try {
        // Create HLS instance
        hls.value = new Hls(hlsConfig);

        // Bind events
        hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
          console.log('HLS: Media attached');
        });

        hls.value.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
          console.log(`HLS: Manifest parsed, found ${data.levels.length} quality levels`);
          loading.value = false;
          emit('stream-ready');
        });

        hls.value.on(Hls.Events.ERROR, (event, data) => {
          console.log('HLS error:', data);
          
          // Log more detailed error information
          if (data.details) {
            console.log(`HLS error details: ${data.details}`);
          }
          
          if (data.response) {
            console.log(`HLS response: status=${data.response.code}, url=${data.response.url}`);
          }
          
          if (data.error) {
            console.log(`HLS error message: ${data.error.message}`);
            console.log(`HLS error stack: ${data.error.stack}`);
          }
          
          if (data.type === 'networkError') {
            console.log('HLS network error, trying to recover');
            
            // For network errors, try a different authentication approach
            if (data.details === 'manifestLoadError' && data.response && data.response.code === 401) {
              console.log('Authentication failed, trying alternative method');
              
              // Try with a different authentication method
              const alternativeUrl = props.streamUrl.replace('http://', 'http://');
              hls.value.loadSource(alternativeUrl);
              
              // Also try with explicit headers
              const authString = `${props.username}:${props.password}`;
              const encodedAuth = btoa(authString);
              console.log(`Using Basic Auth header: ${encodedAuth}`);
            }
          }
          
          if (data.fatal) {
            switch(data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                console.error('HLS network error, trying to recover');
                hls.value.startLoad();
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                console.error('HLS media error, trying to recover');
                hls.value.recoverMediaError();
                break;
              default:
                console.error('HLS fatal error, cannot recover');
                error.value = `Stream error: ${data.details}. This may be due to authentication failure or the stream is not available.`;
                loading.value = false;
                emit('stream-error', error.value);
                break;
            }
          }
        });

        // Load source and attach media
        hls.value.loadSource(proxiedUrl);
        hls.value.attachMedia(videoElement.value);
      } catch (e) {
        error.value = `Failed to initialize player: ${e.message}`;
        loading.value = false;
        emit('stream-error', error.value);
      }
    };

    // Function to retry connection
    const retryConnection = () => {
      console.log('Retrying stream connection...');
      initializePlayer();
    };

    // Function to retry with alternative authentication method
    const retryWithAlternativeMethod = () => {
      console.log('Retrying with alternative authentication method...');
      error.value = null;
      loading.value = true;
      
      // Try different authentication methods
      const authMethods = [
        // Method 1: Direct URL with embedded credentials
        () => {
          const url = props.streamUrl.replace('http://', `http://${props.username}:${props.password}@`);
          console.log('Trying method 1: URL with embedded credentials', url);
          return url;
        },
        // Method 2: Direct URL without credentials but with Authorization header
        () => {
          console.log('Trying method 2: URL without credentials but with Authorization header');
          // This is handled in the xhrSetup function
          return props.streamUrl;
        },
        // Method 3: Try with a different format of the URL
        () => {
          const url = props.streamUrl.replace('http://', 'http://');
          console.log('Trying method 3: Alternative URL format', url);
          return url;
        }
      ];
      
      // Get the current method index from a data attribute
      const methodIndex = parseInt(videoElement.value.dataset.methodIndex || '0');
      const nextMethodIndex = (methodIndex + 1) % authMethods.length;
      
      // Store the method index for next retry
      videoElement.value.dataset.methodIndex = nextMethodIndex.toString();
      
      // Get the URL from the next method
      const url = authMethods[nextMethodIndex]();
      
      // Clean up existing HLS instance if any
      if (hls.value) {
        hls.value.destroy();
        hls.value = null;
      }
      
      // Initialize a new HLS instance
      try {
        hls.value = new Hls(hlsConfig);
        
        // Set up event handlers
        hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
          console.log('HLS: Media attached');
          hls.value.loadSource(url);
        });
        
        // Attach to the video element
        hls.value.attachMedia(videoElement.value);
      } catch (e) {
        error.value = `Failed to initialize player: ${e.message}`;
        loading.value = false;
        emit('stream-error', error.value);
      }
    };

    // Initialize on mount
    onMounted(() => {
      initializePlayer();
    });

    // Clean up on unmount
    onUnmounted(() => {
      if (hls.value) {
        hls.value.destroy();
        hls.value = null;
      }
    });

    // Watch for changes in stream URL
    watch(() => props.streamUrl, () => {
      initializePlayer();
    });

    return {
      videoElement,
      loading,
      error,
      retryConnection,
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
  object-fit: cover;
}

.hidden {
  display: none;
}

.loading-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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

.error-container {
  color: #ff6b6b;
  text-align: center;
  padding: 20px;
}

.error-container i {
  font-size: 2rem;
  margin-bottom: 10px;
}

.retry-button {
  margin-top: 15px;
  padding: 8px 16px;
  background-color: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.retry-button:hover {
  background-color: #3a7bc8;
}
</style>
