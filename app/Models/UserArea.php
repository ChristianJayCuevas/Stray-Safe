<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class UserArea extends Model
{
    use HasFactory;

    /**
     * The attributes that are mass assignable.
     *
     * @var array
     */
    protected $fillable = [
        'user_id',
        'user_map_id',
        'feature_id',
        'name',
        'description',
        'geometry',
        'properties',
    ];

    /**
     * Get the user that owns the area.
     */
    public function user()
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get the map that this area belongs to.
     */
    public function userMap()
    {
        return $this->belongsTo(UserMap::class, 'user_map_id');
    }
}
