<?php

namespace App\Http\Controllers;

use Illuminate\Support\Facades\Log;
use App\Models\Comment;
use App\Http\Resources\PostResource;
use App\Models\Post;
use Illuminate\Http\Request;
use Illuminate\Http\RedirectResponse;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Storage;
use Inertia\Inertia;
use App\Models\PostImage;
use App\Models\TemporaryImage;
use App\Models\User;
class PostController extends Controller
{
    public function index()
    {
        $authUserId = auth()->id();
    
        // Build the query for posts with necessary relationships and additional properties
        $paginatedPosts = Post::with(['user', 'postImages'])
            ->latest()
            ->withCount('likes')
            ->withCount(['likes as liked' => function ($query) use ($authUserId) {
                $query->where('user_id', $authUserId);
            }])
            ->withCasts(['liked' => 'boolean'])
            ->paginate(5);
    
        // Get comments grouped by post ID
        $comments = Comment::with('user')->get()->groupBy('post_id');
    
        // Return data to Inertia
        return Inertia::render('Home', [
            'posts' => PostResource::collection($paginatedPosts),
            'comments' => $comments,
        ]);
    }

    //For deleting a post
    public function deletePost($id)
    {
        Log::info('Delete post request received for post ID: ' . $id);

        $post = Post::findOrFail($id);
        $postImages = PostImage::where('post_id', $id)->get();
        $directoriesToDelete = [];

        foreach ($postImages as $postImage) {
            $imagePath = $postImage->post_image_path;
            
            if (Storage::exists('images/' . $imagePath)) {
                Storage::delete('images/' . $imagePath);
                
        
                $directory = dirname($imagePath);
                if (!in_array($directory, $directoriesToDelete)) {
                    $directoriesToDelete[] = $directory;
                }
            }
        }

        PostImage::where('post_id', $id)->delete();
        $post->delete();
        foreach ($directoriesToDelete as $directory) {
            if (Storage::exists('images/' . $directory) && Storage::allFiles('images/' . $directory) == []) {
                Storage::deleteDirectory('images/' . $directory);
            }
        }

        Log::info('Post deleted: ' . $id);

        return Inertia::render(route('home'));
    }

    //For creating a post
    public function uploadPost(Request $request)
    {   
        $userID = Auth::user();
        $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'description' => ['required'],
            'images.*' => ['image', 'mimes:jpeg,png,jpg,gif', 'max:2048'], // Validation for multiple images
        ]);

        // Create the post
        $post = Post::create([
            'title' => $request->title,
            'description' => $request->description,
            'user_id' => $userID->id
        ]);

        // Handle multiple image uploads
        $temporaryImages = TemporaryImage::whereIn('folder', $request->image_url)->get();
        foreach($temporaryImages as $temporaryImage) {
            Storage::copy('images/tmp/' . $temporaryImage->folder . '/' . $temporaryImage->file, 'images/' . $temporaryImage->folder . '/' . $temporaryImage->file);
            PostImage::create(
                [
                    'post_id' => $post->id,
                    'post_image_caption' => $temporaryImage->file,
                    'post_image_path' => $temporaryImage->folder . '/' . $temporaryImage->file
                ]
                );
                Storage::deleteDirectory('images/tmp/' . $temporaryImage->folder);
                $temporaryImage->delete();
            }
        return to_route('home');
    }

    public function sharePost(Request $request)
    {   
        $userID = Auth::user();
    
        // Validate request data
        $request->validate([
            'title' => ['required', 'string', 'max:255'],
            'description' => ['required'],
        ]);
    
        $imageUrl = $request->image_url;
    
        // Extract filename from the URL
        $filename = basename(parse_url($imageUrl, PHP_URL_PATH));
    
        // Create a new post
        $post = Post::create([
            'title' => $request->title,
            'description' => $request->description,
            'user_id' => $userID->id,
        ]);
    
        // Create a new PostImage record
        PostImage::create([
            'post_id' => $post->id,
            'post_image_caption' => $filename, // Store the filename for caption
            'post_image_path' => $filename, // Store the filename for path
        ]);
    
        return to_route('home');
    }


    //Show Edit Post Page
    public function updatePost(Request $request, $id)
    {
        $post = Post::findOrFail($id);

        $data = $request->only(['title', 'description']);

        // Preserve existing image URL if no new image is uploaded
        if ($request->hasFile('image_url')) {
            $file = $request->file('image_url');
            $path = $file->store('images', 'public');
            $data['image_url'] = $path;
        } else {
            $data['image_url'] = $post->image_url;
        }

        $post->update($data);

        return to_route('home');
    }

}
