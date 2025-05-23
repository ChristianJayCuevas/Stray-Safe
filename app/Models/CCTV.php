<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class CCTV extends Model
{
    use HasFactory;

    /**
     * The table associated with the model.
     *
     * @var string
     */
    protected $table = 'cctvs';

    /**
     * The attributes that are mass assignable.
     *
     * @var array<int, string>
     */
    protected $fillable = [
        'camera_name',
        'location',
        'stream_url',
        'original_stream_id',
        'status',
        'is_custom'
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array<string, string>
     */
    protected $casts = [
        'is_custom' => 'boolean',
    ];

    /**
     * Set the stream URL, converting http to https.
     *
     * @param  string  $value
     * @return void
     */
    public function setStreamUrlAttribute($value)
    {
        $this->attributes['stream_url'] = str_replace('http://', 'https://', $value);
    }
}
