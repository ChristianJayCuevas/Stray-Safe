<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class DebugApiRequests
{
    /**
     * Handle an incoming request.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \Closure  $next
     * @return mixed
     */
    public function handle(Request $request, Closure $next)
    {
        // Log request details
        Log::channel('daily')->info('API Request', [
            'url' => $request->fullUrl(),
            'method' => $request->method(),
            'ip' => $request->ip(),
            'user_agent' => $request->userAgent(),
            'content_type' => $request->header('Content-Type'),
            'ajax' => $request->ajax(),
            'headers' => $request->headers->all(),
            'inputs' => $request->all(),
            'session_id' => session()->getId(),
            'csrf_token' => csrf_token(),
        ]);

        // Get the response
        $response = $next($request);

        // Log response details for errors
        if (!$response->isSuccessful()) {
            Log::channel('daily')->error('API Response Error', [
                'url' => $request->fullUrl(),
                'method' => $request->method(),
                'status' => $response->getStatusCode(),
                'content' => $response->getContent(),
            ]);
        }

        return $response;
    }
} 