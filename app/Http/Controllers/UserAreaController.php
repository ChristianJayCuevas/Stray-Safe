<?php

namespace App\Http\Controllers;

use App\Models\UserArea;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Validator;

class UserAreaController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index(Request $request)
    {
        $query = UserArea::where('user_id', Auth::id());
        
        // Filter by user_map_id if provided
        if ($request->has('user_map_id')) {
            $query->where('user_map_id', $request->user_map_id);
        }
        
        $areas = $query->get();
        return response()->json($areas);
    }

    /**
     * Show the form for creating a new resource.
     */
    public function create()
    {
        //
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'feature_id' => 'required|string|unique:user_areas',
            'name' => 'nullable|string|max:255',
            'description' => 'nullable|string',
            'geometry' => 'required|json',
            'properties' => 'nullable|json',
            'user_map_id' => 'nullable|exists:user_maps,id',
        ]);

        if ($validator->fails()) {
            return response()->json(['errors' => $validator->errors()], 422);
        }

        $area = new UserArea();
        $area->user_id = Auth::id();
        $area->user_map_id = $request->user_map_id;
        $area->feature_id = $request->feature_id;
        $area->name = $request->name;
        $area->description = $request->description;
        $area->geometry = $request->geometry;
        $area->properties = $request->properties;
        $area->save();

        return response()->json($area, 201);
    }

    /**
     * Display the specified resource.
     */
    public function show(string $id)
    {
        $area = UserArea::where('user_id', Auth::id())
            ->where('feature_id', $id)
            ->first();
            
        if (!$area) {
            return response()->json(['error' => 'Area not found'], 404);
        }
        
        return response()->json($area);
    }

    /**
     * Show the form for editing the specified resource.
     */
    public function edit(string $id)
    {
        //
    }

    /**
     * Update the specified resource in storage.
     */
    public function update(Request $request, string $id)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'nullable|string|max:255',
            'description' => 'nullable|string',
            'geometry' => 'required|json',
            'properties' => 'nullable|json',
        ]);

        if ($validator->fails()) {
            return response()->json(['errors' => $validator->errors()], 422);
        }

        $area = UserArea::where('user_id', Auth::id())
            ->where('feature_id', $id)
            ->first();
            
        if (!$area) {
            return response()->json(['error' => 'Area not found'], 404);
        }
        
        $area->name = $request->name ?? $area->name;
        $area->description = $request->description ?? $area->description;
        $area->geometry = $request->geometry;
        $area->properties = $request->properties;
        $area->save();
        
        return response()->json($area);
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(string $id)
    {
        $area = UserArea::where('user_id', Auth::id())
            ->where('feature_id', $id)
            ->first();
            
        if (!$area) {
            return response()->json(['error' => 'Area not found'], 404);
        }
        
        $area->delete();
        
        return response()->json(['message' => 'Area deleted successfully']);
    }
}
