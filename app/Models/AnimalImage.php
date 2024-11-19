<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class AnimalImage extends Model
{
    use HasFactory;

    protected $fillable = ['registered_animal_id', 'file_name', 'file_path'];

    // Relationship with RegisteredAnimal
    public function registeredAnimal()
    {
        return $this->belongsTo(RegisteredAnimal::class);
    }
}
