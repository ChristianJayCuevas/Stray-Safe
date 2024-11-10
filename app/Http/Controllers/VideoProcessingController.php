<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Symfony\Component\Process\Process;
use Symfony\Component\Process\Exception\ProcessFailedException;
use Illuminate\Support\Facades\Storage;

class VideoProcessingController extends Controller
{

    public function processVideo(Request $request)
{
    try {
        $request->validate([
            'file' => 'required|file|mimes:mp4|max:20480',
        ]);

        $file = $request->file('file');
        $inputPath = $file->storeAs('videos', 'input_video.mp4');
        $outputPath = storage_path('app/videos/output_video_resized.mp4');

        $process = new Process(['python', 'D:\Project Design - Web App\StraySafe\model\try copy.py', storage_path('app/' . $inputPath), $outputPath]);
        $process->run();

        if (!$process->isSuccessful()) {
            throw new ProcessFailedException($process);
        }

        return response()->json(['message' => 'Video processed', 'video_url' => 'http://178.128.48.126/videos/output_video_detr1.mp4']);
    } catch (\Exception $e) {
        return response()->json(['error' => $e->getMessage()], 500);
    }
}
    public function processVideo1(Request $request)
{
    try {
        $request->validate([
            'file' => 'required|file|mimes:mp4|max:20480',
        ]);

        $file = $request->file('file');
        $inputPath = $file->storeAs('videos', 'input_video1.mp4');
        $outputPath = storage_path('app/videos/output_video_resized1.mp4');

        $process = new Process(['python', 'D:\Project Design - Web App\StraySafe\model\try.py', storage_path('app/' . $inputPath), $outputPath]);
        $process->run();

        if (!$process->isSuccessful()) {
            throw new ProcessFailedException($process);
        }

        return response()->json(['message' => 'Video processed', 'video_url' => 'http://178.128.48.126/videos/output_video_resized1.mp4']);
    } catch (\Exception $e) {
        return response()->json(['error' => $e->getMessage()], 500);
    }
}
public function processVideo2(Request $request)
{
    try {
        $request->validate([
            'file' => 'required|file|mimes:mp4|max:20480',
        ]);

        $file = $request->file('file');
        $inputPath = $file->storeAs('videos', 'input_video2.mp4');
        $outputPath = storage_path('app/videos/output_video_resized2.mp4');

        $process = new Process(['python', 'D:\Project Design - Web App\StraySafe\model\try.py', storage_path('app/' . $inputPath), $outputPath]);
        $process->run();

        if (!$process->isSuccessful()) {
            throw new ProcessFailedException($process);
        }

        return response()->json(['message' => 'Video processed', 'video_url' => 'http://178.128.48.126/videos/output_for_rtmdet1.mp4']);
    } catch (\Exception $e) {
        return response()->json(['error' => $e->getMessage()], 500);
    }
}
}