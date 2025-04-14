<?php

namespace App\Http\Controllers;

use App\Models\MapPin;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class PinController extends Controller
{
    public function index(Request $request)
    {
        try {
            $query = MapPin::query();
            
            // Filter by user_map_id if provided
            if ($request->has('user_map_id')) {
                $query->where('user_map_id', $request->user_map_id);
            }
            
            // Add other filters as needed
            if ($request->has('animal_type') && $request->animal_type !== 'all') {
                $query->where('animal_type', $request->animal_type);
            }
            
            // Get all pins
            $pins = $query->get();
            
            return response()->json(['data' => $pins]);
        } catch (\Exception $e) {
            Log::error('Error fetching pins: ' . $e->getMessage());
            return response()->json(['error' => 'Failed to fetch pins'], 500);
        }
    }

    public function store(Request $request)
    {
        try {
            // Validate the request
            $validatedData = $request->validate([
                'lat' => 'required|numeric',
                'lng' => 'required|numeric',
                'animal_type' => 'required|string',
                'description' => 'nullable|string',
                'image_url' => 'nullable|string',
                'user_map_id' => 'nullable|exists:user_maps,id',
            ]);
            
            // Create a new pin
            $pin = MapPin::create([
                'coordinates' => [$validatedData['lng'], $validatedData['lat']],
                'animal_type' => $validatedData['animal_type'],
                'description' => $validatedData['description'] ?? null,
                'image_url' => $validatedData['image_url'] ?? null,
                'user_map_id' => $validatedData['user_map_id'] ?? null,
            ]);
            
            return response()->json([
                'success' => true,
                'message' => 'Pin created successfully',
                'pin' => $pin
            ]);
        } catch (\Exception $e) {
            Log::error('Error creating pin: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Failed to create pin: ' . $e->getMessage()
            ], 500);
        }
    }
} 