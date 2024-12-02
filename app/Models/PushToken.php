<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class PushToken extends Model
{
    use HasFactory;

    protected $table = 'push_tokens'; // Ensure this matches your table name
    protected $fillable = ['token']; // Add fields that can be mass assigned
}
