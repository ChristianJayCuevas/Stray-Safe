<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Str;

class UserMap extends Model
{
    use HasFactory;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<int, string>
     */
    protected $fillable = [
        'owner_id',
        'name',
        'description',
        'access_code',
        'settings',
        'default_view',
        'is_public',
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array<string, string>
     */
    protected $casts = [
        'settings' => 'array',
        'default_view' => 'array',
        'is_public' => 'boolean',
    ];

    /**
     * Generate a unique access code for the map
     * 
     * @return string
     */
    public static function generateAccessCode()
    {
        do {
            $code = strtoupper(Str::random(6)); // 6-character alphanumeric code
        } while (self::where('access_code', $code)->exists());
        
        return $code;
    }

    /**
     * The owner of the map
     */
    public function owner()
    {
        return $this->belongsTo(User::class, 'owner_id');
    }

    /**
     * The users who have access to this map
     */
    public function viewers()
    {
        return $this->belongsToMany(User::class, 'user_map_access', 'user_map_id', 'user_id')
                    ->withPivot('role')
                    ->withTimestamps();
    }

    /**
     * The pins associated with this map
     */
    public function pins()
    {
        return $this->hasMany(MapPin::class);
    }

    /**
     * Get the areas associated with this map
     */
    public function areas()
    {
        return $this->hasMany(UserArea::class);
    }

    /**
     * Check if a user has access to this map
     *
     * @param User $user
     * @return bool
     */
    public function userHasAccess(User $user)
    {
        if ($user->id === $this->owner_id) {
            return true; // Owner always has access
        }

        if ($this->is_public) {
            return true; // Public maps are accessible to everyone
        }
        
        return $this->viewers()->where('users.id', $user->id)->exists();
    }
    
    /**
     * Get the role of a user for this map
     *
     * @param User $user
     * @return string|null
     */
    public function getUserRole(User $user)
    {
        if ($user->id === $this->owner_id) {
            return 'owner';
        }
        
        $access = $this->viewers()->where('users.id', $user->id)->first();
        return $access ? $access->pivot->role : null;
    }
}
