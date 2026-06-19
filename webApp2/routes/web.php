<?php

use App\Http\Controllers\VisitorController;
use App\Http\Controllers\PageController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Web Routes
|--------------------------------------------------------------------------
|
| Here is where you can register web routes for your application. These
| routes are loaded by the RouteServiceProvider within a group which
| contains the "web" middleware group. Now create something great!
|
*/

Route::get('/', function () {
    return view('welcome');
});

Route::get('/dashboard', [PageController::class, 'getDashboard'])->middleware(['auth'])->name('dashboard');

Route::post('/landing/signup', [VisitorController::class, 'landingSignUp']);
Route::post('/email/signup', [VisitorController::class, 'emailOnlySignUp']);
Route::get('/thankyou', [PageController::class, 'getThankyou']);
Route::get('/plans', [PageController::class, 'getPlans']);
require __DIR__ . '/auth.php';
