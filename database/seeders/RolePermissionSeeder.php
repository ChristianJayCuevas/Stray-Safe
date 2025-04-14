<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Role;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\PermissionRegistrar;

class RolePermissionSeeder extends Seeder
{
    public function run(): void
    {
        // Reset cache
        app()[PermissionRegistrar::class]->forgetCachedPermissions();

        // List of permissions with descriptions
        $permissions = [
            'view_users' => 'Can view users',
            'create_users' => 'Can create users',
            'edit_users' => 'Can edit users',
            'delete_users' => 'Can delete users',
            'manage_users' => 'Can manage user roles and access',
            'manage_roles' => 'Can manage roles and permissions',
            'manage_referral_codes' => 'Can manage referral codes',
            'manage_animals' => 'Can manage animal registrations',
            'view_animals' => 'Can view animal registrations',
            'manage_posts' => 'Can manage posts and announcements',
            'manage_cctv' => 'Can manage CCTV cameras and streams',
            'view_cctv' => 'Can view CCTV feeds',
            'manage_map_pins' => 'Can manage map pins and locations',
            'manage_maps' => 'Can manage user maps and access codes',
            'view_analytics' => 'Can view analytics and reports',
            'manage_notifications' => 'Can manage notifications',
        ];

        // Create or update permissions
        foreach ($permissions as $name => $description) {
            Permission::updateOrCreate(
                ['name' => $name, 'guard_name' => 'web'],
                []
            );
        }

        // Define roles with specific permissions
        $roles = [
            'super_admin' => array_keys($permissions),
            'barangay_official' => [
                'manage_animals',
                'view_animals',
                'manage_posts',
                'view_cctv',
                'manage_map_pins',
                'manage_maps',
                'manage_notifications',
            ],
            'animal_pound' => [
                'view_animals',
                'manage_animals',
                'view_cctv',
            ],
            'viewer' => [
                'view_animals',
                'view_cctv',
            ],
        ];

        // Assign permissions to roles
        foreach ($roles as $roleName => $permissionList) {
            $role = Role::firstOrCreate([
                'name' => $roleName,
                'guard_name' => 'web',
            ]);

            // Attach the permissions safely
            $role->syncPermissions($permissionList);
        }

        // Clear permission cache again after all assignments
        app()[PermissionRegistrar::class]->forgetCachedPermissions();
    }
}
