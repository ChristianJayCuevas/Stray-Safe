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
        Schema::table('user_areas', function (Blueprint $table) {
            $table->foreignId('user_map_id')->nullable()->after('user_id')->constrained('user_maps')->nullOnDelete();
            $table->index('user_map_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('user_areas', function (Blueprint $table) {
            $table->dropForeign(['user_map_id']);
            $table->dropIndex(['user_map_id']);
            $table->dropColumn('user_map_id');
        });
    }
};
