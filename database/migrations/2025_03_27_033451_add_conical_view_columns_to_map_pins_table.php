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
            $table->decimal('viewing_direction', 5, 2)->nullable();
            $table->decimal('viewing_angle', 5, 2)->nullable();
            $table->boolean('conical_view')->default(false);
            $table->decimal('perception_range', 8, 2)->nullable();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('map_pins', function (Blueprint $table) {
            $table->dropColumn(['viewing_direction', 'viewing_angle', 'conical_view', 'perception_range']);
        });
    }
};
