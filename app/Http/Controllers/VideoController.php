<?php

use Illuminate\Http\Request;
use App\Models\Snapshot;
use App\Http\Controllers\Controller;
class VideoController extends Controller
{
    public function uploadVideo(Request $request)
    {
        $request->validate(['video' => 'required|mimes:mp4,mov,avi|max:20480']);
        $path = $request->file('video')->store('videos');
        
        // Call Python script to process video
        shell_exec("python3 process_video.py " . storage_path("app/$path"));

        return response()->json(['message' => 'Video uploaded and processed']);
    }

    public function storeSnapshot(Request $request)
    {
        $snapshot = new Snapshot();
        $snapshot->path = $request->path;
        $snapshot->save();

        return response()->json(['message' => 'Snapshot stored']);
    }

    public function getSnapshots()
    {
        return Snapshot::all();
    }
}
