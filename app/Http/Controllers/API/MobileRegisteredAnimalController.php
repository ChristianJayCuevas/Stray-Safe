<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\RegisteredAnimal;
use Illuminate\Support\Facades\Validator;
class MobileRegisteredAnimalController extends Controller
{
    public function fetchRegisteredAnimals()
    {
        // Retrieve all registered animals from the database
        $animals = RegisteredAnimal::select('id', 'owner', 'contact', 'animal_type', 'picture', 'status', 'created_at', 'updated_at', 'breed')->get();

        return response()->json([
            'status' => 'success',
            'data' => $animals,
        ]);
    }

    public function storeRegisteredAnimal(Request $request)
    {
        // Validate the incoming request
        $validator = Validator::make($request->all(), [
            'owner' => 'required|string|max:255',
            'contact' => 'required|string|max:255',
            'animal_type' => 'required|in:dog,cat',
            'picture' => 'required|url', // Expecting a URL from a CDN
            'status' => 'in:caught,free,claimed',
            'breed' => 'nullable|string|max:255',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'status' => 'error',
                'errors' => $validator->errors(),
            ], 422);
        }

        // Create a new registered animal record
        $animal = RegisteredAnimal::create([
            'owner' => $request->owner,
            'contact' => $request->contact,
            'animal_type' => $request->animal_type,
            'picture' => $request->picture,
            'status' => $request->status ?? 'free',
            'breed' => $request->breed,
        ]);

        return response()->json([
            'status' => 'success',
            'message' => 'Animal registered successfully.',
            'data' => $animal,
        ], 201);
    }
}
