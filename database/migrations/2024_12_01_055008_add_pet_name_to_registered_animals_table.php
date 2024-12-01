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
    Schema::table('registered_animals', function (Blueprint $table) {
        $table->string('pet_name')->nullable(); // Add pet_name column, nullable if not mandatory
    });
}

public function down()
{
    Schema::table('registered_animals', function (Blueprint $table) {
        $table->dropColumn('pet_name'); // Rollback by removing the column
    });
}
};
