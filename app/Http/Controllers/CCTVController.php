<?php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use App\Models\CCTV;
use Inertia\Inertia;

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
        // Load custom CCTVs from the database
        $customCCTVs = CCTV::all();
        
        return inertia('CCTVMonitor', [
            'initialCustomCCTVs' => $customCCTVs
        ]);
    }
    
    /**
     * Store a new custom CCTV.
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'location' => 'nullable|string|max:255',
            'stream_url' => 'required|string|max:255',
            'original_stream_id' => 'nullable|string|max:255',
        ]);
        
        $cctv = CCTV::create([
            'name' => $validated['name'],
            'location' => $validated['location'],
            'stream_url' => $validated['stream_url'],
            'original_stream_id' => $validated['original_stream_id'],
            'status' => 'Online',
            'is_custom' => true,
        ]);
        
        return response()->json([
            'success' => true,
            'message' => 'CCTV created successfully',
            'cctv' => $cctv
        ]);
    }
    
    /**
     * Get all custom CCTVs.
     */
    public function getCustomCCTVs()
    {
        $cctvs = CCTV::all();
        
        return response()->json([
            'success' => true,
            'cctvs' => $cctvs
        ]);
    }
    
    /**
     * Delete a custom CCTV.
     */
    public function destroy($id)
    {
        $cctv = CCTV::findOrFail($id);
        $cctv->delete();
        
        return response()->json([
            'success' => true,
            'message' => 'CCTV deleted successfully'
        ]);
    }
}