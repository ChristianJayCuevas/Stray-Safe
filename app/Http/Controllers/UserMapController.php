<?php

namespace App\Http\Controllers;

use App\Models\UserMap;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class UserMapController extends Controller
{
    /**
     * Display a listing of the user's maps.
     */
    public function index()
    {
        $user = Auth::user();
        $ownedMaps = $user->ownedMaps;
        $accessibleMaps = $user->accessibleMaps;
        
        return response()->json([
            'owned_maps' => $ownedMaps,
            'accessible_maps' => $accessibleMaps
        ]);
    }

    /**
     * Store a newly created map.
     */
    public function store(Request $request)
    {
        $user = Auth::user();
        
        // Check if user already has a personal map
        if ($user->hasPersonalMap() && !$user->isAdmin()) {
            return response()->json([
                'success' => false,
                'message' => 'You already have a personal map. Please use the existing one or delete it before creating a new one.'
            ], 422);
        }
        
        // Validate request
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'is_public' => 'boolean',
            'default_view' => 'nullable|array',
        ]);
        
        try {
            // Generate a unique access code
            $accessCode = UserMap::generateAccessCode();
            
            // Create the map
            $map = new UserMap([
                'owner_id' => $user->id,
                'name' => $validated['name'],
                'description' => $validated['description'] ?? null,
                'access_code' => $accessCode,
                'is_public' => $validated['is_public'] ?? false,
                'default_view' => $validated['default_view'] ?? [
                    'center' => [120.9842, 14.5995], // Manila, Philippines coordinates
                    'zoom' => 12 // Closer zoom level for city view
                ],
            ]);
            
            $map->save();
            
            return response()->json([
                'success' => true,
                'message' => 'Map created successfully',
                'map' => $map
            ]);
            
        } catch (\Exception $e) {
            Log::error('Error creating map: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Failed to create map. Please try again.'
            ], 500);
        }
    }

    /**
     * Display the specified map if user has access.
     */
    public function show(string $id)
    {
        $user = Auth::user();
        $map = UserMap::findOrFail($id);
        
        // Check if user has access
        if (!$map->userHasAccess($user)) {
            return response()->json([
                'success' => false,
                'message' => 'You do not have access to this map.'
            ], 403);
        }
        
        // Get map with pins and areas
        $map->load(['pins', 'areas']);
        $role = $map->getUserRole($user);
        
        return response()->json([
            'success' => true,
            'map' => $map,
            'role' => $role
        ]);
    }

    /**
     * Access a map by its access code.
     */
    public function accessByCode(Request $request)
    {
        $request->validate([
            'access_code' => 'required|string|size:6'
        ]);
        
        $accessCode = strtoupper($request->access_code);
        $user = Auth::user();
        
        // Find the map by access code
        $map = UserMap::where('access_code', $accessCode)->first();
        
        if (!$map) {
            return response()->json([
                'success' => false,
                'message' => 'Invalid access code. Please check and try again.'
            ], 404);
        }
        
        // If user is not the owner and doesn't already have access, add them
        if ($map->owner_id !== $user->id && !$map->userHasAccess($user)) {
            // Add user as a viewer
            $map->viewers()->attach($user->id, ['role' => 'viewer']);
        }
        
        // Get map with pins
        $map->load('pins');
        $role = $map->getUserRole($user);
        
        return response()->json([
            'success' => true,
            'message' => 'Map accessed successfully',
            'map' => $map,
            'role' => $role
        ]);
    }

    /**
     * Update the specified map if user is owner.
     */
    public function update(Request $request, string $id)
    {
        $user = Auth::user();
        $map = UserMap::findOrFail($id);
        
        // Check if user is owner
        if ($map->owner_id !== $user->id && !$user->isAdmin()) {
            return response()->json([
                'success' => false,
                'message' => 'Only the map owner can update it.'
            ], 403);
        }
        
        // Validate request
        $validated = $request->validate([
            'name' => 'sometimes|required|string|max:255',
            'description' => 'nullable|string',
            'is_public' => 'sometimes|boolean',
            'default_view' => 'sometimes|array',
        ]);
        
        try {
            // Update the map
            $map->update($validated);
            
            return response()->json([
                'success' => true,
                'message' => 'Map updated successfully',
                'map' => $map
            ]);
            
        } catch (\Exception $e) {
            Log::error('Error updating map: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Failed to update map. Please try again.'
            ], 500);
        }
    }

    /**
     * Remove the specified map if user is owner.
     */
    public function destroy(string $id)
    {
        $user = Auth::user();
        $map = UserMap::findOrFail($id);
        
        // Check if user is owner
        if ($map->owner_id !== $user->id && !$user->isAdmin()) {
            return response()->json([
                'success' => false,
                'message' => 'Only the map owner can delete it.'
            ], 403);
        }
        
        try {
            // Delete the map
            $map->delete();
            
            return response()->json([
                'success' => true,
                'message' => 'Map deleted successfully'
            ]);
            
        } catch (\Exception $e) {
            Log::error('Error deleting map: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Failed to delete map. Please try again.'
            ], 500);
        }
    }
    
    /**
     * Generate a new access code for the map.
     */
    public function regenerateAccessCode(string $id)
    {
        $user = Auth::user();
        $map = UserMap::findOrFail($id);
        
        // Check if user is owner
        if ($map->owner_id !== $user->id && !$user->isAdmin()) {
            return response()->json([
                'success' => false,
                'message' => 'Only the map owner can regenerate the access code.'
            ], 403);
        }
        
        try {
            // Generate a new access code
            $accessCode = UserMap::generateAccessCode();
            $map->access_code = $accessCode;
            $map->save();
            
            return response()->json([
                'success' => true,
                'message' => 'Access code regenerated successfully',
                'access_code' => $accessCode
            ]);
            
        } catch (\Exception $e) {
            Log::error('Error regenerating access code: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Failed to regenerate access code. Please try again.'
            ], 500);
        }
    }

    /**
     * Display a listing of all maps (admin only).
     */
    public function adminIndex()
    {
        $user = Auth::user();
        
        // Check if user is admin
        if (!$user->isAdmin()) {
            return response()->json([
                'success' => false,
                'message' => 'Unauthorized. Admin access required.'
            ], 403);
        }
        
        try {
            // Get all maps with owner information
            $maps = UserMap::with(['owner', 'viewers'])->get();
            
            return response()->json([
                'success' => true,
                'maps' => $maps
            ]);
        } catch (\Exception $e) {
            Log::error('Error fetching admin maps: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Failed to fetch maps. Please try again.'
            ], 500);
        }
    }
}
