<?php
// app/Http/Middleware/VerifyCsrfToken.php
namespace App\Http\Middleware;

use Illuminate\Foundation\Http\Middleware\VerifyCsrfToken as Middleware;
use Closure;
use Illuminate\Support\Facades\Log;

class VerifyCsrfToken extends Middleware
{
    /**
     * URIs that should be excluded from CSRF verification.
     *
     * @var array<int, string>
     */
    protected $except = [
        '/mobilelogin',
    ];
    
    /**
     * Handle an incoming request.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \Closure  $next
     * @return mixed
     *
     * @throws \Illuminate\Session\TokenMismatchException
     */
    public function handle($request, Closure $next)
    {
        try {
            return parent::handle($request, $next);
        } catch (\Illuminate\Session\TokenMismatchException $e) {
            Log::error('CSRF token mismatch', [
                'url' => $request->fullUrl(),
                'method' => $request->method(),
                'token_in_header' => $request->header('X-CSRF-TOKEN'),
                'token_in_form' => $request->input('_token'),
                'session_token' => csrf_token(),
                'session_id' => session()->getId(),
                'user_agent' => $request->userAgent(),
                'ip' => $request->ip(),
            ]);
            
            // Re-throw the exception to maintain default behavior
            throw $e;
        }
    }
}
