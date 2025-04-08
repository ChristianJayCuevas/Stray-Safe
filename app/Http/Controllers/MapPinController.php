<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\MapPin;
use Log;
use App\Http\Resources\MapPinResource;
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
     * Get all pins from the database with randomized coordinates.
     */
    public function index()
    {
        $pins = MapPin::all();
        return MapPinResource::collection($pins);
    }

    /**
     * Get recent sightings with randomized locations.
     */
    public function recentSightings()
    {
        try {
            $sightings = MapPin::orderBy('created_at', 'desc')
                ->take(10)
                ->get(['created_at', 'animal_type', 'stray_status', 'latitude', 'longitude', 'snapshot_path']);

            $sightings->transform(function ($sighting) {
                [$randomLatitude, $randomLongitude] = $this->randomizeCoordinates($sighting->latitude, $sighting->longitude);

                return [
                    'timestamp' => $sighting->created_at->format('Y-m-d H:i:s'),
                    'animal_type' => ucfirst($sighting->animal_type),
                    'stray_status' => ucfirst($sighting->stray_status),
                    'location' => "{$randomLatitude}, {$randomLongitude}",
                    'snapshot' => url('storage/' . $sighting->snapshot_path),
                ];
            });

            return response()->json($sightings, 200);
        } catch (\Exception $e) {
            Log::error("Failed to fetch recent sightings: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to fetch recent sightings'], 500);
        }
    }

    /**
     * Get snapshots with randomized locations.
     */
    public function getSnapshots(Request $request)
    {
        $cctvName = $request->input('cctvName');

        try {
            $snapshots = MapPin::where('animal_type', 'like', '%' . $cctvName . '%')
                ->orderBy('created_at', 'desc')
                ->take(10)
                ->get(['created_at', 'stray_status', 'snapshot_path', 'latitude', 'longitude']);

            $snapshots->transform(function ($snapshot) {
                [$randomLatitude, $randomLongitude] = $this->randomizeCoordinates($snapshot->latitude, $snapshot->longitude);

                return [
                    'timestamp' => $snapshot->created_at->format('Y-m-d H:i:s'),
                    'stray_status' => ucfirst($snapshot->stray_status),
                    'image_url' => url('storage/' . $snapshot->snapshot_path),
                    'location' => "{$randomLatitude}, {$randomLongitude}",
                ];
            });

            return response()->json(['snapshots' => $snapshots], 200);
        } catch (\Exception $e) {
            Log::error("Failed to fetch snapshots: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to fetch snapshots'], 500);
        }
    }

    /**
     * Get recent snapshots with randomized locations.
     */
    public function getRecentSnapshots()
    {
        try {
            $snapshots = MapPin::orderBy('created_at', 'desc')
                ->take(10)
                ->get(['created_at', 'stray_status', 'snapshot_path', 'latitude', 'longitude']);

            $snapshots->transform(function ($snapshot) {
                [$randomLatitude, $randomLongitude] = $this->randomizeCoordinates($snapshot->latitude, $snapshot->longitude);

                return [
                    'timestamp' => $snapshot->created_at->format('Y-m-d H:i:s'),
                    'stray_status' => ucfirst($snapshot->stray_status),
                    'image_url' => url('storage/' . $snapshot->snapshot_path),
                    'location' => "{$randomLatitude}, {$randomLongitude}",
                ];
            });

            return response()->json(['snapshots' => $snapshots], 200);
        } catch (\Exception $e) {
            Log::error("Failed to fetch recent snapshots: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to fetch recent snapshots'], 500);
        }
    }

    /**
     * Generate randomized coordinates.
     */
    private function randomizeCoordinates($latitude, $longitude, $radius = 0.0005)
    {
        // Randomly adjust latitude and longitude within the given radius
        $latOffset = (rand(-1000, 1000) / 1000) * $radius;
        $lngOffset = (rand(-1000, 1000) / 1000) * $radius;

        return [
            $latitude + $latOffset,
            $longitude + $lngOffset,
        ];
    }

    /**
     * Delete a pin from the database.
     */
    public function destroy($id)
    {
        try {
            Log::info('Pin deletion request received', ['id' => $id]);
            
            $pin = MapPin::find($id);
            
            if (!$pin) {
                Log::warning('Pin not found for deletion', ['id' => $id]);
                return response()->json([
                    'success' => false, 
                    'message' => 'Pin not found'
                ], 404);
            }
            
            // If the pin is a camera pin, check if we should use the camera pin controller
            if ($pin->is_camera) {
                Log::info('Pin is a camera pin, redirecting to camera pin controller', ['id' => $id]);
                return app(CameraPinController::class)->destroy($id);
            }
            
            // Delete the pin
            $pin->delete();
            
            Log::info('Pin deleted successfully', ['id' => $id]);
            return response()->json([
                'success' => true, 
                'message' => 'Pin deleted successfully'
            ], 200);
        } catch (\Exception $e) {
            Log::error('Failed to delete pin', [
                'id' => $id,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return response()->json([
                'success' => false, 
                'message' => 'Failed to delete pin: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get statistics about pins and cameras.
     */
    public function getStats()
    {
        try {
            $stats = [
                'totalSightings' => MapPin::where('is_camera', false)->count(),
                'dogSightings' => MapPin::where('animal_type', 'dog')->where('is_camera', false)->count(),
                'catSightings' => MapPin::where('animal_type', 'cat')->where('is_camera', false)->count(),
                'activeCCTVs' => MapPin::where('is_camera', true)->where('stray_status', 'Active')->count()
            ];

            return response()->json($stats, 200);
        } catch (\Exception $e) {
            Log::error("Failed to fetch statistics: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to fetch statistics'], 500);
        }
    }
}
