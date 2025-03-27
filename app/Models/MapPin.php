<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class MapPin extends Model
{
    use HasFactory;

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
        'viewing_direction',
        'viewing_angle',
        'conical_view',
        'perception_range',
        'rtmp_key',
        'original_id',
        'location',
    ];
}
