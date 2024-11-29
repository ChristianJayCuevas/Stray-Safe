<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\JsonResponse;

class RegisteredUsersAPI extends Controller
{
    /**
     * Fetch all users.
     */
    public function fetchUsers(): JsonResponse
    {
        $users = User::select('id', 'name', 'email', 'created_at', 'updated_at')->get();

        return response()->json([
            'status' => 'success',
            'data' => $users,
        ], 200);
    }
}
