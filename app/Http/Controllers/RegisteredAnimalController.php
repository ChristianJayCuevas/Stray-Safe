<?php

namespace App\Http\Controllers;

use App\Models\RegisteredAnimal;
use App\Models\TemporaryImage;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;

class RegisteredAnimalController extends Controller
{
    /**
     * Display a listing of the registered animals.
     */
    public function index()
    {
        $today = now()->toDateString();
        $animals = RegisteredAnimal::all();
        $total = $animals->count();
        $todayCount = RegisteredAnimal::whereDate('created_at', $today)->count();

        return response()->json([
            'animals' => $animals,
            'total' => $total,
            'today' => $todayCount,
        ]);
    }

    /**
     * Store a newly created animal in storage.
     */
    public function store(Request $request)
    {
        $request->validate([
            'owner' => 'required|string|max:255',
            'contact' => 'required|string|max:255',
            'animal_type' => 'required|in:dog,cat',
            'image_url' => 'required|array', // Array of temporary folder IDs
            'status' => 'required|in:caught,free,claimed',
        ]);
    
        $animal = RegisteredAnimal::create($request->only(['owner', 'contact', 'animal_type', 'status']));
    
        $temporaryImages = TemporaryImage::whereIn('folder', $request->image_url)->get();
        foreach ($temporaryImages as $temporaryImage) {
            Storage::copy(
                "images/tmp/{$temporaryImage->folder}/{$temporaryImage->file}",
                "images/{$temporaryImage->folder}/{$temporaryImage->file}"
            );
    
            $animal->images()->create([
                'file_name' => $temporaryImage->file,
                'file_path' => "{$temporaryImage->folder}/{$temporaryImage->file}",
            ]);
    
            Storage::deleteDirectory("images/tmp/{$temporaryImage->folder}");
            $temporaryImage->delete();
        }
    
        return response()->json(['status' => 'created'], 201);
    }
    
    public function update(Request $request, $id)
    {
        $animal = RegisteredAnimal::findOrFail($id);
    
        $request->validate([
            'owner' => 'required|string|max:255',
            'contact' => 'required|string|max:255',
            'animal_type' => 'required|in:dog,cat',
            'image_url' => 'required|array',
            'status' => 'required|in:caught,free,claimed',
        ]);
    
        $animal->update($request->only(['owner', 'contact', 'animal_type', 'status']));
    
        $animal->images()->delete();
    
        $temporaryImages = TemporaryImage::whereIn('folder', $request->image_url)->get();
        foreach ($temporaryImages as $temporaryImage) {
            Storage::copy(
                "images/tmp/{$temporaryImage->folder}/{$temporaryImage->file}",
                "images/{$temporaryImage->folder}/{$temporaryImage->file}"
            );
    
            $animal->images()->create([
                'file_name' => $temporaryImage->file,
                'file_path' => "{$temporaryImage->folder}/{$temporaryImage->file}",
            ]);
    
            Storage::deleteDirectory("images/tmp/{$temporaryImage->folder}");
            $temporaryImage->delete();
        }
    
        return response()->json(['status' => 'updated'], 200);
    }
    

    /**
     * Remove the specified animal from storage.
     */
    public function destroy($id)
    {
        RegisteredAnimal::destroy($id);

        return response()->json(['status' => 'deleted'], 200);
    }
}
