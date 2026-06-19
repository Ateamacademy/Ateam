<?php

namespace App\Http\Controllers;

use Carbon\Carbon;
use App\Models\Visitor;
use Illuminate\Http\Request;

class PageController extends Controller
{
    public function getThankyou()
    {
        return view('pages.thankyou');
    }

    public function getPlans()
    {
        return view('pages.plans');
    }

    public function getDashboard()
    {
        $visitors = Visitor::latest()->paginate(30);

        return view('dashboard')->with('visitors', $visitors);
    }
}
