<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class RegisteredAnimal extends Model
{
    use HasFactory;

    protected $fillable = [
        'owner',
        'contact',
        'animal_type',
        'picture',
        'status',
    ];
    public function images()
    {
        return $this->hasMany(AnimalImage::class, 'registered_animal_id');
    }
}
