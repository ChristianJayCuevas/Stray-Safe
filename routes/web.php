<?php
use App\Http\Controllers\{
    ProfileController,
    PostController,
    UploadTemporaryImageController,
    DeleteTemporaryImageController,
    CommentController,
    CCTVController,
};
use Illuminate\Foundation\Application;
use Illuminate\Support\Facades\Route;
use Illuminate\Http\Request;
use Inertia\Inertia;
use App\Http\Controllers\VideoProcessingController;

use App\Http\Controllers\MapPinController;


Route::get('/', function () {
    return Inertia::render('Welcome', [
        'canLogin' => Route::has('login'),
        'canRegister' => Route::has('register'),
        'laravelVersion' => Application::VERSION,
        'phpVersion' => PHP_VERSION,
    ]);
});

Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('/dashboard', function () {
        return Inertia::render('Dashboard');
    })->name('dashboard');

    Route::get('/map', function () {
        return Inertia::render('StrayMap');
    })->name('map');

    // For the homepage
    Route::get('/home', [PostController::class, 'index'])->name('home');

    //For the uploading logic
    Route::post('/upload-image', [UploadTemporaryImageController::class, 'upload']);
    Route::delete('/revert/{folder}', [DeleteTemporaryImageController::class, 'delete']);
    Route::post('/post-upload', [PostController::class, 'uploadPost'])->name('post.uploadPost');
    Route::delete('/post-delete/{id}', [PostController::class, 'deletePost'])->name("deletePost");
    Route::patch('/post-update/{id}', [PostController::class, 'updatePost'])->middleware(['auth', 'verified'])
    ->name("updatePost");

    Route::post('/post/comment', [CommentController::class, 'createComment'])->name('createComment');

    Route::get('/cctv-monitor', [CCTVController::class, 'monitor'])->name('cctv.monitor');
    Route::get('/cctv', [CCTVController::class, 'view'])->name('cctv.view');
    Route::get('/cctv/detect', [CCTVController::class, 'detect'])->name('cctv.detect');
    
    Route::post('/upload-video', [VideoController::class, 'uploadVideo']);
    Route::post('/store-snapshot', [VideoController::class, 'storeSnapshot']);
    Route::get('/snapshots', [VideoController::class, 'getSnapshots']);

    //For the profile
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');


});

require __DIR__.'/auth.php';
