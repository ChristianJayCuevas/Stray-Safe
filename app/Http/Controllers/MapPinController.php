<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\MapPin;
use Log;

class MapPinController extends Controller
{
    /**
     * Store a new pin in the database.
     */
    public function store(Request $request)
    {
        $animalType = $request->input('animal_type');
        $coordinates = $request->input('coordinates');
        $snapshot = $request->input('snapshot');
        $strayStatus = $request->input('stray_status');
    
        Log::info("Received pin request: Animal Type - $animalType, Stray Status - $strayStatus, Coordinates - " . implode(', ', $coordinates));
    
        $request->validate([
            'animal_type' => 'required|string',
            'stray_status' => 'required|string',
            'coordinates' => 'required|array',
            'coordinates.0' => 'required|numeric',
            'coordinates.1' => 'required|numeric',
            'snapshot' => 'required|string',
        ]);
    
        try {
            // Decode the Base64 image
            $imageData = base64_decode($snapshot);
            if ($imageData === false) {
                return response()->json(['success' => false, 'message' => 'Invalid Base64 image data'], 400);
            }
    
            // Save the image directly to the public/snapshots directory
            $imagePath = 'snapshots/' . uniqid('snapshot_', true) . '.jpg';
            file_put_contents(public_path($imagePath), $imageData);
    
            // Store the pin information in the database
            MapPin::create([
                'animal_type' => $animalType,
                'stray_status' => $strayStatus,
                'latitude' => $coordinates[1],
                'longitude' => $coordinates[0],
                'snapshot_path' => $imagePath,
            ]);
    
            return response()->json(['success' => true, 'message' => 'Pin added successfully'], 200);
        } catch (\Exception $e) {
            Log::error("Failed to store pin: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to add pin'], 500);
        }
    }
    
    /**
     * Get all pins from the database.
     */
    public function index()
    {
        try {
            $pins = MapPin::all();

            // Format the response data
            $response = $pins->map(function ($pin) {
                return [
                    'animal_type' => $pin->animal_type,
                    'stray_status' => $pin->stray_status, // Include stray status
                    'coordinates' => [$pin->longitude, $pin->latitude],
                ];
            });

            return response()->json($response, 200);
        } catch (\Exception $e) {
            Log::error("Failed to fetch pins: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to fetch pins'], 500);
        }
    }

    /**
     * Get recent sightings from the database.
     */
    public function recentSightings()
    {
        $sightings = MapPin::orderBy('created_at', 'desc')
            ->take(10)
            ->get(['created_at', 'animal_type', 'stray_status', 'latitude', 'longitude', 'snapshot_path']);

        $sightings->transform(function ($sighting) {
            return [
                'timestamp' => $sighting->created_at->format('Y-m-d H:i:s'),
                'animal_type' => ucfirst($sighting->animal_type),
                'stray_status' => ucfirst($sighting->stray_status),
                'location' => "{$sighting->latitude}, {$sighting->longitude}",
                'snapshot' => url('storage/' . $sighting->snapshot_path),
            ];
        });

        return response()->json($sightings);
    }
    public function getSnapshots(Request $request)
{
    $cctvName = $request->input('cctvName');

    try {
        $snapshots = MapPin::where('animal_type', 'like', '%' . $cctvName . '%')
            ->orderBy('created_at', 'desc')
            ->take(10)
            ->get(['created_at', 'stray_status', 'snapshot_path']);

        $snapshots->transform(function ($snapshot) {
            return [
                'timestamp' => $snapshot->created_at->format('Y-m-d H:i:s'),
                'stray_status' => ucfirst($snapshot->stray_status),
                'image_url' => url('storage/' . $snapshot->snapshot_path),
            ];
        });

        return response()->json(['snapshots' => $snapshots], 200);
    } catch (\Exception $e) {
        Log::error("Failed to fetch snapshots: " . $e->getMessage());
        return response()->json(['success' => false, 'message' => 'Failed to fetch snapshots'], 500);
    }
}
public function getRecentSnapshots()
{
    try {
        $snapshots = MapPin::orderBy('created_at', 'desc')
            ->take(10)
            ->get(['created_at', 'stray_status', 'snapshot_path', 'latitude', 'longitude']);

        $snapshots->transform(function ($snapshot) {
            return [
                'timestamp' => $snapshot->created_at->format('Y-m-d H:i:s'),
                'stray_status' => ucfirst($snapshot->stray_status),
                'image_url' => url($snapshot->snapshot_path), // Use the direct URL from the public directory
                'location' => "{$snapshot->latitude}, {$snapshot->longitude}",
            ];
        });

        return response()->json(['snapshots' => $snapshots], 200);
    } catch (\Exception $e) {
        Log::error("Failed to fetch recent snapshots: " . $e->getMessage());
        return response()->json(['success' => false, 'message' => 'Failed to fetch snapshots'], 500);
    }
}



}
