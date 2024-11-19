<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreateRegisteredAnimalsTable extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('registered_animals', function (Blueprint $table) {
            $table->id();
            $table->string('owner');
            $table->string('contact');
            $table->enum('animal_type', ['dog', 'cat']);
            $table->string('picture')->nullable();
            $table->enum('status', ['caught', 'free', 'claimed'])->default('free');
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('registered_animals');
    }
}