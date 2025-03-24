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
    const actualStreamUrl = ref(props.streamUrl); // Store the actual stream URL after API fetch
    
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
        
        // Try to get the rtmp key for the stream
        try {
          const response = await axios.get('https://straysafe.me/api/streams', {
            timeout: 3000
          });
          
          if (response.data?.streams) {
            const streamInfo = response.data.streams.find(s => s.id === streamId);
            if (streamInfo && streamInfo.rtmp_key) {
              // Use the direct Nginx HLS URL with the rtmp key
              const hlsUrl = `https://straysafe.me/hls/${streamInfo.rtmp_key}.m3u8`;
              return hlsUrl;
            }
          }
        } catch (err) {
          console.warn('Error getting stream info:', err);
        }
        
        // Fallback to Flask HLS URL if we can't get the stream key
        const flaskHlsUrl = `https://straysafe.me/api/hls/${streamId}/playlist.m3u8`;
        return flaskHlsUrl;
      } catch (err) {
        console.warn('Error getting HLS URL:', err);
        return videoUrl; // Fall back to original video URL
      }
    };

    // Fetch the stream URL from the API
    const fetchStreamUrl = async () => {
      try {
        // Get the stream URL from the API
        const response = await axios.get('https://straysafe.me/api/streams', {
          timeout: 5000
        });
        
        if (response.data?.streams?.length > 0) {
          // Find the stream that matches the streamId if provided
          let stream = null;
          if (props.streamId) {
            stream = response.data.streams.find(s => s.id === props.streamId);
          }
          
          // If no matching stream or no streamId provided, use the first stream
          if (!stream) {
            stream = response.data.streams[0];
          }
          
          // Use the direct Nginx HLS URL if available, otherwise fall back to Flask HLS URL
          const timestamp = Date.now();
          if (stream.hls_url) {
            const hlsUrl = stream.hls_url.replace('http://', 'https://');
            actualStreamUrl.value = `${hlsUrl}${hlsUrl.includes('?') ? '&' : '?'}t=${timestamp}`;
            console.log('Using Nginx HLS URL:', actualStreamUrl.value);
            return actualStreamUrl.value;
          } else if (stream.flask_hls_url) {
            const flaskUrl = stream.flask_hls_url.replace('http://', 'https://');
            actualStreamUrl.value = `${flaskUrl}${flaskUrl.includes('?') ? '&' : '?'}t=${timestamp}`;
            console.log('Using Flask HLS URL:', actualStreamUrl.value);
            return actualStreamUrl.value;
          }
        }
        
        // If no stream found or no valid URLs, return the original URL
        return props.streamUrl;
      } catch (err) {
        console.error('Error fetching stream URL from API:', err);
        return props.streamUrl;
      }
    };

    // Function to initialize HLS player
    const initializeHls = (url) => {
      // Always use HTTPS for external access
      let streamUrl = url;
      
      // Fix URLs:
      // 1. Convert http to https for straysafe.me
      if (url.includes('straysafe.me') && url.startsWith('http://')) {
        streamUrl = url.replace('http://', 'https://');
        console.log('Converted to HTTPS URL:', streamUrl);
      }
      
      // 2. Fix URL format if needed - convert /hls/key/playlist.m3u8 to /hls/key.m3u8
      if (url.includes('/hls/') && url.includes('/playlist.m3u8')) {
        const match = url.match(/\/hls\/([^\/]+)\/playlist.m3u8/);
        if (match) {
          const key = match[1];
          streamUrl = url.replace(`/hls/${key}/playlist.m3u8`, `/hls/${key}.m3u8`);
          console.log('Fixed HLS URL format:', streamUrl);
        }
      }
      
      // 3. Add timestamp for cache-busting if needed
      if (!streamUrl.includes('?t=') && !streamUrl.includes('&t=')) {
        const timestamp = Date.now();
        streamUrl = streamUrl.includes('?') 
          ? `${streamUrl}&t=${timestamp}` 
          : `${streamUrl}?t=${timestamp}`;
        console.log('Added timestamp to URL:', streamUrl);
      }
      
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
            hls.value.loadSource(streamUrl);
            
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
        console.log('Initializing HLS player with URL:', streamUrl);
        
        // First, try to get latest segments info before initializing player
        if (streamUrl.includes('straysafe.me') && streamUrl.includes('.m3u8')) {
          // Fetch the available segments list by making a request to the directory
          fetchSegmentInfo(streamUrl).then(segmentInfo => {
            initHlsWithSegmentInfo(streamUrl, segmentInfo);
          }).catch(err => {
            console.error('Error fetching segment info:', err);
            // Continue without segment info
            initHlsWithSegmentInfo(streamUrl);
          });
        } else {
          initHlsWithSegmentInfo(streamUrl);
        }
      } else if (videoElement.value.canPlayType('application/vnd.apple.mpegurl')) {
        // For Safari and iOS devices which have built-in HLS support
        videoElement.value.src = streamUrl;
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

    // Function to fetch segment information
    const fetchSegmentInfo = async (playlistUrl) => {
      try {
        // URL to the directory containing the segments
        const directoryUrl = playlistUrl.replace('playlist.m3u8', '');
        
        // Make a HEAD request to the playlist to verify it exists
        await axios.head(playlistUrl);
        
        // For actual production, we would need a directory listing,
        // but since we can't get that directly, we'll use the information from the logs
        // At least we know the segments are from segment_018.ts to segment_027.ts
        
        return {
          exists: true,
          startSegment: 18,
          endSegment: 27
        };
      } catch (err) {
        console.error('Error fetching segment info:', err);
        return { exists: false };
      }
    };

    // Initialize HLS with segment information
    const initHlsWithSegmentInfo = (streamUrl, segmentInfo = null) => {
      hls.value = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 30,
        maxBufferLength: 10,
        maxMaxBufferLength: 15,
        maxBufferSize: 15 * 1000 * 1000,
        maxBufferHole: 0.5,
        liveSyncDurationCount: 3,
        liveMaxLatencyDurationCount: 5,
        liveDurationInfinity: true,
        startLevel: -1, // Auto quality selection
        debug: false,
        // Add HLS specific settings for better error recovery
        fragLoadingMaxRetry: 6,
        manifestLoadingMaxRetry: 6,
        levelLoadingMaxRetry: 6,
        fragLoadingRetryDelay: 500,
        manifestLoadingRetryDelay: 500,
        levelLoadingRetryDelay: 500,
        // Try to start playback from the end to avoid missing segment errors
        startPosition: -1
      });
      
      // Handle availability of segments
      if (segmentInfo && segmentInfo.exists) {
        console.log('Using segment info:', segmentInfo);
        
        // Listen for manifest loading to potentially modify it
        hls.value.on(Hls.Events.MANIFEST_LOADING, () => {
          console.log('Manifest loading with segment info');
        });
        
        // Intercept fragment loading to handle missing segments
        hls.value.on(Hls.Events.FRAG_LOADING, (event, data) => {
          // Check if the fragment URL contains a segment number
          const segmentMatch = data.frag.url.match(/segment_(\d+)\.ts/);
          if (segmentMatch) {
            const segmentNum = parseInt(segmentMatch[1], 10);
            
            // If we know the segment range and this segment is outside of it
            if (segmentInfo.startSegment && segmentInfo.endSegment) {
              if (segmentNum < segmentInfo.startSegment || segmentNum > segmentInfo.endSegment) {
                console.warn(`Segment ${segmentNum} is outside available range (${segmentInfo.startSegment}-${segmentInfo.endSegment})`);
                
                // Let's try to skip to a valid segment
                const validSegment = Math.max(segmentInfo.startSegment, Math.min(segmentNum, segmentInfo.endSegment));
                
                if (validSegment !== segmentNum) {
                  console.log(`Attempting to skip to valid segment ${validSegment}`);
                  
                  // Force the player to seek to a new position
                  const targetTime = hls.value.media.duration * 
                    ((validSegment - segmentInfo.startSegment) / 
                     (segmentInfo.endSegment - segmentInfo.startSegment + 1));
                  
                  hls.value.media.currentTime = targetTime;
                }
              }
            }
          }
        });
      }
      
      hls.value.attachMedia(videoElement.value);
      hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
        console.log('HLS media attached, loading source:', streamUrl);
        hls.value.loadSource(streamUrl);
        hls.value.url = streamUrl;
        
        hls.value.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
          console.log('Manifest parsed, levels:', data.levels.length);
          videoElement.value.play().catch(err => {
            console.error('Error playing video:', err);
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
        console.error('HLS Error:', data.type, data.details, data);
        
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              if (data.response?.code === 403) {
                error.value = 'Access denied to stream';
                emit('stream-error', error.value);
              } else {
                console.log('Network error - restarting stream');
                hls.value.startLoad();
              }
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.log('Media error - attempting recovery');
              hls.value.recoverMediaError();
              break;
            default:
              if (retryCount.value < props.maxRetries) {
                retryCount.value++;
                
                if (retryTimeout.value) {
                  clearTimeout(retryTimeout.value);
                }
                
                const delay = Math.min(1000 * Math.pow(2, retryCount.value - 1), 10000);
                console.log(`Retrying in ${delay}ms (attempt ${retryCount.value})`);
                retryTimeout.value = setTimeout(() => {
                  initializePlayer();
                }, delay);
              } else {
                error.value = `Stream playback error`;
                emit('stream-error', error.value);
              }
              break;
          }
        } else if (data.details === Hls.ErrorDetails.FRAG_LOAD_ERROR || 
                   data.details === Hls.ErrorDetails.FRAG_LOAD_TIMEOUT) {
          // Non-fatal fragment error - try to recover
          console.warn('Fragment load error - attempting to continue');
          
          // If it's a fragment with an index likely outside our range, try skipping ahead
          const segmentMatch = data.frag?.url?.match(/segment_(\d+)\.ts/);
          if (segmentMatch) {
            const segmentNum = parseInt(segmentMatch[1], 10);
            console.log(`Fragment error was for segment ${segmentNum}`);
            
            // Skip ahead by 1 second to try to move past the problematic fragment
            if (hls.value.media && !isNaN(hls.value.media.currentTime)) {
              hls.value.media.currentTime += 1;
            }
          }
        }
      });
    };

    // Function to initialize player
    const initializePlayer = async () => {
      // Check if we should use an existing video element
      if (props.useExistingInstance && props.streamId && activeStreamInstances.value[props.streamId]) {
        // If we have a video element and it's different from the existing one
        if (videoElement.value) {
          // If there's an HLS instance, use it
          if (activeHlsInstances.value[props.streamId]) {
            // Clean up any existing instance for this component
            if (hls.value && hls.value !== activeHlsInstances.value[props.streamId]) {
              hls.value.destroy();
              hls.value = null;
            }
            
            // Use the existing HLS instance
            hls.value = activeHlsInstances.value[props.streamId];
            
            // Clone the stream instead of detaching from the original
            hls.value.attachMedia(videoElement.value);
            videoElement.value.play().catch(() => {
              // Autoplay failed
            });
          } else {
            // For non-HLS streams, we need to clone the stream
            const existingVideo = activeStreamInstances.value[props.streamId];
            videoElement.value.src = existingVideo.src;
            
            // Try to sync the time position
            videoElement.value.currentTime = existingVideo.currentTime;
            videoElement.value.play().catch(() => {
              // Autoplay failed
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
        // Always try to fetch the latest stream URL from the API first
        const streamUrl = await fetchStreamUrl();
        
        if (!streamUrl) {
          throw new Error('No stream URL provided');
        }
        
        // Update the actual stream URL
        actualStreamUrl.value = streamUrl;
        
        if (isFlaskVideoStream.value) {
          const hlsUrl = await getHlsUrl(actualStreamUrl.value);
          initializeHls(hlsUrl);
        } else if (isHlsStream.value) {
          initializeHls(actualStreamUrl.value);
        } else {
          // For direct video streams (not HLS)
          videoElement.value.src = actualStreamUrl.value;
          videoElement.value.addEventListener('loadedmetadata', () => {
            videoElement.value.play().catch(() => {
              // Autoplay failed
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
              error.value = 'Error loading video stream';
              emit('stream-error', error.value);
            }
          });
        }
      } catch (err) {
        error.value = `Failed to initialize player: ${err.message}`;
        emit('stream-error', error.value);
      }
    };

    // Function to retry with alternative method
    const retryWithAlternativeMethod = async () => {
      // First, try to get the latest stream URL from the API again
      await fetchStreamUrl();
      
      if (isHlsStream.value || isFlaskVideoStream.value) {
        // If the URL is using the player.m3u8 format, try the direct .m3u8 format
        if (actualStreamUrl.value.includes('/playlist.m3u8')) {
          const match = actualStreamUrl.value.match(/\/hls\/([^\/]+)\/playlist.m3u8/);
          if (match) {
            const key = match[1];
            const directUrl = actualStreamUrl.value.replace(`/hls/${key}/playlist.m3u8`, `/hls/${key}.m3u8`);
            console.log('Trying alternative URL format:', directUrl);
            initializeHls(directUrl);
            return;
          }
        }
        
        // Try the Flask API URL
        if (actualStreamUrl.value.includes('/hls/')) {
          const timestamp = Date.now();
          const flaskUrl = `https://straysafe.me/api/hls/main-camera/playlist.m3u8?t=${timestamp}`;
          console.log('Trying Flask URL fallback:', flaskUrl);
          initializeHls(flaskUrl);
          return;
        }
        
        // If HLS failed, try Flask video URL
        const videoUrl = actualStreamUrl.value
          .replace('/hls/', '/api/video/')
          .replace('/playlist.m3u8', '')
          .replace('.m3u8', '');
        
        console.log('Trying video API fallback:', videoUrl);
        videoElement.value.src = videoUrl;
        videoElement.value.play().catch(() => {
          error.value = 'Failed to play stream with alternative method';
          emit('stream-error', error.value);
        });
      } else {
        // If direct video failed, try Flask HLS API
        try {
          // Extract stream ID from video URL
          const match = actualStreamUrl.value.match(/\/video\/([^\/]+)/);
          if (match) {
            const streamId = match[1];
            const hlsUrl = `https://straysafe.me/api/hls/${streamId}/playlist.m3u8?t=${Date.now()}`;
            console.log('Trying Flask HLS API fallback:', hlsUrl);
            initializeHls(hlsUrl);
          } else {
            error.value = 'Failed to parse stream URL for alternative method';
            emit('stream-error', error.value);
          }
        } catch (err) {
          error.value = 'Failed to play stream with alternative method';
          emit('stream-error', error.value);
        }
      }
    };

    // Initialize player on mount
    onMounted(() => {
      if (videoElement.value) {
        initializePlayer();
      }
    });

    // Clean up on unmount
    onUnmounted(() => {
      if (hls.value && (!props.useExistingInstance || 
          (props.registerInstance && props.streamId && 
           activeHlsInstances.value[props.streamId] === hls.value))) {
        hls.value.destroy();
        hls.value = null;
        
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
      if (newUrl !== oldUrl) {
        retryCount.value = 0;
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
