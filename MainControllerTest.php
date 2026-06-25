<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Tests\TestCase;

class MainControllerTest extends TestCase
{
    public function testHelloWorld()
    {
        $response = $this->get('/hello-world');

        $response->assertStatus(200);
        $response->assertSee('Hello, World!');
    }
}