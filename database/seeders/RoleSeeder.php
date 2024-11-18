<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Role;
use Spatie\Permission\Models\Permission;

class RoleSeeder extends Seeder
{
    public function run()
    {
        // Create permissions
        Permission::create(['name' => 'view analytics']);
        Permission::create(['name' => 'view maps']);
        Permission::create(['name' => 'view cctv']);
        Permission::create(['name' => 'view notifications']);

        Permission::create(['name' => 'create posts']);
        Permission::create(['name' => 'create cctv']);
        Permission::create(['name' => 'create maps']);

        Permission::create(['name' => 'edit posts']);
        Permission::create(['name' => 'edit cctv']);
        Permission::create(['name' => 'edit maps']);
        
        Permission::create(['name' => 'delete posts']);
        Permission::create(['name' => 'delete cctv']);
        Permission::create(['name' => 'delete maps']);

        Permission::create(['name' => 'view users']);
        Permission::create(['name' => 'edit users']);
        Permission::create(['name' => 'delete users']);
        Permission::create(['name' => 'ban users']);

        // Create roles and assign existing permissions
        $superAdminRole = Role::create(['name' => 'super_admin']);
        $superAdminRole->givePermissionTo([
            'view analytics',
            'view maps',
            'view cctv',
            'view notifications',
            'create posts',
            'create cctv',
            'create maps',
            'edit posts',
            'edit cctv',
            'edit maps',
            'delete posts',
            'delete cctv',
            'delete maps',
            'view users',
            'edit users',
            'delete users',
            'ban users',
        ]);

        $barangayOfficialRole = Role::create(['name' => 'barangay_official']);
        $barangayOfficialRole->givePermissionTo([
            'view analytics',
            'view maps',
            'view cctv',
            'view notifications',
            'create posts',
            'create cctv',
            'create maps',
            'edit posts',
            'edit cctv',
            'edit maps',
            'delete posts',
            'delete cctv',
            'delete maps',
        ]);

        $animalPoundRole = Role::create(['name' => 'animal_pound']);
        $animalPoundRole->givePermissionTo([
            'view analytics',
            'view maps',
            'view notifications',
        ]);

        // Create roles for user types without assigning permissions
        Role::create(['name' => 'user']);
    }
}
