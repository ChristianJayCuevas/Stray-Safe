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
  </div>
</template>
<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import Hls from 'hls.js'

const props = defineProps({
  streamUrl: {
    type: String,
    required: true
  },
  maxRetries: {
    type: Number,
    default: 3
  }
})

const videoElement = ref(null)
const hls = ref(null)
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')
const retryCount = ref(0)
const segmentCount = ref(0)

function getFreshUrl(url) {
  const timestamp = Date.now()
  return url.includes('?') ? `${url}&t=${timestamp}` : `${url}?t=${timestamp}`
}

function initializeHls(url) {
  if (hls.value) {
    hls.value.destroy()
    hls.value = null
  }

  isLoading.value = true
  hasError.value = false
  errorMessage.value = ''
  segmentCount.value = 0

  if (Hls.isSupported()) {
    hls.value = new Hls()
    hls.value.attachMedia(videoElement.value)

    hls.value.on(Hls.Events.MEDIA_ATTACHED, () => {
      console.log('HLS media attached, loading source:', url)
      hls.value.loadSource(url)
    })

    hls.value.on(Hls.Events.MANIFEST_PARSED, () => {
      console.log('HLS manifest parsed')
      isLoading.value = false
      retryCount.value = 0
      videoElement.value.play().catch((err) => {
        console.warn('Autoplay failed:', err)
      })
    })

    hls.value.on(Hls.Events.FRAG_LOADED, () => {
      segmentCount.value++
      if (segmentCount.value >= 4) {
        console.log('Refreshing stream after 4 segments...')
        segmentCount.value = 0
        const refreshedUrl = getFreshUrl(props.streamUrl)
        initializeHls(refreshedUrl)
      }
    })

    hls.value.on(Hls.Events.ERROR, (event, data) => {
      console.error('HLS.js error:', data.type, data.details)

      if (data.fatal) {
        if (data.type === Hls.ErrorTypes.NETWORK_ERROR || data.details.includes('FRAG_LOAD')) {
          if (retryCount.value < props.maxRetries) {
            retryCount.value++
            const retryDelay = 1000 * retryCount.value
            console.log(`Retrying stream... attempt ${retryCount.value}, delay: ${retryDelay}ms`)
            setTimeout(() => {
              const refreshedUrl = getFreshUrl(props.streamUrl)
              initializeHls(refreshedUrl)
            }, retryDelay)
          } else {
            hasError.value = true
            errorMessage.value = 'Stream failed after multiple attempts.'
          }
        } else {
          hasError.value = true
          errorMessage.value = 'Fatal stream error occurred.'
        }
      }
    })
  } else if (videoElement.value.canPlayType('application/vnd.apple.mpegurl')) {
    videoElement.value.src = url
    videoElement.value.addEventListener('loadedmetadata', () => {
      isLoading.value = false
      videoElement.value.play().catch(() => {})
    })
  } else {
    hasError.value = true
    errorMessage.value = 'Your browser does not support HLS streaming.'
  }
}

onMounted(() => {
  const initialUrl = getFreshUrl(props.streamUrl)
  initializeHls(initialUrl)
})

onUnmounted(() => {
  if (hls.value) {
    hls.value.destroy()
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
</style>
