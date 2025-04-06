<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use Spatie\Permission\Models\Role;

class UserSeeder extends Seeder
{
    public function run(): void
    {
        // Create super admin
        $superAdmin = User::create([
            'name' => 'Super Admin',
            'email' => 'admin@straysafe.com',
            'password' => Hash::make('Admin@123'),
            'email_verified_at' => now(),
        ]);
        $superAdmin->assignRole('super_admin');

        // Create barangay official
        $barangayOfficial = User::create([
            'name' => 'Barangay Official',
            'email' => 'official@straysafe.com',
            'password' => Hash::make('Official@123'),
            'email_verified_at' => now(),
        ]);
        $barangayOfficial->assignRole('barangay_official');

        // Create animal pound staff
        $animalPound = User::create([
            'name' => 'Animal Pound Staff',
            'email' => 'pound@straysafe.com',
            'password' => Hash::make('Pound@123'),
            'email_verified_at' => now(),
        ]);
        $animalPound->assignRole('animal_pound');

        // Create a regular viewer
        $viewer = User::create([
            'name' => 'Regular Viewer',
            'email' => 'viewer@straysafe.com',
            'password' => Hash::make('Viewer@123'),
            'email_verified_at' => now(),
        ]);
        $viewer->assignRole('viewer');
    }
}
