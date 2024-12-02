<?php

namespace App\Http\Controllers;

use App\Models\PushToken;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
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
    $request->validate([
        'title' => 'required|string',
        'body' => 'required|string',
    ]);

    $tokens = PushToken::all()->pluck('token')->toArray();
    $message = [
        'to' => $tokens,
        'sound' => 'default',
        'title' => $request->title,
        'body' => $request->body,
    ];

    $response = Http::post('https://exp.host/--/api/v2/push/send', $message);

    if ($response->successful()) {
        return response()->json(['message' => 'Notification sent successfully']);
    }

    return response()->json(['message' => 'Failed to send notification'], 500);
}
}
