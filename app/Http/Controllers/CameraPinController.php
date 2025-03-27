<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use App\Models\MapPin;

class CameraPinController extends Controller
{
    /**
     * Store a newly created camera pin in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\Response
     */
    public function store(Request $request)
    {
        Log::info('Camera pin creation request received via web route', $request->all());
        
        try {
            // Validate the request
            $validated = $request->validate([
                'coordinates' => 'required|array|size:2',
                'coordinates.0' => 'required|numeric', // longitude
                'coordinates.1' => 'required|numeric', // latitude
                'camera_id' => 'required|string',
                'camera_name' => 'required|string',
                'hls_url' => 'required|string',
            ]);
            
            Log::info('Camera pin validation successful', $validated);
            
            // Store the camera pin information in the database
            $pin = MapPin::create([
                'animal_type' => 'Camera',
                'stray_status' => 'Active',
                'latitude' => $request->coordinates[1],
                'longitude' => $request->coordinates[0],
                'snapshot_path' => null,
                'is_camera' => true,
                'camera_id' => $request->camera_id,
                'camera_name' => $request->camera_name,
                'hls_url' => $request->hls_url,
            ]);
            
            Log::info('Camera pin stored successfully', ['pin' => $pin]);
            
            return response()->json([
                'success' => true,
                'message' => 'Camera pin created successfully',
                'pin' => $pin
            ], 201);
            
        } catch (\Illuminate\Validation\ValidationException $e) {
            Log::error('Camera pin validation failed', ['errors' => $e->errors()]);
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $e->errors()
            ], 422);
        } catch (\Exception $e) {
            Log::error('Failed to save camera pin', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to save camera pin: ' . $e->getMessage()
            ], 500);
        }
    }
}
