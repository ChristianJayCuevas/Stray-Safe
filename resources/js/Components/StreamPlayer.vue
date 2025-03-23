<template>
  <div class="stream-player-container" :class="{ 'loading': loading, 'error': error }">
    <div v-if="loading" class="loading-indicator">
      <q-spinner color="primary" size="3em" />
      <p>Loading stream...</p>
    </div>
    <div v-if="error" class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="retryWithAlternativeMethod" class="retry-button">Try Alternative Method</button>
    </div>
    <video
      ref="videoElement"
      class="video-player"
      playsinline
      :muted="muted"
      :autoplay="autoplay"
      :controls="controls"
    ></video>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, computed, inject } from 'vue';
import Hls from 'hls.js';
import axios from 'axios';

export default {
  name: 'StreamPlayer',
  props: {
    streamUrl: {
      type: String,
      required: true
    },
    streamId: {
      type: String,
      default: ''
    },
    username: {
      type: String,
      default: 'user' // Default username for the stream
    },
    password: {
      type: String,
      default: 'pass' // Default password for the stream
    },
    autoplay: {
      type: Boolean,
      default: true
    },
    muted: {
      type: Boolean,
      default: true
    },
    controls: {
      type: Boolean,
      default: false
    },
    maxRetries: {
      type: Number,
      default: 3
    },
    registerInstance: {
      type: Boolean,
      default: false
    },
    useExistingInstance: {
      type: Boolean,
      default: false
    }
  },
  emits: ['stream-ready', 'stream-error', 'register-instance'],
  setup(props, { emit }) {
    const videoElement = ref(null);
    const loading = ref(true);
    const error = ref(null);
    const hls = ref(null);
    const retryCount = ref(0);
    const retryTimeout = ref(null);
    
    // Get shared stream instances from parent component if available
    const activeStreamInstances = inject('activeStreamInstances', ref({}));
    const activeHlsInstances = inject('activeHlsInstances', ref({}));

    // Determine stream type
    const isHlsStream = computed(() => {
      return props.streamUrl.includes('.m3u8');
    });

    const isFlaskVideoStream = computed(() => {
      return props.streamUrl.includes('/video/');
    });

    // Function to get HLS URL from Flask video stream
    const getHlsUrl = async (videoUrl) => {
      try {
        // Extract stream ID from video URL
        const match = videoUrl.match(/\/video\/([^\/]+)/);
        if (!match) {
          throw new Error('Invalid video URL format');
        }
        
        const streamId = match[1];
        // Use the same server URL as the video URL
        const baseUrl = videoUrl.substring(0, videoUrl.indexOf('/video/'));
        const hlsUrl = `${baseUrl}/hls/${streamId}/playlist.m3u8`;
        
        // Verify HLS stream is accessible
        try {
          const response = await axios.head(hlsUrl);
          if (response.status === 200) {
            return hlsUrl;
          }
        } catch (error) {
          console.warn(`HLS stream not accessible at ${hlsUrl}, falling back to video stream`);
          return videoUrl;
        }
      } catch (err) {
        console.warn('Error getting HLS URL:', err);
        return videoUrl; // Fall back to original video URL
      }
    };

    // Function to initialize HLS player
    const initializeHls = (url) => {
      // Ensure URL uses same protocol as website
      const secureUrl = url.replace('http:', window.location.protocol);
      
      // Check if we should use an existing HLS instance
      if (props.useExistingInstance && props.streamId && activeHlsInstances.value[props.streamId]) {
        // Clean up any existing instance for this component
        if (hls.value && hls.value !== activeHlsInstances.value[props.streamId]) {
          hls.value.destroy();
          hls.value = null;
        }
        
        // Use the existing HLS instance
        const existingHls = activeHlsInstances.value[props.streamId];
        
        // Create a new media source for this player that shares the same stream
        hls.value = new Hls({
          ...existingHls.config,
          liveSyncDurationCount: 3,
          liveMaxLatencyDurationCount: 5,
          liveDurationInfinity: true,
          enableWorker: true,
          lowLatencyMode: true,
          maxBufferLength: 10,
          maxMaxBufferLength: 15,
          startLevel: -1, // Auto quality selection
          debug: false
        });
        
        // Attach to our video element
        if (videoElement.value) {
          hls.value.attachMedia(videoElement.value);
          hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
            // Use the same source as the existing stream
            hls.value.loadSource(secureUrl);
            
            // Sync with the existing player's time
            const existingVideo = activeStreamInstances.value[props.streamId];
            if (existingVideo) {
              const syncInterval = setInterval(() => {
                if (Math.abs(videoElement.value.currentTime - existingVideo.currentTime) > 0.3) {
                  videoElement.value.currentTime = existingVideo.currentTime;
                }
              }, 1000);
              
              onUnmounted(() => {
                clearInterval(syncInterval);
              });
            }
            
            videoElement.value.play().catch(() => {
              // Autoplay failed, user interaction needed
            });
          });
        }
        
        loading.value = false;
        emit('stream-ready');
        return;
      }
      
      // Clean up existing HLS instance if any
      if (hls.value) {
        hls.value.destroy();
        hls.value = null;
      }
      
      // Check if HLS.js is supported
      if (Hls.isSupported()) {
        hls.value = new Hls({
          enableWorker: true,
          lowLatencyMode: true,
          backBufferLength: 30,
          maxBufferLength: 10,
          maxMaxBufferLength: 15,
          maxBufferSize: 15 * 1000 * 1000,
          maxBufferHole: 0.3,
          liveSyncDurationCount: 3,
          liveMaxLatencyDurationCount: 5,
          liveDurationInfinity: true,
          startLevel: -1, // Auto quality selection
          debug: false
        });
        
        hls.value.attachMedia(videoElement.value);
        hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
          hls.value.loadSource(secureUrl);
          hls.value.url = secureUrl;
          
          hls.value.on(Hls.Events.MANIFEST_PARSED, () => {
            videoElement.value.play().catch(() => {
              // Autoplay failed, user interaction needed
            });
            loading.value = false;
            retryCount.value = 0;
            emit('stream-ready');
            
            if (props.registerInstance && props.streamId) {
              emit('register-instance', props.streamId, videoElement.value, hls.value);
            }
          });
        });
        
        // Enhanced error handling
        hls.value.on(Hls.Events.ERROR, (event, data) => {
          if (data.fatal) {
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                if (data.response?.code === 403) {
                  error.value = 'Access denied to stream';
                  emit('stream-error', error.value);
                } else {
                  hls.value.startLoad();
                }
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                hls.value.recoverMediaError();
                break;
              default:
                if (retryCount.value < props.maxRetries) {
                  retryCount.value++;
                  
                  if (retryTimeout.value) {
                    clearTimeout(retryTimeout.value);
                  }
                  
                  const delay = Math.min(1000 * Math.pow(2, retryCount.value - 1), 10000);
                  retryTimeout.value = setTimeout(() => {
                    initializePlayer();
                  }, delay);
                } else {
                  error.value = `Stream playback error`;
                  emit('stream-error', error.value);
                }
                break;
            }
          }
        });
      } else if (videoElement.value.canPlayType('application/vnd.apple.mpegurl')) {
        // For Safari and iOS devices which have built-in HLS support
        videoElement.value.src = secureUrl;
        videoElement.value.addEventListener('loadedmetadata', () => {
          videoElement.value.play().catch(() => {
            // Autoplay failed, user interaction needed
          });
          loading.value = false;
          emit('stream-ready');
          
          if (props.registerInstance && props.streamId) {
            emit('register-instance', props.streamId, videoElement.value, null);
          }
        });
        
        videoElement.value.addEventListener('error', () => {
          if (retryCount.value < props.maxRetries) {
            retryCount.value++;
            const delay = Math.min(1000 * Math.pow(2, retryCount.value - 1), 10000);
            setTimeout(() => {
              initializePlayer();
            }, delay);
          } else {
            error.value = 'Stream playback error';
            emit('stream-error', error.value);
          }
        });
      } else {
        error.value = 'HLS playback not supported in this browser';
        emit('stream-error', error.value);
      }
    };

    // Function to initialize player
    const initializePlayer = async () => {
      // Check if we should use an existing video element
      if (props.useExistingInstance && props.streamId && activeStreamInstances.value[props.streamId]) {
        console.log(`Using existing video instance for stream ${props.streamId}`);
        
        // If we have a video element and it's different from the existing one
        if (videoElement.value) {
          // If there's an HLS instance, use it
          if (activeHlsInstances.value[props.streamId]) {
            console.log(`Using existing HLS instance for stream ${props.streamId}`);
            
            // Clean up any existing instance for this component
            if (hls.value && hls.value !== activeHlsInstances.value[props.streamId]) {
              hls.value.destroy();
              hls.value = null;
            }
            
            // Use the existing HLS instance
            hls.value = activeHlsInstances.value[props.streamId];
            
            // Clone the stream instead of detaching from the original
            // This allows both players to show the same stream simultaneously
            hls.value.attachMedia(videoElement.value);
            videoElement.value.play().catch(e => {
              console.warn('Auto-play failed:', e);
            });
          } else {
            // For non-HLS streams, we need to clone the stream
            const existingVideo = activeStreamInstances.value[props.streamId];
            videoElement.value.src = existingVideo.src;
            
            // Try to sync the time position
            videoElement.value.currentTime = existingVideo.currentTime;
            videoElement.value.play().catch(e => {
              console.warn('Auto-play failed:', e);
            });
          }
          
          loading.value = false;
          emit('stream-ready');
        }
        
        return;
      }
      
      loading.value = true;
      error.value = null;

      try {
        if (!props.streamUrl) {
          throw new Error('No stream URL provided');
        }
        
        console.log('StreamPlayer mounted with URL:', props.streamUrl);
        
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
            
            // Register this instance if requested
            if (props.registerInstance && props.streamId) {
              emit('register-instance', props.streamId, videoElement.value, null);
            }
          });
          
          videoElement.value.addEventListener('error', () => {
            if (retryCount.value < props.maxRetries) {
              retryCount.value++;
              console.log(`Retry attempt ${retryCount.value}/${props.maxRetries}`);
              
              // Retry with exponential backoff
              const delay = Math.min(1000 * Math.pow(2, retryCount.value - 1), 10000);
              setTimeout(() => {
                console.log(`Retrying stream after ${delay}ms delay`);
                initializePlayer();
              }, delay);
            } else {
              error.value = 'Error loading video stream';
              emit('stream-error', error.value);
            }
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
      if (isHlsStream.value || isFlaskVideoStream.value) {
        // If HLS failed, try direct video URL
        const videoUrl = props.streamUrl.replace('/hls/', '/video/').replace('/playlist.m3u8', '');
        console.log('Retrying with direct video URL:', videoUrl);
        videoElement.value.src = videoUrl;
        videoElement.value.play().catch(e => {
          console.warn('Auto-play failed:', e);
          error.value = 'Failed to play stream with alternative method';
          emit('stream-error', error.value);
        });
      } else {
        // If direct video failed, try HLS
        try {
          const hlsUrl = props.streamUrl.replace('/video/', '/hls/') + '/playlist.m3u8';
          console.log('Retrying with HLS URL:', hlsUrl);
          initializeHls(hlsUrl);
        } catch (err) {
          console.error('Error retrying with alternative method:', err);
          error.value = 'Failed to play stream with alternative method';
          emit('stream-error', error.value);
        }
      }
    };

    // Initialize player on mount
    onMounted(() => {
      console.log('StreamPlayer mounted with URL:', props.streamUrl);
      if (videoElement.value) {
        initializePlayer();
      }
    });

    // Clean up on unmount
    onUnmounted(() => {
      console.log('StreamPlayer unmounted');
      
      // Only destroy the HLS instance if we're not using a shared instance
      // or if we're the "owner" of the shared instance
      if (hls.value && (!props.useExistingInstance || 
          (props.registerInstance && props.streamId && 
           activeHlsInstances.value[props.streamId] === hls.value))) {
        hls.value.destroy();
        hls.value = null;
        
        // Remove from active instances if this is the registered instance
        if (props.registerInstance && props.streamId) {
          delete activeHlsInstances.value[props.streamId];
          delete activeStreamInstances.value[props.streamId];
        }
      }
      
      if (retryTimeout.value) {
        clearTimeout(retryTimeout.value);
      }
    });

    // Watch for changes to stream URL
    watch(() => props.streamUrl, (newUrl, oldUrl) => {
      console.log('Stream URL changed:', newUrl);
      if (newUrl !== oldUrl) {
        retryCount.value = 0; // Reset retry count
        initializePlayer();
      }
    });

    return {
      videoElement,
      loading,
      error,
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
  border-radius: 8px;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.loading-indicator, .error-message {
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

.loading-indicator p, .error-message p {
  margin-top: 10px;
  font-size: 14px;
}

.error-message i {
  font-size: 24px;
  color: #ff5252;
  margin-bottom: 10px;
}

.retry-button {
  margin-top: 10px;
  padding: 8px 16px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.retry-button:hover {
  background-color: #1565c0;
}
</style>
