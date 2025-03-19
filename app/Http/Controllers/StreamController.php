<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Symfony\Component\HttpFoundation\StreamedResponse;

class StreamController extends Controller
{
    protected $streamBaseUrl = 'http://20.195.42.135:8888';
    protected $username = 'user';
    protected $password = 'Straysafeteam3';
    
    /**
     * Proxy an HLS stream segment
     */
    public function proxyStream(Request $request, $path)
    {
        $targetUrl = "{$this->streamBaseUrl}/{$path}";
        
        try {
            // Make the request to the stream server with authentication
            $response = Http::withBasicAuth($this->username, $this->password)
                ->withHeaders([
                    'User-Agent' => $request->header('User-Agent'),
                ])
                ->get($targetUrl);
            
            // Get the content type from the response
            $contentType = $response->header('Content-Type');
            
            // Create a response with the same content and content type
            $proxyResponse = response($response->body(), $response->status());
            
            // Set the content type
            if ($contentType) {
                $proxyResponse->header('Content-Type', $contentType);
            }
            
            // Set cache headers for m3u8 and ts files
            if (str_ends_with($path, '.m3u8')) {
                // Don't cache m3u8 files (they update frequently)
                $proxyResponse->header('Cache-Control', 'no-cache');
            } elseif (str_ends_with($path, '.ts')) {
                // Cache ts segments (they don't change)
                $proxyResponse->header('Cache-Control', 'public, max-age=31536000');
            }
            
            return $proxyResponse;
        } catch (\Exception $e) {
            Log::error('Stream proxy error: ' . $e->getMessage());
            return response()->json(['error' => 'Failed to proxy stream'], 500);
        }
    }
    
    /**
     * Get available streams
     */
    public function getStreams()
    {
        try {
            // In a real implementation, you would query the MediaMTX API
            // For now, we'll return a hardcoded list of streams
            return response()->json([
                'streams' => [
                    [
                        'id' => 'ai_cam1',
                        'name' => 'AI Camera 1',
                        'url' => '/stream/ai_cam1/index.m3u8',
                        'status' => 'active',
                    ]
                ]
            ]);
        } catch (\Exception $e) {
            Log::error('Failed to get streams: ' . $e->getMessage());
            return response()->json(['error' => 'Failed to get streams'], 500);
        }
    }
    
    /**
     * Test if a stream is accessible
     */
    public function testStream($streamId)
    {
        $targetUrl = "{$this->streamBaseUrl}/{$streamId}/index.m3u8";
        
        try {
            $response = Http::withBasicAuth($this->username, $this->password)
                ->get($targetUrl);
            
            if ($response->successful()) {
                return response()->json([
                    'status' => 'success',
                    'message' => 'Stream is accessible',
                    'url' => "/stream/{$streamId}/index.m3u8"
                ]);
            } else {
                return response()->json([
                    'status' => 'error',
                    'message' => 'Stream returned status code ' . $response->status(),
                ], 404);
            }
        } catch (\Exception $e) {
            Log::error('Stream test error: ' . $e->getMessage());
            return response()->json([
                'status' => 'error',
                'message' => 'Failed to access stream: ' . $e->getMessage()
            ], 500);
        }
    }
}
