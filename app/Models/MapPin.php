<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class MapPin extends Model
{
    use HasFactory;
    protected $casts = [
        'coordinates' => 'array',
        'conical_view' => 'boolean',
        'perception_range' => 'float',
        'viewing_direction' => 'float',
        'viewing_angle' => 'float',
    ];
    
    protected $fillable = [
        'animal_type',
        'stray_status', // New attribute
        'latitude',
        'longitude',
        'snapshot_path',
        'is_camera',
        'camera_id',
        'camera_name',
        'hls_url',
    ];
}
