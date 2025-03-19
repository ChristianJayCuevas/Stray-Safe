<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class StreamProxyController extends Controller
{
    /**
     * Proxy for HLS stream requests to handle CORS and authentication
     */
    public function proxy(Request $request, $path = null)
    {
        // Base URL for the stream server
        $streamServer = 'http://20.195.42.135:8888';
        
        // Get the full path from the request
        $fullPath = $request->path();
        
        // Extract the part after 'stream-proxy/'
        $streamPath = substr($fullPath, strpos($fullPath, 'stream-proxy/') + 12);
        
        // Build the target URL
        $targetUrl = "{$streamServer}/{$streamPath}";
        
        try {
            // Make the request to the stream server with authentication
            $response = Http::withBasicAuth('user', 'Straysafeteam3')
                ->withHeaders([
                    'User-Agent' => $request->header('User-Agent'),
                    'Accept' => $request->header('Accept'),
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
            
            // Set CORS headers to allow requests from our application
            $proxyResponse->header('Access-Control-Allow-Origin', $request->header('Origin'));
            $proxyResponse->header('Access-Control-Allow-Methods', 'GET, OPTIONS');
            $proxyResponse->header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
            $proxyResponse->header('Access-Control-Allow-Credentials', 'true');
            
            return $proxyResponse;
        } catch (\Exception $e) {
            Log::error('Stream proxy error: ' . $e->getMessage());
            return response()->json(['error' => 'Failed to proxy stream'], 500);
        }
    }
    
    /**
     * Handle OPTIONS requests for CORS preflight
     */
    public function options(Request $request)
    {
        return response('', 200)
            ->header('Access-Control-Allow-Origin', $request->header('Origin'))
            ->header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            ->header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            ->header('Access-Control-Allow-Credentials', 'true')
            ->header('Access-Control-Max-Age', '86400'); // 24 hours
    }
}
