<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\MapPinController;
Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');
Route::post('/pin', [MapPinController::class, 'store']);
Route::get('/pins', [MapPinController::class, 'index']);
Route::get('/recent-sightings', [MapPinController::class, 'recentSightings']);
Route::get('/snapshots', [MapPinController::class, 'getSnapshots']);
Route::get('/snapshots/recent', [MapPinController::class, 'getRecentSnapshots']);
