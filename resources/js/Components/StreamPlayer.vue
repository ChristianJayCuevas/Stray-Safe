<template>
  <div class="stream-player-container" :class="{ loading: isLoading, error: hasError }">
    <div v-if="isLoading" class="loading-indicator">
      <q-spinner color="primary" size="3em" />
      <p>Loading stream...</p>
    </div>
    <div v-if="hasError" class="error-message">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ errorMessage }}</p>
    </div>
    <video
      ref="videoElement"
      class="video-player"
      playsinline
      autoplay
      muted
      controls
    ></video>
    
    <!-- Advanced Controls Panel -->
    <div class="advanced-controls" v-if="videoElement">
      <!-- Playback Rate Controls -->
      <div class="control-section">
        <h4 class="control-title">Playback Speed</h4>
        <div class="playback-rate">
          <button 
            v-for="rate in playbackRates" 
            :key="rate" 
            @click="setPlaybackRate(rate)"
            :class="{ active: currentRate === rate }"
            class="rate-btn"
          >
            {{ rate === 1 ? 'Normal' : rate + 'x' }}
          </button>
        </div>
      </div>
      
      <!-- Quality Selector -->
      <div class="control-section" v-if="availableQualities.length > 1">
        <h4 class="control-title">Quality</h4>
        <div class="quality-selector">
          <select v-model="currentQuality" @change="changeQuality" class="quality-select">
            <option v-for="(quality, index) in availableQualities" :key="index" :value="index">
              {{ quality.height }}p{{ quality.bitrate ? ' (' + Math.round(quality.bitrate/1000) + 'kbps)' : '' }}
            </option>
            <option value="-1">Auto</option>
          </select>
        </div>
      </div>
      
      <!-- Stream Information -->
      <div class="control-section" v-if="streamInfo.url">
        <h4 class="control-title">Stream Info</h4>
        <div class="stream-info">
          <p class="info-item">Resolution: <span>{{ streamInfo.width }}x{{ streamInfo.height }}</span></p>
          <p class="info-item">Buffer: <span>{{ Math.round(bufferLength * 10) / 10 }}s</span></p>
          <p class="info-item">Latency: <span>{{ Math.round(latency * 10) / 10 }}s</span></p>
        </div>
      </div>

      <!-- Snapshot Button -->
      <div class="control-section">
        <button @click="takeSnapshot" class="snapshot-btn">
          <i class="fas fa-camera"></i> Take Snapshot
        </button>
      </div>
    </div>
    
    <!-- Control Toggle Button -->
    <button @click="toggleControls" class="toggle-controls-btn">
      <i :class="showAdvancedControls ? 'fas fa-times' : 'fas fa-sliders-h'"></i>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import Hls from 'hls.js'

const props = defineProps({
  streamUrl: {
    type: String,
    required: true
  },
  maxRetries: {
    type: Number,
    default: 3
  },
  initialPlaybackRate: {
    type: Number,
    default: 1
  },
  cameraName: {
    type: String,
    default: 'CCTV Camera'
  }
})

const emit = defineEmits(['snapshot'])

const videoElement = ref(null)
const hls = ref(null)
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')
const retryCount = ref(0)
let refreshInterval = null
let bufferCheckInterval = null

// Advanced controls state
const showAdvancedControls = ref(false)

// Playback rate control
const playbackRates = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2]
const currentRate = ref(props.initialPlaybackRate)

// Quality control
const availableQualities = ref([])
const currentQuality = ref(-1) // -1 means auto

// Stream metrics
const bufferLength = ref(0)
const latency = ref(0)
const streamInfo = ref({
  url: '',
  width: 0,
  height: 0,
  bitrate: 0
})

// Toggle advanced controls panel
function toggleControls() {
  showAdvancedControls.value = !showAdvancedControls.value
}

// Function to set playback rate
function setPlaybackRate(rate) {
  if (!videoElement.value) return
  
  currentRate.value = rate
  videoElement.value.playbackRate = rate
  
  // Store user preference
  try {
    localStorage.setItem('preferred-playback-rate', rate)
  } catch (e) {
    console.warn('Could not save playback rate preference to localStorage')
  }
}

// Function to change video quality
function changeQuality() {
  if (!hls.value) return
  
  const qualityIndex = currentQuality.value
  console.log(`Changing quality to index: ${qualityIndex}`)
  
  if (qualityIndex === -1) {
    // Auto mode
    hls.value.currentLevel = -1
    console.log('Set HLS to auto quality')
  } else {
    // Specific quality
    hls.value.currentLevel = qualityIndex
    console.log(`Set HLS to level: ${qualityIndex}`)
  }
  
  // Store user preference
  try {
    localStorage.setItem('preferred-quality', qualityIndex)
  } catch (e) {
    console.warn('Could not save quality preference to localStorage')
  }
}

// Take a snapshot of the current video frame
function takeSnapshot() {
  if (!videoElement.value) return
  
  // Create a canvas element
  const canvas = document.createElement('canvas')
  canvas.width = videoElement.value.videoWidth
  canvas.height = videoElement.value.videoHeight
  
  // Draw the current video frame to the canvas
  const ctx = canvas.getContext('2d')
  ctx.drawImage(videoElement.value, 0, 0, canvas.width, canvas.height)
  
  // Get the image data URL
  const imageDataUrl = canvas.toDataURL('image/png')
  
  // Emit the snapshot event with the image data
  emit('snapshot', {
    dataUrl: imageDataUrl,
    time: new Date().toISOString(),
    width: canvas.width,
    height: canvas.height,
    cameraName: props.cameraName || 'CCTV Camera'
  })
  
  // Optional: Download the image
  const link = document.createElement('a')
  link.href = imageDataUrl
  link.download = `snapshot-${new Date().toISOString().replace(/:/g, '-')}.png`
  link.click()
}

// Start monitoring buffer length and latency
function startMetricsMonitoring() {
  if (bufferCheckInterval) {
    clearInterval(bufferCheckInterval)
  }
  
  bufferCheckInterval = setInterval(() => {
    if (!videoElement.value || !hls.value) return
    
    // Update buffer length
    if (hls.value.media) {
      const buffered = hls.value.media.buffered
      if (buffered.length > 0) {
        const end = buffered.end(buffered.length - 1)
        const current = hls.value.media.currentTime
        bufferLength.value = end - current
      }
    }
    
    // Update latency if stream is live
    if (hls.value.liveSyncPosition) {
      latency.value = hls.value.liveSyncPosition - videoElement.value.currentTime
    }
  }, 1000)
}

function getFreshUrl(url) {
  return url.includes('?') ? `${url}` : `${url}`
}

function initializeHls(url) {
  if (hls.value) {
    hls.value.destroy()
    hls.value = null
  }

  isLoading.value = true
  hasError.value = false
  errorMessage.value = ''
  availableQualities.value = []
  streamInfo.value = { url: url, width: 0, height: 0, bitrate: 0 }

  if (Hls.isSupported()) {
    hls.value = new Hls({
      liveSyncDurationCount: 1,
      liveMaxLatencyDurationCount: 3,
      maxBufferLength: 10,
      maxMaxBufferLength: 20,
      lowLatencyMode: true,
      debug: false
    })
    hls.value.attachMedia(videoElement.value)

    hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
      console.log('HLS media attached, loading source:', url)
      hls.value.loadSource(url)
    })

    hls.value.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
      console.log('HLS manifest parsed', data)
      isLoading.value = false
      retryCount.value = 0

      // Get available qualities
      if (data.levels && data.levels.length > 0) {
        availableQualities.value = data.levels.map(level => ({
          height: level.height,
          width: level.width,
          bitrate: level.bitrate
        }))
        
        // Try to restore preferred quality
        try {
          const savedQuality = localStorage.getItem('preferred-quality')
          if (savedQuality !== null) {
            const parsedQuality = parseInt(savedQuality)
            if (!isNaN(parsedQuality) && 
                (parsedQuality === -1 || parsedQuality < availableQualities.value.length)) {
              currentQuality.value = parsedQuality
              changeQuality()
            }
          }
        } catch (e) {
          console.warn('Could not retrieve saved quality preference')
        }
      }

      // Start loading at the live edge
      hls.value.startLoad(-1)

      // Optional safety jump
      const liveSyncPosition = hls.value.liveSyncPosition
      if (liveSyncPosition) {
        videoElement.value.currentTime = liveSyncPosition
        console.log('Jumping to live sync position (MANIFEST_PARSED):', liveSyncPosition)
      }

      videoElement.value.play().catch(err => {
        console.warn('Autoplay failed:', err)
      })
      
      // Apply saved playback rate
      if (videoElement.value) {
        videoElement.value.playbackRate = currentRate.value
      }
      
      // Start metrics monitoring
      startMetricsMonitoring()
    })

    hls.value.on(Hls.Events.LEVEL_LOADED, (event, data) => {
      if (data.details.live) {
        const liveEdge = hls.value.liveSyncPosition
        if (liveEdge && videoElement.value) {
          console.log('Jumping to live sync position (LEVEL_LOADED):', liveEdge)
          videoElement.value.currentTime = liveEdge
        }
      }
      
      // Update stream info
      if (data.level !== undefined && data.level.details) {
        const level = hls.value.levels[data.level.level]
        if (level) {
          streamInfo.value = {
            url: url,
            width: level.width || 0,
            height: level.height || 0,
            bitrate: level.bitrate || 0
          }
        }
      }
    })

    hls.value.on(Hls.Events.ERROR, (event, data) => {
      console.error('HLS.js error:', data.type, data.details)
      if (data.fatal) {
        if (retryCount.value < props.maxRetries) {
          retryCount.value++
          const retryDelay = 1000 * retryCount.value
          console.log(`Retrying stream... attempt ${retryCount.value}, delay: ${retryDelay}ms`)
          setTimeout(() => {
            initializeHls(getFreshUrl(props.streamUrl))
          }, retryDelay)
        } else {
          hasError.value = true
          errorMessage.value = 'Stream failed after multiple attempts.'
        }
      }
    })
  } else if (videoElement.value.canPlayType('application/vnd.apple.mpegurl')) {
    videoElement.value.src = url
    videoElement.value.addEventListener('loadedmetadata', () => {
      isLoading.value = false
      videoElement.value.play().catch(() => {})
      
      // Apply saved playback rate
      if (videoElement.value) {
        videoElement.value.playbackRate = currentRate.value
      }
      
      // Basic stream info for native HLS
      streamInfo.value = {
        url: url,
        width: videoElement.value.videoWidth || 0,
        height: videoElement.value.videoHeight || 0
      }
    })
  } else {
    hasError.value = true
    errorMessage.value = 'Your browser does not support HLS streaming.'
  }
}

onMounted(() => {
  // Try to get saved playback rate
  try {
    const savedRate = localStorage.getItem('preferred-playback-rate')
    if (savedRate) {
      currentRate.value = parseFloat(savedRate)
    }
  } catch (e) {
    console.warn('Could not retrieve saved playback rate')
  }
  
  // Initialize stream
  initializeHls(getFreshUrl(props.streamUrl))
})

onUnmounted(() => {
  if (hls.value) {
    hls.value.destroy()
  }
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (bufferCheckInterval) {
    clearInterval(bufferCheckInterval)
  }
})

// Watch for changes in stream URL
watch(() => props.streamUrl, (newUrl) => {
  if (newUrl) {
    console.log('Stream URL changed, reinitializing player')
    initializeHls(getFreshUrl(newUrl))
  }
})
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

.loading-indicator,
.error-message {
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

.loading-indicator p,
.error-message p {
  margin-top: 10px;
  font-size: 14px;
}

.error-message i {
  font-size: 24px;
  color: #ff5252;
  margin-bottom: 10px;
}

/* Toggle controls button */
.toggle-controls-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 20;
  transition: background-color 0.2s;
}

.toggle-controls-btn:hover {
  background: rgba(50, 50, 50, 0.8);
}

/* Advanced controls panel */
.advanced-controls {
  position: absolute;
  top: 0;
  right: 0;
  width: 250px;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 50px 15px 15px;
  z-index: 15;
  overflow-y: auto;
  transition: transform 0.3s ease;
  transform: v-bind('showAdvancedControls ? "translateX(0)" : "translateX(100%)"');
  border-top-left-radius: 8px;
  border-bottom-left-radius: 8px;
}

.control-section {
  margin-bottom: 20px;
}

.control-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #ccc;
}

/* Playback rate controls */
.playback-rate {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.rate-btn {
  background: rgba(50, 50, 50, 0.7);
  border: 1px solid #666;
  color: white;
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.rate-btn:hover {
  background: rgba(80, 80, 80, 0.9);
}

.rate-btn.active {
  background: #4f6642;
  border-color: #38a3a5;
}

/* Quality selector */
.quality-select {
  width: 100%;
  padding: 6px;
  background: rgba(50, 50, 50, 0.7);
  color: white;
  border: 1px solid #666;
  border-radius: 3px;
  font-size: 12px;
}

/* Stream info */
.stream-info {
  font-size: 12px;
  color: #ccc;
}

.info-item {
  margin-bottom: 4px;
}

.info-item span {
  color: white;
  font-weight: 500;
}

/* Snapshot button */
.snapshot-btn {
  background: #38a3a5;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  transition: background-color 0.2s;
}

.snapshot-btn:hover {
  background: #2c7d7f;
}

.snapshot-btn i {
  font-size: 14px;
}
</style>
