<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\TemporaryImage;

class UploadTemporaryImageController extends Controller
{
    public function upload(Request $request)
    {
        if($request->hasFile('image')){
            $image = $request->file('image');
            $fileName = $image->getClientOriginalName();
            $folder = uniqid('image-', true);
            $image->storeAs('/images/tmp/' . $folder, $fileName);

            TemporaryImage::create([
                'folder' => $folder,
                'file' => $fileName
            ]);
            return $folder;
        }
        return '';
      
    }
}
