<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;

class CCTVController extends Controller
{
    public function view()
    {
        return inertia('CCTVView');
    }

    public function detect(Request $request)
    {
        $file = $request->file('video');
        $response = Http::attach(
            'file', file_get_contents($file), $file->getClientOriginalName()
        )->post('http://127.0.0.1:8000/process-video/');

        $processedVideoPath = 'processed_video.mp4';
        Storage::put($processedVideoPath, $response->body());

        return response()->json(['video_url' => Storage::url($processedVideoPath)]);
    }

    public function monitor()
    {
        return inertia('CCTVMonitor');
    }
}