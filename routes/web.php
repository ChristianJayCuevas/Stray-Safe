<?php
use App\Http\Controllers\{
    ProfileController,
    PostController,
    UploadTemporaryImageController,
    DeleteTemporaryImageController,
    CommentController,
    CCTVController,
    CameraPinController,
};
use Illuminate\Foundation\Application;
use Illuminate\Support\Facades\Route;
use Illuminate\Http\Request;
use Inertia\Inertia;
use App\Http\Controllers\API\UserController;
use App\Http\Controllers\MapPinController;
use App\Http\Controllers\StreamProxyController;
use App\Http\Controllers\StreamController;

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
    Route::get('/registeredpets', function () {
        return Inertia::render('RegisteredPets');
    })->name('registeredpets');
    //For the uploading logic
    Route::post('/upload-image', [UploadTemporaryImageController::class, 'upload']);
    Route::delete('/revert/{folder}', [DeleteTemporaryImageController::class, 'delete']);
    Route::post('/post-upload', [PostController::class, 'uploadPost'])->name('post.uploadPost');
    Route::delete('/post-delete/{id}', [PostController::class, 'deletePost'])->name("deletePost");
    Route::patch('/post-update/{id}', [PostController::class, 'updatePost'])->middleware(['auth', 'verified'])
    ->name("updatePost");

    Route::post('/post/comment', [CommentController::class, 'createComment'])->name('createComment');

    Route::get('/cctv-monitor', [CCTVController::class, 'monitor'])->name('cctv.monitor');
    Route::get('/stream-test', function () {
        return Inertia::render('StreamTest');
    })->name('stream.test');
    Route::get('/cctv', [CCTVController::class, 'view'])->name('cctv.view');
    Route::get('/cctv/detect', [CCTVController::class, 'detect'])->name('cctv.detect');
    
    // Stream proxy routes to handle CORS
    Route::options('stream-proxy/{path?}', [StreamProxyController::class, 'options'])
        ->where('path', '.*');
    Route::get('stream-proxy/{path?}', [StreamProxyController::class, 'proxy'])
        ->where('path', '.*');
        
    // New stream controller routes
    Route::get('stream/{path}', [StreamController::class, 'proxyStream'])
        ->where('path', '.*');
    Route::get('api/streams', [StreamController::class, 'getStreams']);
    Route::get('api/streams/test/{streamId}', [StreamController::class, 'testStream']);

    Route::post('/pin', [MapPinController::class, 'store']); // For regular pins
    Route::post('/camera-pin', [CameraPinController::class, 'store']); // Camera pin with dedicated controller
    Route::get('/pins', [MapPinController::class, 'index']);
    Route::delete('/pins/{id}', [MapPinController::class, 'destroy']); // Delete a pin

    Route::post('/cctvs', [CCTVController::class, 'store'])->name('cctvs.store');
    Route::get('/cctvs', [CCTVController::class, 'getCustomCCTVs'])->name('cctvs.index');
    Route::delete('/cctvs/{id}', [CCTVController::class, 'destroy'])->name('cctvs.destroy');


    Route::post('/user/image', [UserController::class, 'updateProfileImage']);
    Route::post('/user/signup', [UserController::class, 'register']);
    Route::post('/mobilelogin', [UserController::class, 'login']);
    Route::get('/mobileusers', [UserController::class, 'fetchUsers']);
    Route::get('mobileuser/me', [UserController::class, 'fetchLoggedInUser']);
    Route::get('/mobileregisteredanimals', [MobileRegisteredAnimalController::class, 'fetchRegisteredAnimals']);
    Route::post('/mobileregisteredanimals', [MobileRegisteredAnimalController::class, 'storeRegisteredAnimal']);

   
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');


});

require __DIR__.'/auth.php';
