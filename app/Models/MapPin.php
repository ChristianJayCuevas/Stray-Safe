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
        'cone_coordinates' => 'array',
        'cone_center' => 'array',
        'cone_radius' => 'float',
        'cone_direction' => 'float',
        'cone_angle' => 'float',
    ];

    protected $fillable = [
        'animal_type',
        'stray_status',
        'latitude',
        'longitude',
        'snapshot_path',
        'is_camera',
        'camera_id',
        'camera_name',
        'hls_url',
        'conical_view',
        'viewing_direction',
        'viewing_angle',
        'perception_range',
        'original_id',
        'location',
        'rtmp_key',
        'user_map_id',
        'cone_coordinates',
        'cone_center',
        'cone_radius',
        'cone_direction',
        'cone_angle',
    ];

    /**
     * Get the user map this pin belongs to
     */
    public function userMap()
    {
        return $this->belongsTo(UserMap::class, 'user_map_id');
    }
}
