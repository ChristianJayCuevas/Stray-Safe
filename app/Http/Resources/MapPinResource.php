<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class MapPinResource extends JsonResource
{
    /**
     * Transform the resource into an array.
     *
     * @return array<string, mixed>
     */
    public function toArray($request)
    {
        return [
            'id' => $this->id,
            'camera_id' => $this->camera_id,
            'camera_name' => $this->camera_name,
            'rtmp_key' => $this->rtmp_key,
            'location' => $this->location,
            'animal_type' => $this->animal_type,
            'description' => $this->description,
            'status' => $this->status,
            'coordinates' => $this->coordinates,
            'latitude' => $this->latitude,
            'longitude' => $this->longitude,
            'perception_range' => $this->perception_range,
            'viewing_direction' => $this->viewing_direction,
            'viewing_angle' => $this->viewing_angle,
            'conical_view' => $this->conical_view,
            'snapshot_path' => $this->snapshot_path,
            'hls_url' => $this->hls_url,
            'detection_timestamp' => $this->detection_timestamp,
            // add other relevant fields
        ];
    }
}
