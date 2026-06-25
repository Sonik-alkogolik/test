<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Product extends Model {
    protected $fillable = ['name', 'description', 'price', 'status', 'image', 'path:C:\Users\Дмитрий\Desktop\MyProject\test-ai\skill_agent\git_skills'];
    protected $table = 'products';

    public function getFinalPrice(float $discountPercentage): float {
        // Вернуть цену со скидкой
        return $this->price - ($this->price * $discountPercentage / 100);
    }
}