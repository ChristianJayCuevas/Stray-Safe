<?php

namespace Database\Seeders;

use App\Models\ReferralCode;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class ReferralCodeSeeder extends Seeder
{
    public function run(): void
    {
        // Generate 5 referral codes
        for ($i = 0; $i < 5; $i++) {
            ReferralCode::create([
                'code' => 'BRGY' . strtoupper(Str::random(6)), // Format: BRGY + 6 random characters
                'is_used' => false,
                'expires_at' => now()->addYear(), // Codes expire in 1 year
            ]);
        }
    }
} 