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
        Schema::table('map_pins', function (Blueprint $table) {
            // Add the is_camera field to distinguish camera pins
            $table->boolean('is_camera')->default(false);
            
            // Add camera-specific fields
            $table->string('camera_id')->nullable();
            $table->string('camera_name')->nullable();
            $table->string('hls_url')->nullable();
            
            // Make snapshot_path nullable since cameras may not have snapshots
            $table->string('snapshot_path')->nullable()->change();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('map_pins', function (Blueprint $table) {
            // Remove camera-specific fields
            $table->dropColumn('is_camera');
            $table->dropColumn('camera_id');
            $table->dropColumn('camera_name');
            $table->dropColumn('hls_url');
            
            // Restore snapshot_path to be required
            $table->string('snapshot_path')->nullable(false)->change();
        });
    }
};
