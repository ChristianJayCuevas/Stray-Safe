namespace App\Http\Controllers;

use App\Models\PushToken;
use Illuminate\Http\Request;

class PushTokenController extends Controller
{
    public function saveToken(Request $request)
    {
        $request->validate(['token' => 'required|string|unique:push_tokens']);

        PushToken::create(['token' => $request->token]);

        return response()->json(['message' => 'Push token saved successfully']);
    }
}
