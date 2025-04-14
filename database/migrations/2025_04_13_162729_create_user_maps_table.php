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
        Schema::create('user_maps', function (Blueprint $table) {
            $table->id();
            $table->foreignId('owner_id')->constrained('users')->onDelete('cascade');
            $table->string('name');
            $table->text('description')->nullable();
            $table->string('access_code', 10)->unique();
            $table->json('settings')->nullable();
            $table->json('default_view')->nullable(); // Store default center, zoom level
            $table->boolean('is_public')->default(false);
            $table->timestamps();
        });

        // Create pivot table for users who have access to maps
        Schema::create('user_map_access', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained('users')->onDelete('cascade');
            $table->foreignId('user_map_id')->constrained('user_maps')->onDelete('cascade');
            $table->enum('role', ['viewer', 'editor'])->default('viewer');
            $table->timestamps();
            
            // Each user can only have one role per map
            $table->unique(['user_id', 'user_map_id']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('user_map_access');
        Schema::dropIfExists('user_maps');
    }
};
