<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class ReferralCode extends Model
{
    use HasFactory;

    protected $fillable = [
        'code',
        'description',
        'is_active',
        'max_uses',
        'usage_count',
        'expires_at'
    ];

    protected $casts = [
        'is_active' => 'boolean',
        'max_uses' => 'integer',
        'usage_count' => 'integer',
        'expires_at' => 'datetime'
    ];

    public function isValid()
    {
        $isActive = $this->is_active;
        $notExpired = !$this->expires_at || $this->expires_at->isFuture();
        $usesAvailable = $this->max_uses === 0 || $this->usage_count < $this->max_uses;
        
        return $isActive && $notExpired && $usesAvailable;
    }
} 