<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;
use Spatie\Permission\Traits\HasRoles;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable, HasRoles;

    protected $guard_name = 'web'; // Needed for Spatie permission checks

    protected $fillable = [
        'name',
        'email',
        'password',
        'profile_image_link',
        'referral_code',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'password' => 'hashed',
    ];

    // Optional: Custom helper if you still want this alias
    public function isAdmin(): bool
    {
        return $this->hasRole('super_admin'); // Assuming "admin" was a typo
    }

    public function userAreas()
    {
        return $this->hasMany(UserArea::class);
    }
    
    /**
     * Maps owned by this user
     */
    public function ownedMaps()
    {
        return $this->hasMany(UserMap::class, 'owner_id');
    }
    
    /**
     * Maps this user has access to (excluding owned maps)
     */
    public function accessibleMaps()
    {
        return $this->belongsToMany(UserMap::class, 'user_map_access', 'user_id', 'user_map_id')
                    ->withPivot('role')
                    ->withTimestamps();
    }
    
    /**
     * Get all maps this user can access (both owned and shared)
     */
    public function getAllAccessibleMaps()
    {
        // Get IDs of both owned and accessible maps
        $ownedMapIds = $this->ownedMaps()->pluck('id');
        $accessibleMapIds = $this->accessibleMaps()->pluck('user_maps.id');
        
        // Combine and get unique IDs
        $allMapIds = $ownedMapIds->merge($accessibleMapIds)->unique();
        
        // Return all maps
        return UserMap::whereIn('id', $allMapIds)->get();
    }
    
    /**
     * Check if user has a personal map
     */
    public function hasPersonalMap()
    {
        return $this->ownedMaps()->exists();
    }
    
    /**
     * Get user's personal map or null
     */
    public function getPersonalMap()
    {
        return $this->ownedMaps()->first();
    }
}
