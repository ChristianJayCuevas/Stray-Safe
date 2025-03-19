# StreamPlayer Component

A reusable Vue component for playing HLS streams with authentication.

## Features

- Automatic HLS stream playback using HLS.js
- Built-in authentication support via Laravel proxy
- CORS handling through a server-side proxy
- Error handling with retry functionality
- Loading indicators
- Responsive design
- Event emitters for stream status

## Usage

### Basic Usage

```vue
<template>
  <div class="stream-container">
    <StreamPlayer 
      stream-url="/stream/ai_cam1/index.m3u8"
      @stream-ready="onStreamReady"
      @stream-error="onStreamError"
    />
  </div>
</template>

<script setup>
import StreamPlayer from '@/Components/StreamPlayer.vue';

function onStreamReady() {
  console.log('Stream is ready to play');
}

function onStreamError(error) {
  console.error('Stream error:', error);
}
</script>

<style>
.stream-container {
  width: 100%;
  height: 400px;
}
</style>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| streamUrl | String | required | The URL of the HLS stream (.m3u8) |
| autoplay | Boolean | true | Whether to autoplay the stream |
| muted | Boolean | true | Whether to mute the stream |

### Events

| Event | Description | Payload |
|-------|-------------|---------|
| stream-ready | Emitted when the stream is ready to play | None |
| stream-error | Emitted when an error occurs | Error message |

## Stream URLs

The following stream URLs are available:

- Original HLS Streams: `http://20.195.42.135:8888/[stream_name]/index.m3u8`
- Proxied HLS Streams: `/stream/[stream_name]/index.m3u8`
- RTSP Streams: `rtsp://20.195.42.135:8554/[stream_name]`

## Authentication

The streams require Basic Authentication with the following credentials:
- Username: `user`
- Password: `Straysafeteam3`

However, when using the proxied URLs (`/stream/...`), the authentication is handled automatically by the Laravel backend, so you don't need to provide credentials in the frontend.

## CORS Handling

To handle CORS (Cross-Origin Resource Sharing) issues, the application uses a Laravel proxy that:

1. Receives requests from the browser at `/stream/[stream_name]/index.m3u8`
2. Makes authenticated requests to the original stream server
3. Returns the stream content to the browser with proper CORS headers

This approach avoids CORS issues entirely since the browser is only making requests to your own domain.

## Example

A complete example can be found in the `StreamTest.vue` page, which demonstrates how to use the StreamPlayer component with authentication.

To view the example, navigate to `/stream-test` in your browser.
