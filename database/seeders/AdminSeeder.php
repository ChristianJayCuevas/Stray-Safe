<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class AdminSeeder extends Seeder
{
    public function run(): void
    {
        // Create admin user
        User::create([
            'name' => 'Admin',
            'email' => 'admin@straysafe.com',
            'password' => Hash::make('Admin@123'), // You should change this password after first login
            'referral_code' => null, // Admin doesn't need a referral code
        ])->assignRole('admin'); // Assuming you're using spatie/laravel-permission package
    }
} 