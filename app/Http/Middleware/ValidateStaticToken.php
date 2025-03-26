<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class ValidateStaticToken
{
    /**
     * Handle an incoming request.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \Closure  $next
     * @return mixed
     */
    public function handle(Request $request, Closure $next)
    {
        $token = $request->header('Authorization');

        if ($token !== 'Bearer ' . API_ACCESS_TOKEN) {
            return response()->json(['error' => 'Unauthorized'], 401);
        }

        return $next($request);
    }
}
