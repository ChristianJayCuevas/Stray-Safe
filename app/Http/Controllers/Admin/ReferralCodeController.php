<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\ReferralCode;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Inertia\Inertia;

class ReferralCodeController extends Controller
{
    public function index()
    {
        $referralCodes = ReferralCode::all();
        
        // Get users who have used referral codes
        $usersWithReferralCodes = \App\Models\User::whereNotNull('referral_code')->get();
        
        // Calculate usage counts for each code
        $codeCounts = $usersWithReferralCodes->groupBy('referral_code')
            ->map(function($users) {
                return $users->count();
            });
        
        // Update referral code usage counts in the database
        foreach ($referralCodes as $code) {
            if (isset($codeCounts[$code->code])) {
                $actualCount = $codeCounts[$code->code];
                
                // Only update if the count is different
                if ($code->usage_count != $actualCount) {
                    $code->usage_count = $actualCount;
                    
                    // Deactivate if max uses reached and max uses is not unlimited (0)
                    if ($code->max_uses > 0 && $code->usage_count >= $code->max_uses) {
                        $code->is_active = false;
                    }
                    
                    $code->save();
                }
            }
        }
        
        // Reload the codes after updates
        $referralCodes = ReferralCode::all();
        
        // Format the redemption data
        $redemptions = $usersWithReferralCodes->map(function($user) {
            return [
                'id' => $user->id,
                'code' => $user->referral_code,
                'user' => [
                    'name' => $user->name,
                    'avatar' => null, // Add avatar if available
                ],
                'created_at' => $user->created_at,
            ];
        });

        return Inertia::render('Admin/ReferralCodes/Index', [
            'referralCodes' => $referralCodes,
            'redemptions' => $redemptions,
        ]);
    }

    public function store(Request $request)
    {
        // Log debugging info
        \Log::info('CSRF Token in request: ' . $request->header('X-CSRF-TOKEN'));
        \Log::info('Session token: ' . csrf_token());
        \Log::info('Request method: ' . $request->method());
        \Log::info('Request path: ' . $request->path());
        \Log::info('Request is AJAX: ' . ($request->ajax() ? 'Yes' : 'No'));
        \Log::info('Request wants JSON: ' . ($request->wantsJson() ? 'Yes' : 'No'));
        \Log::info('Request data: ' . json_encode($request->all()));
        
        $validated = $request->validate([
            'description' => 'required|string|max:255',
            'code' => 'nullable|string|min:6|max:20|unique:referral_codes,code',
            'max_uses' => 'required|integer|min:0',
            'expires_at' => 'nullable|date',
        ]);

        // Generate a code if one wasn't provided
        $code = $request->code;
        if (empty($code)) {
            $code = 'BRGY' . strtoupper(Str::random(6));
        }

        $referralCode = ReferralCode::create([
            'code' => $code,
            'description' => $request->description,
            'max_uses' => $request->max_uses,
            'expires_at' => $request->expires_at,
            'is_active' => true,
            'usage_count' => 0,
        ]);

        // Always return a redirect back for Inertia
        return redirect()->back()->with('success', 'Referral code generated successfully.');
    }

    public function update(Request $request, $id)
    {
        $referralCode = ReferralCode::findOrFail($id);

        $validated = $request->validate([
            'description' => 'required|string|max:255',
            'max_uses' => 'required|integer|min:0',
            'expires_at' => 'nullable|date',
            'is_active' => 'required|boolean',
        ]);

        $referralCode->update([
            'description' => $request->description,
            'max_uses' => $request->max_uses,
            'expires_at' => $request->expires_at,
            'is_active' => $request->is_active,
        ]);

        // Always return a redirect back for Inertia
        return redirect()->back()->with('success', 'Referral code updated successfully.');
    }

    public function toggleStatus(Request $request, $id)
    {
        $referralCode = ReferralCode::findOrFail($id);
        $referralCode->is_active = !$referralCode->is_active;
        $referralCode->save();

        // Always return a redirect back for Inertia
        return redirect()->back()->with('success', 'Referral code status updated successfully.');
    }

    public function destroy(Request $request, $id)
    {
        $referralCode = ReferralCode::findOrFail($id);
        $referralCode->delete();

        // Always return a redirect back for Inertia
        return redirect()->back()->with('success', 'Referral code deleted successfully.');
    }
} 