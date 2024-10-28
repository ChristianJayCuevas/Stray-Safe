<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\TemporaryImage;
use Illuminate\Support\Facades\Storage;

class DeleteTemporaryImageController extends Controller
{
    public function delete($folder)
    {
        $temporaryImage = TemporaryImage::where('folder', $folder)->first();
        if($temporaryImage){
            Storage::deleteDirectory('images/tmp/' . $temporaryImage->folder);
            $temporaryImage->delete();
        }
        return '';
    }
}
