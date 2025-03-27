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
            $table->string('rtmp_key')->nullable();
            $table->string('original_id')->nullable();
            $table->string('location')->nullable();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('map_pins', function (Blueprint $table) {
            $table->dropColumn(['rtmp_key', 'original_id', 'location']);
        });
    }
};
