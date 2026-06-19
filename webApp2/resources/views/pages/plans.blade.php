@extends('main')

@section('content')

<div class="mt-24 container mx-auto sm:px-6 lg:px-8 grid grid-cols-12 py-10 lg:py-20 plans gap-8">
    <div class="col-span-12 lg:col-span-10 lg:col-start-2 text-center">
        <h1 class="font-heading font-black text-7xl md:text-8xl xl:text-ateam-xl xl:leading-ateam-xl  text-center">
            OUR PLANS
        </h1>

    </div>

    <div class="col-span-12 lg:col-span-4 shadow-lg secondary px-6 py-8 mb-8 lg:mb-12">
        <h5 class="mb-4">ONE TO ONE PLAN</h5>
        <p><span class="font-heading text-ateam-blue text-7xl font-bold">£40</span><span
                class="text-ateam-black ml-2 text-lg">/hour</span>
        </p>
        <p class="my-8 text-ateam-dark-blue">Maximum Flexibility</p>

        <ul>
            <li>Lessons at your own convenience</li>
            <li>Any subject</li>
            <li>Subject specialist tutors</li>
            <li>Flexible timing</li>
        </ul>

        <a href="/#signUpForm"
            class="hover:bg-ateam-red hover:text-white text-center py-4 block w-full mt-8 lg:mt-12 tracking-wider border border-ateam-red text-ateam-red">CHOOSE
            PLAN</a>
    </div>
    <div
        class="primary col-span-12 lg:col-span-4 bg-ateam-blue text-white shadow-lg mt-9 lg:mt-0 px-6 py-8 mb-8 lg:mb-6">
        <h5 class="mb-4">WEEKLY PLAN GCSE</h5>
        <p><span class="font-heading text-7xl font-bold">£25</span><span class="ml-2 text-lg">/2 hours</span>
        </p>
        <p class="mt-2"><i>subject to termly payment, £400 Termly</i></p>
        <p class="my-8 text-ateam-blue-100">8 Hours Per Month</p>

        <ul>
            <li>Maximum structure</li>
            <li>Dedicated schedule</li>
            <li>Subject specialist tutors</li>
            <li>Free trial available</li>
        </ul>

        <a href="/#signUpForm"
            class="hover:bg-ateam-red hover:text-white text-center py-4 block w-full  mt-8 lg:mt-12 tracking-wider border bg-white text-ateam-red">CHOOSE
            PLAN</a>
    </div>
    <div class="col-span-12 lg:col-span-4 shadow-lg mt-9 lg:mt-0 px-6 py-8 mb-8 lg:mb-12 secondary">
        <h5 class="mb-4">WEEKLY PLAN A-LEVEL</h5>
        <p><span class="font-heading text-ateam-blue text-7xl font-bold">£31.25</span><span
                class="text-ateam-black ml-2 text-lg">/2 hours</span>
        </p>
        <p class="mt-2"><i>subject to termly payment, £500 Termly</i></p>
        <p class="my-8 text-ateam-dark-blue">8 Hours Per Month</p>
        <ul>
            <li>Maximum structure</li>
            <li>Dedicated schedule</li>
            <li>Subject specialist tutors</li>
            <li>Free trial available</li>
        </ul>

        <a href="/#signUpForm"
            class="hover:bg-ateam-red hover:text-white text-center py-4 block w-full  mt-8 lg:mt-12 tracking-wider border border-ateam-red text-ateam-red">CHOOSE
            PLAN</a>
    </div>

</div>
@endsection