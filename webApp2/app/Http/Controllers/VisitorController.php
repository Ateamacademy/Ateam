<?php

namespace App\Http\Controllers;

use App\Models\Visitor;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;

class VisitorController extends Controller
{
    /**
     * Display a listing of the resource.
     *
     * @return \Illuminate\Http\Response
     */
    public function index()
    {
        //
    }

    /**
     * Show the form for creating a new resource.
     *
     * @return \Illuminate\Http\Response
     */
    public function create()
    {
        //
    }

    /**
     * Store a newly created resource in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\Response
     */
    public function store(Request $request)
    {
        //
    }

    /**
     * Display the specified resource.
     *
     * @param  \App\Models\Visitor  $visitor
     * @return \Illuminate\Http\Response
     */
    public function show(Visitor $visitor)
    {
        //
    }

    /**
     * Show the form for editing the specified resource.
     *
     * @param  \App\Models\Visitor  $visitor
     * @return \Illuminate\Http\Response
     */
    public function edit(Visitor $visitor)
    {
        //
    }

    /**
     * Update the specified resource in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \App\Models\Visitor  $visitor
     * @return \Illuminate\Http\Response
     */
    public function update(Request $request, Visitor $visitor)
    {
        //
    }

    /**
     * Remove the specified resource from storage.
     *
     * @param  \App\Models\Visitor  $visitor
     * @return \Illuminate\Http\Response
     */
    public function destroy(Visitor $visitor)
    {
        //
    }

    public function landingSignUp(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'name' => 'required|max:80',
            'email' => 'required|email|max:255|unique:visitors,email',
            'option' => 'required|max:255',
            'subject' => 'required|max:255',
            'message' => 'nullable|max:2000',
        ]);

        if ($validator->fails()) {
            return redirect('/#signUpForm')
                ->withErrors($validator)
                ->withInput();
        }



        $visitor = new Visitor();
        $visitor->name = $request->input('name');
        $visitor->email = $request->input('email');
        $visitor->option = $request->input('option');
        $visitor->subject = $request->input('subject');
        $visitor->message = $request->input('message');



        if ($visitor->save()) {
            return view('pages.thankyou');
        }
    }

    public function emailOnlySignUp(Request $request)
    {

        $validator = Validator::make($request->all(), [
            'email' => 'required|email|max:255|unique:visitors,email',
        ]);

        if ($validator->fails()) {
            return redirect('/#topForm')
                ->withErrors($validator, 'emailSignup')
                ->withInput();
        }

        $visitor = new Visitor();
        $visitor->email = $request->input('email');
        if ($visitor->save()) {
            return view('pages.thankyou');
        }
    }
}
