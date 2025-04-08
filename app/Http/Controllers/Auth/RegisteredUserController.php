<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\ReferralCode;
use App\Models\User;
use Illuminate\Auth\Events\Registered;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules;
use Inertia\Inertia;
use Inertia\Response;

class RegisteredUserController extends Controller
{
    /**
     * Display the registration view.
     */
    public function create(): Response
    {
        return Inertia::render('Auth/Register');
    }

    /**
     * Handle an incoming registration request.
     *
     * @throws \Illuminate\Validation\ValidationException
     */
    public function store(Request $request): RedirectResponse
    {
        $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|string|lowercase|email|max:255|unique:'.User::class,
            'password' => ['required', 'confirmed', Rules\Password::defaults()],
            'referral_code' => ['required', 'string', 'exists:referral_codes,code'],
        ]);

        $referralCode = ReferralCode::where('code', $request->referral_code)->first();

        if (!$referralCode->isValid()) {
            return back()->withErrors([
                'referral_code' => 'The referral code is invalid or has expired.',
            ]);
        }

        $user = User::create([
            'name' => $request->name,
            'email' => $request->email,
            'password' => Hash::make($request->password),
            'referral_code' => $request->referral_code,
        ]);

        // Increment usage count and deactivate if max uses reached
        $referralCode->usage_count = $referralCode->usage_count + 1;
        
        // Deactivate if max uses reached and max uses is not unlimited (0)
        if ($referralCode->max_uses > 0 && $referralCode->usage_count >= $referralCode->max_uses) {
            $referralCode->is_active = false;
        }
        
        $referralCode->save();

        event(new Registered($user));

        Auth::login($user);

        return redirect(route('dashboard', absolute: false));
    }

}
