<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;
use App\Http\Resources\UserResource;
class PostResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    // public function toArray(Request $request): array
    // {
    //     return parent::toArray($request);
    // }
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'description' => $this->description,
            'likes_count' => $this->likes_count,
            'liked' => $this->liked,
            'postImages' => $this->postImages->map(function ($image) {
                return [
                    'post_id' => $image->post_id,
                    'post_image_path' => $image->post_image_path,
                ];
            }),
            'created_at' => $this->created_at->toDateTimeString(),
            'user' => new UserResource($this->whenLoaded('user')),
        ];
    }
}
