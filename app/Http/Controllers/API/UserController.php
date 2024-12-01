<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use App\Models\User;
use Illuminate\Support\Facades\Auth;
use Laravel\Sanctum\HasApiTokens;
use Illuminate\Support\Facades\Validator;

class UserController extends Controller
{
    public function login(Request $request)
    {
        $request->validate([
            'email' => 'required|email',
            'password' => 'required',
        ]);

        // Attempt to authenticate the user
        if (!Auth::attempt($request->only('email', 'password'))) {
            return response()->json(['error' => 'Invalid login credentials'], 401);
        }

        // Get the authenticated user
        $user = Auth::user();

        // Generate a Sanctum token
        $token = $user->createToken('mobile')->plainTextToken;

        return response()->json([
            'status' => 'success',
            'user' => $user,
            'token' => $token,
        ]);
    }

    public function register(Request $request)
    {
        // Validate the incoming request data
        $validator = Validator::make($request->all(), [
            'username' => 'required|string|max:255',
            'email' => 'required|string|email|max:255|unique:users',
            'password' => 'required|string|min:8|confirmed', // Ensure passwords match
            'contact_number' => 'nullable|string|max:15',
            'profile_image_link' => 'nullable|url', // Optional profile image link
        ]);

        if ($validator->fails()) {
            return response()->json([
                'status' => 'error',
                'message' => $validator->errors(),
            ], 422);
        }

        // Create the user
        $user = User::create([
            'name' => $request->username,
            'email' => $request->email,
            'password' => Hash::make($request->password),
            'contact_number' => $request->contact_number,
            'profile_image_link' => $request->profile_image_link,
        ]);

        // Generate a Sanctum token
        $token = $user->createToken('mobile')->plainTextToken;

        return response()->json([
            'status' => 'success',
            'message' => 'User created successfully',
            'user' => $user,
            'token' => $token,
        ], 201);
    }

    public function fetchUsers()
    {
        $users = User::select('id', 'name', 'email', 'created_at', 'updated_at', 'contact_number', 'profile_image_link')->get();

        return response()->json([
            'status' => 'success',
            'data' => $users,
        ]);
    }

    public function fetchLoggedInUser()
    {
        $user = Auth::user();

        if ($user) {
            return response()->json([
                'status' => 'success',
                'data' => $user,
            ]);
        } else {
            return response()->json([
                'status' => 'error',
                'message' => 'User not authenticated',
            ], 401);
        }
    }

    public function updateProfileImage(Request $request)
{
    // Validate the request
    $validator = Validator::make($request->all(), [
        'profile_image_link' => 'required|url',
        'email' => 'required|email', // Ensure email is included in the request
    ]);

    if ($validator->fails()) {
        return response()->json([
            'status' => 'error',
            'message' => $validator->errors(),
        ], 422);
    }

    // Find the user by email
    $user = User::where('email', $request->email)->first();

    if (!$user) {
        return response()->json([
            'status' => 'error',
            'message' => 'User not found',
        ], 404);
    }

    // Update the profile image link
    $user->profile_image_link = $request->profile_image_link;
    $user->save();

    return response()->json([
        'status' => 'success',
        'message' => 'Profile image updated successfully',
        'data' => $user,
    ]);
}

}
