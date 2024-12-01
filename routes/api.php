<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\MapPinController;
use App\Http\Controllers\API\UserController;
use App\Http\Middleware\ValidateStaticToken;
use App\Http\Controllers\API\MobileRegisteredAnimalController;
use App\Http\Controllers\RegisteredAnimalController;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');
Route::post('/pin', [MapPinController::class, 'store']);
Route::get('/pins', [MapPinController::class, 'index']);
Route::get('/recent-sightings', [MapPinController::class, 'recentSightings']);
Route::get('/snapshots', [MapPinController::class, 'getSnapshots']);
Route::get('/snapshots/recent', [MapPinController::class, 'getRecentSnapshots']);


Route::get('/registered-animals', [RegisteredAnimalController::class, 'index']);
Route::post('/registered-animals', [RegisteredAnimalController::class, 'store']);
Route::put('/registered-animals/{id}', [RegisteredAnimalController::class, 'update']);
Route::delete('/registered-animals/{id}', [RegisteredAnimalController::class, 'destroy']);

/*Mobile API*/

Route::middleware([ValidateStaticToken::class])->group(function () {
    Route::post('/user/signup', [UserController::class, 'register']);
    Route::post('/mobilelogin', [UserController::class, 'login']);
    Route::get('/mobileusers', [UserController::class, 'fetchUsers']);
    Route::get('mobileuser/me', [UserController::class, 'fetchLoggedInUser']);
    Route::get('/mobileregisteredanimals', [MobileRegisteredAnimalController::class, 'fetchRegisteredAnimals']);
    Route::post('/mobileregisteredanimals', [MobileRegisteredAnimalController::class, 'storeRegisteredAnimal']);
});
