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
     * Get all pins from the database with randomized coordinates.
     */
    public function index()
    {
        try {
            $pins = MapPin::all();

            // Return the original coordinates without randomization
            $response = $pins->map(function ($pin) {
                $pinData = [
                    'id' => $pin->id,
                    'animal_type' => $pin->animal_type,
                    'stray_status' => $pin->stray_status,
                    'coordinates' => [$pin->longitude, $pin->latitude], // Original coordinates
                ];

                // Add camera-specific properties if this is a camera
                if ($pin->is_camera || strtolower($pin->animal_type) === 'camera') {
                    $pinData['isCamera'] = true;
                    $pinData['camera_id'] = $pin->camera_id;
                    $pinData['cameraName'] = $pin->camera_name;
                    $pinData['hls_url'] = $pin->hls_url;
                    $pinData['viewingDirection'] = $pin->viewing_direction;
                    $pinData['viewingAngle'] = $pin->viewing_angle;
                    $pinData['conicalView'] = (bool)$pin->conical_view;
                    $pinData['perceptionRange'] = $pin->perception_range;
                }

                return $pinData;
            });

            return response()->json($response, 200);
        } catch (\Exception $e) {
            Log::error("Failed to fetch pins: " . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to fetch pins'], 500);
        }
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
            $pin = MapPin::findOrFail($id);
            $pin->delete();
            
            return response()->json([
                'success' => true, 
                'message' => 'Pin deleted successfully'
            ], 200);
        } catch (\Exception $e) {
            Log::error("Failed to delete pin: " . $e->getMessage());
            return response()->json([
                'success' => false, 
                'message' => 'Failed to delete pin: ' . $e->getMessage()
            ], 500);
        }
    }
}
