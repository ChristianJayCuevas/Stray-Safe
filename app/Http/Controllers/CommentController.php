<?php

namespace App\Http\Controllers;

use App\Models\Comment;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class CommentController extends Controller
{
    public function createComment(Request $request)
    {
        $userID = Auth::user();
        Comment::create([
            'comments' => $request->comment,
            'post_id' => $request->post_id,
            'user_id' => $userID->id
        ]
        );
        return redirect()->route('dashboard', ['post' => $request->post_id]);
    }
}
