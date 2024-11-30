<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class AddBreedToRegisteredAnimalsTable extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('registered_animals', function (Blueprint $table) {
            $table->string('breed')->nullable()->after('animal_type'); // Add nullable breed column after animal_type
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('registered_animals', function (Blueprint $table) {
            $table->dropColumn('breed'); // Remove the breed column
        });
    }
};

