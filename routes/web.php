<?php
use App\Http\Controllers\{
    ProfileController,
    PostController,
    UploadTemporaryImageController,
    DeleteTemporaryImageController,
    CommentController,
    CCTVController,
    CameraPinController,
    RoleController,
};
use Illuminate\Foundation\Application;
use Illuminate\Support\Facades\Route;
use Illuminate\Http\Request;
use Inertia\Inertia;
use App\Http\Controllers\API\UserController;
use App\Http\Controllers\MapPinController;
use App\Http\Controllers\StreamProxyController;
use App\Http\Controllers\StreamController;
use Illuminate\Support\Facades\Auth;
use Spatie\Permission\Middleware\PermissionMiddleware;
Route::get('/', function () {
    return Inertia::render('Welcome', [
        'canLogin' => Route::has('login'),
        'canRegister' => Route::has('register'),
        'laravelVersion' => Application::VERSION,
        'phpVersion' => PHP_VERSION,
    ]);
});

// Auth check route for web app
Route::get('/auth/check', function () {
    if (Auth::check()) {
        return response()->json([
            'authenticated' => true,
            'user' => Auth::user()
        ]);
    }
    
    return response()->json(['authenticated' => false]);
});

// Main application routes
Route::middleware(['auth'])->group(function () {
    Route::get('/dashboard', function () {
        return Inertia::render('Dashboard');
    })->name('dashboard');

    Route::get('/map', function () {
        return Inertia::render('StrayMap');
    })->name('map');

    Route::get('/home', [PostController::class, 'index'])->name('home');
    Route::get('/registeredpets', function () {
        return Inertia::render('RegisteredPets');
    })->name('registeredpets');

    // Post related routes
    Route::post('/upload-image', [UploadTemporaryImageController::class, 'upload']);
    Route::delete('/revert/{folder}', [DeleteTemporaryImageController::class, 'delete']);
    Route::post('/post-upload', [PostController::class, 'uploadPost'])->name('post.uploadPost');
    Route::delete('/post-delete/{id}', [PostController::class, 'deletePost'])->name("deletePost");
    Route::patch('/post-update/{id}', [PostController::class, 'updatePost'])->name("updatePost");
    Route::post('/post/comment', [CommentController::class, 'createComment'])->name('createComment');

    // CCTV routes
    Route::get('/cctv-monitor', [CCTVController::class, 'monitor'])->name('cctv.monitor');
    Route::get('/stream-test', function () {
        return Inertia::render('StreamTest');
    })->name('stream.test');
    Route::get('/cctv', [CCTVController::class, 'view'])->name('cctv.view');
    Route::get('/cctv/detect', [CCTVController::class, 'detect'])->name('cctv.detect');
    
    // Map and pin routes
    Route::post('/pin', [MapPinController::class, 'store']);
    Route::post('/camera-pin', [CameraPinController::class, 'store']);
    Route::get('/pins', [MapPinController::class, 'index']);
    Route::delete('/pins/{id}', [MapPinController::class, 'destroy']);

    // CCTV management routes
    Route::post('/cctvs', [CCTVController::class, 'store'])->name('cctvs.store');
    Route::get('/cctvs', [CCTVController::class, 'getCustomCCTVs'])->name('cctvs.index');
    Route::delete('/cctvs/{id}', [CCTVController::class, 'destroy'])->name('cctvs.destroy');

    // Profile routes
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');

    // Admin Routes
    Route::prefix('admin')->name('admin.')->group(function () {
        // Role Management
        Route::get('/roles', [App\Http\Controllers\Admin\RoleController::class, 'index'])
            ->name('roles')
            ->middleware(PermissionMiddleware::class . ':manage_roles');
    
        Route::post('/roles', [App\Http\Controllers\Admin\RoleController::class, 'store'])
            ->name('roles.store')
            ->middleware(PermissionMiddleware::class . ':manage_roles');
    
        Route::put('/roles/{role}', [App\Http\Controllers\Admin\RoleController::class, 'update'])
            ->name('roles.update')
            ->middleware(PermissionMiddleware::class . ':manage_roles');
    
        Route::delete('/roles/{role}', [App\Http\Controllers\Admin\RoleController::class, 'destroy'])
            ->name('roles.destroy')
            ->middleware(PermissionMiddleware::class . ':manage_roles');
    
        // User Management
        Route::get('/users', [App\Http\Controllers\Admin\UserController::class, 'index'])
            ->name('users')
            ->middleware(PermissionMiddleware::class . ':manage_users');
    
        Route::post('/users/{user}/roles', [App\Http\Controllers\Admin\UserController::class, 'assignRoles'])
            ->name('users.assign-roles')
            ->middleware(PermissionMiddleware::class . ':manage_users');
    
        // Referral Codes
        Route::get('/referral-codes', [App\Http\Controllers\Admin\ReferralCodeController::class, 'index'])
            ->name('referral-codes')
            ->middleware(PermissionMiddleware::class . ':manage_referral_codes');
    
        Route::post('/referral-codes', [App\Http\Controllers\Admin\ReferralCodeController::class, 'store'])
            ->name('referral-codes.store')
            ->middleware(PermissionMiddleware::class . ':manage_referral_codes');
    });
});

require __DIR__.'/auth.php';
