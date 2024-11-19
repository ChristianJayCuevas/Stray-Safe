<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up()
{
    Schema::create('animal_images', function (Blueprint $table) {
        $table->id();
        $table->foreignId('registered_animal_id')->constrained()->cascadeOnDelete(); // Foreign key
        $table->string('file_name'); // Name of the file
        $table->string('file_path'); // Path to the file
        $table->timestamps();
    });
}

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('animal_images');
    }
};
