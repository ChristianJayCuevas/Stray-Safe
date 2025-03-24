<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\MapPin;
use Log;

class CameraPinController extends Controller
{
    /**
     * Create a new controller instance.
     * This controller does not use auth middleware.
     */
    public function __construct()
    {
        // No middleware - intentionally public
    }
    
    /**
     * Store a camera pin in the database - no auth required.
     */
    public function store(Request $request)
    {
        // Check for the static token
        $token = $request->header('Authorization');
        if ($token !== 'Bearer StraySafeTeam3') {
            return response()->json(['error' => 'Unauthorized - Invalid API token'], 401);
        }

        // Debugging request data
        Log::info("Public Camera Pin API Request Data:", $request->all());

        // Get camera pin data
        $coordinates = $request->input('coordinates');
        $cameraId = $request->input('camera_id');
        $cameraName = $request->input('camera_name');
        $hlsUrl = $request->input('hls_url');
        
        Log::info("Received public camera pin request: Camera ID - $cameraId, Camera Name - $cameraName, Coordinates - " . json_encode($coordinates));
        
        // Validate with more flexible requirements
        try {
            $validated = $request->validate([
                'coordinates' => 'required|array',
                'coordinates.0' => 'required|numeric',
                'coordinates.1' => 'required|numeric',
                'camera_id' => 'required|string',
                'camera_name' => 'required|string',
                'hls_url' => 'required|string',
            ]);
            
            Log::info("Validation passed:", $validated);
        } catch (\Exception $e) {
            Log::error("Validation failed: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Validation failed: ' . $e->getMessage()], 400);
        }
        
        try {
            // Store the camera pin information in the database
            $pin = MapPin::create([
                'animal_type' => 'Camera',
                'stray_status' => 'Active',
                'latitude' => $coordinates[1],
                'longitude' => $coordinates[0],
                'snapshot_path' => null,
                'is_camera' => true,
                'camera_id' => $cameraId,
                'camera_name' => $cameraName,
                'hls_url' => $hlsUrl,
            ]);
            
            return response()->json([
                'success' => true, 
                'message' => 'Camera pin added successfully',
                'pin' => $pin
            ], 200);
        } catch (\Exception $e) {
            Log::error("Failed to store camera pin: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to add camera pin: ' . $e->getMessage()], 500);
        }
    }
}
