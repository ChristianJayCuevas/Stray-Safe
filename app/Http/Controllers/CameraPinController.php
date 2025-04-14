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
            // Validate the request with additional cone data fields
            $validated = $request->validate([
                'coordinates' => 'required|array|size:2',
                'coordinates.0' => 'required|numeric',
                'coordinates.1' => 'required|numeric',
                'camera_id' => 'nullable|string',
                'camera_name' => 'nullable|string',
                'hls_url' => 'nullable|string',
                'conical_view' => 'nullable|boolean',
                'viewing_direction' => 'nullable|numeric',
                'viewing_angle' => 'nullable|numeric',
                'perception_range' => 'nullable|numeric',
                'cone_coordinates' => 'nullable|json',
                'cone_center' => 'nullable|json',
                'cone_radius' => 'nullable|numeric',
                'cone_direction' => 'nullable|numeric',
                'cone_angle' => 'nullable|numeric',
                'user_map_id' => 'nullable|exists:user_maps,id',
            ]);
            
            Log::info('Camera pin validation successful', $validated);
            
            // Use cone data from frontend if available, otherwise calculate it
            $conePoints = null;
            $coneCenter = null;
            $perceptionRange = $request->perception_range ?? 30;
            $viewingDirection = $request->viewing_direction ?? 0;
            $viewingAngle = $request->viewing_angle ?? 60;
            
            if ($request->filled('cone_coordinates') && $request->filled('cone_center')) {
                Log::info('Using cone data from frontend');
                $conePoints = json_decode($request->cone_coordinates, true);
                $coneCenter = json_decode($request->cone_center, true);
            } else {
                Log::info('Calculating cone data in backend');
                // Convert perception range from meters to approximate degrees
                $radiusInDegrees = $perceptionRange * 0.000009;
                
                // Calculate cone center based on camera position and direction
                $directionRad = ($viewingDirection * M_PI) / 180;
                $centerLng = $request->coordinates[0] + ($radiusInDegrees * sin($directionRad));
                $centerLat = $request->coordinates[1] + ($radiusInDegrees * cos($directionRad));
                $coneCenter = [$centerLng, $centerLat];
                
                // Generate cone points
                $conePoints = [[$request->coordinates[0], $request->coordinates[1]]];
                $numPoints = 30;
                $halfAngleRad = ($viewingAngle / 2 * M_PI) / 180;
                $startAngle = $directionRad - $halfAngleRad;
                $endAngle = $directionRad + $halfAngleRad;
                
                for ($i = 0; $i <= $numPoints; $i++) {
                    $currentAngle = $startAngle + ($i / $numPoints) * ($endAngle - $startAngle);
                    $x = $request->coordinates[0] + $radiusInDegrees * sin($currentAngle);
                    $y = $request->coordinates[1] + $radiusInDegrees * cos($currentAngle);
                    $conePoints[] = [$x, $y];
                }
                
                // Close the polygon
                $conePoints[] = [$request->coordinates[0], $request->coordinates[1]];
            }
            
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
                'conical_view' => $request->boolean('conical_view'),
                'viewing_direction' => $viewingDirection,
                'viewing_angle' => $viewingAngle,
                'perception_range' => $perceptionRange,
                'original_id' => $request->original_id ?? $request->camera_id,
                'location' => $request->location ?? 'Unknown Location',
                'rtmp_key' => $request->rtmp_key ?? $request->camera_id,
                'user_map_id' => $request->user_map_id,
                
                // Add cone data
                'cone_coordinates' => json_encode($conePoints),
                'cone_center' => json_encode($coneCenter),
                'cone_radius' => $request->cone_radius ?? $perceptionRange,
                'cone_direction' => $request->cone_direction ?? $viewingDirection,
                'cone_angle' => $request->cone_angle ?? $viewingAngle
            ]);
            
            Log::info('Camera pin stored successfully with cone data', [
                'pin' => $pin,
                'cone_data' => [
                    'coordinates' => $conePoints,
                    'center' => $coneCenter,
                    'radius' => $request->cone_radius ?? $perceptionRange,
                    'direction' => $request->cone_direction ?? $viewingDirection,
                    'angle' => $request->cone_angle ?? $viewingAngle
                ]
            ]);
            
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

    /**
     * Remove the specified camera pin from storage.
     *
     * @param  int  $id
     * @return \Illuminate\Http\Response
     */
    public function destroy($id)
    {
        try {
            Log::info('Camera pin deletion request received', ['id' => $id]);
            
            // Find the pin by ID, ensuring it's a camera pin
            $pin = \App\Models\MapPin::where('id', $id)
                ->where('is_camera', true)
                ->first();
                
            if (!$pin) {
                Log::warning('Camera pin not found or not a camera', ['id' => $id]);
                return response()->json([
                    'success' => false,
                    'message' => 'Camera pin not found'
                ], 404);
            }
            
            // Delete the pin
            $pin->delete();
            
            Log::info('Camera pin deleted successfully', ['id' => $id]);
            return response()->json([
                'success' => true,
                'message' => 'Camera pin deleted successfully'
            ]);
            
        } catch (\Exception $e) {
            Log::error('Failed to delete camera pin', [
                'id' => $id,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return response()->json([
                'success' => false,
                'message' => 'Failed to delete camera pin: ' . $e->getMessage()
            ], 500);
        }
    }
}
