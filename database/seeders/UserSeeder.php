<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\User;

class UserSeeder extends Seeder
{
    public function run()
    {
        // Super Admin
        $superAdmin = User::create([
            'name' => 'Super Admin',
            'email' => 'superadmin@example.com',
            'password' => bcrypt('password'),
        ]);
        $superAdmin->assignRole('super_admin');

        // IT Admin
        $barangayOfficial = User::create([
            'name' => 'Barangay Sacred Heart',
            'email' => 'sacredheart@example.com',
            'password' => bcrypt('password'),
        ]);
        $barangayOfficial->assignRole('barangay_official');

        // Regular User
        $animalPound = User::create([
            'name' => 'Animal Pound',
            'email' => 'animalpound@example.com',
            'password' => bcrypt('password'),
        ]);
        $animalPound->assignRole('animal_pound');

        // Therapist
        $regularUser = User::create([
            'name' => 'Regular User',
            'email' => 'regular@example.com',
            'password' => bcrypt('password'),
        ]);
        $regularUser->assignRole('user');
    }
}
