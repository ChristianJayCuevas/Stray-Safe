<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use App\Models\User;

class UserController extends Controller
{
    public function login(Request $request)
{
    $request->validate([
        'email' => 'required|email',
        'password' => 'required',
    ]);

    $user = User::where('email', $request->email)->first();

    if (!$user || !Hash::check($request->password, $user->password)) {
        return response()->json(['message' => 'Invalid credentials'], 401);
    }

    // Issue a token
    $token = $user->createToken('API Token')->plainTextToken;

    return response()->json([
        'token' => $token,
        'user' => $user,
    ]);
}
public function fetchUsers()
{
    $users = User::select('id', 'name', 'email', 'created_at', 'updated_at')->get();

    return response()->json([
        'status' => 'success',
        'data' => $users,
    ]);
}
}
