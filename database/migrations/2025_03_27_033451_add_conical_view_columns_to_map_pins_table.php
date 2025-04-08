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
            if (!Schema::hasColumn('map_pins', 'conical_view')) {
                $table->boolean('conical_view')->default(false)->after('is_camera');
            }
            if (!Schema::hasColumn('map_pins', 'viewing_direction')) {
                $table->decimal('viewing_direction', 5, 2)->nullable()->after('conical_view');
            }
            if (!Schema::hasColumn('map_pins', 'viewing_angle')) {
                $table->decimal('viewing_angle', 5, 2)->nullable()->after('viewing_direction');
            }
            if (!Schema::hasColumn('map_pins', 'perception_range')) {
                $table->decimal('perception_range', 10, 2)->nullable()->after('viewing_angle');
            }
            
            // Add columns for cone data storage
            $table->json('cone_coordinates')->nullable()->after('perception_range');
            $table->json('cone_center')->nullable()->after('cone_coordinates');
            $table->decimal('cone_radius', 10, 2)->nullable()->after('cone_center');
            $table->decimal('cone_direction', 5, 2)->nullable()->after('cone_radius');
            $table->decimal('cone_angle', 5, 2)->nullable()->after('cone_direction');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('map_pins', function (Blueprint $table) {
            $table->dropColumn([
                'conical_view',
                'viewing_direction',
                'viewing_angle',
                'perception_range',
                'cone_coordinates',
                'cone_center',
                'cone_radius',
                'cone_direction',
                'cone_angle'
            ]);
        });
    }
};
