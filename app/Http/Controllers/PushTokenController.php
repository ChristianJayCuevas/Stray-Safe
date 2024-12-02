<?php

namespace App\Http\Controllers;

use App\Models\PushToken;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
class PushTokenController extends Controller
{
    public function saveToken(Request $request)
    {
        $request->validate(['token' => 'required|string|unique:push_tokens']);

        PushToken::create(['token' => $request->token]);

        return response()->json(['message' => 'Push token saved successfully']);
    }
    public function sendNotification(Request $request)
    {
        try {
            \Log::info('Incoming notification request', $request->all());
    
            $request->validate([
                'title' => 'required|string',
                'body' => 'required|string',
            ]);
    
            $tokens = PushToken::all()->pluck('token')->toArray();
            \Log::info('Fetched tokens', $tokens);
    
            if (empty($tokens)) {
                \Log::warning('No tokens available');
                return response()->json(['message' => 'No push tokens found'], 400);
            }
    
            $notifications = collect($tokens)->map(fn ($token) => [
                'to' => $token,
                'sound' => 'default',
                'title' => $request->title,
                'body' => $request->body,
            ])->toArray();
    
            $response = Http::post('https://exp.host/--/api/v2/push/send', $notifications);
            \Log::info('Expo API Response', ['status' => $response->status(), 'body' => $response->body()]);
    
            if ($response->successful()) {
                return response()->json(['message' => 'Notification sent successfully']);
            }
    
            return response()->json(['message' => 'Failed to send notification', 'details' => $response->body()], $response->status());
        } catch (\Exception $e) {
            \Log::error('Notification error', ['exception' => $e->getMessage()]);
            return response()->json(['message' => 'Internal server error'], 500);
        }
    }
}
