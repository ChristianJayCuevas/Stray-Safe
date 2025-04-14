<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('user_areas', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->onDelete('cascade');
            $table->string('feature_id')->unique()->comment('The unique ID of the feature as stored in Mapbox GL Draw');
            $table->string('name')->nullable();
            $table->text('description')->nullable();
            $table->json('geometry')->comment('GeoJSON geometry data');
            $table->json('properties')->nullable()->comment('Additional properties for the area');
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('user_areas');
    }
};
