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
        $referralCodes = ReferralCode::with('user')->get();

        return Inertia::render('Admin/ReferralCodes/Index', [
            'referralCodes' => $referralCodes,
        ]);
    }

    public function store(Request $request)
    {
        $request->validate([
            'count' => 'required|integer|min:1|max:10',
        ]);

        $codes = [];
        for ($i = 0; $i < $request->count; $i++) {
            $code = 'BRGY' . strtoupper(Str::random(6));
            $referralCode = ReferralCode::create([
                'code' => $code,
                'is_used' => false,
                'expires_at' => now()->addYear(),
            ]);
            $codes[] = $referralCode;
        }

        return redirect()->back()->with('success', 'Referral codes generated successfully.');
    }
} 