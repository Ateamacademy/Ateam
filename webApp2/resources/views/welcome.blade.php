@extends('main')

@section('content')
<div class="mt-24 container mx-auto sm:px-6 lg:px-8 xl:grid xl:grid-cols-12 py-10 lg:py-20 top-banner">
    <div class="col-span-12 lg:col-span-10 lg:col-start-2 text-center">
        <h1
            class="slide-in from-top font-heading font-black text-7xl md:text-8xl xl:text-ateam-xl xl:leading-ateam-xl 2xl:text-ateam-2xl 2xl:leading-ateam-2xl text-center">
            GET THE
            GRADE YOU DESERVE
        </h1>
    </div>

    <div class="col-span-12 lg:col-span-10 lg:col-start-2 grid second-row gap-8">
        <div class="award-pic-wrapper xl:flex items-center relative hidden">
            <img src="/img/award_pic2.png" alt="Award picture" class="award-pic ">

        </div>
        <div class="slogen lg:flex items-center relative xl:-left-5 2xl:-left-15">
            <div class="">
                <img src="/img/award_pic.png" alt="Award picture"
                    class="xl:hidden inline-block relative bottom-10 w-1/3">
                <div class="inline-block w-2/3 md:w-1/2 xl:w-full md:-ml-8 xl:-ml-2 pt-16 lg:pt-0">
                    <p class=" text-md md:text-lg  text-left xl:w-auto ">
                        Never miss the grades you want. Try out a session
                        absolutely FREE. See the difference for
                        yourself</p>

                    <form id="topForm" class="w-full mt-5 hidden lg:block xl:hidden" action="/email/signup"
                        method="POST">
                        @csrf
                        @if ($errors->emailSignup->any())
                        <div class="alert alert-danger">
                            <ul class="text-left">
                                @foreach ($errors->emailSignup->all() as $error)
                                <li class="bg-red-100 text-red-700 mb-4 p-6">{{ $error }}</li>
                                @endforeach
                            </ul>
                        </div>
                        @endif
                        <input name="email" class="w-full lg:w-3/4 lg:-w-100 h-15 border border-gray-200" type="email"
                            placeholder="Your email address">
                        <button class="w-full mt-4 lg:mt-0 lg:w-1/4 btn-cta h-15 hover:bg-ateam-dark-blue "
                            type="submit">SIGN UP</button>
                    </form>
                </div>
                <form class="w-full mt-5 lg:hidden xl:block xl:-ml-2" action="/email/signup" method="POST">
                    @csrf
                    @if ($errors->emailSignup->any())
                    <div class="alert alert-danger">
                        <ul class="text-left">
                            @foreach ($errors->emailSignup->all() as $error)
                            <li class="bg-red-100 text-red-700 mb-4 p-6">{{ $error }}</li>
                            @endforeach
                        </ul>
                    </div>
                    @endif
                    <input name="email" class="w-full lg:w-3/4 lg:-w-100 h-15 border border-gray-200" type="email"
                        placeholder="Your email">
                    <button class="w-full mt-4 lg:mt-0 lg:w-1/4 btn-cta h-15" type="submit">SIGN UP</button>
                </form>
                <div class="w-1/6 hidden xl:hidden lg:inline-flex justify-center  h-full ">
                    <img src="/img/emblem.png" alt="Award emblem" class="w-5/6 inline-block relative top-8 -right-6 ">
                </div>
            </div>
        </div>
        <div class="emblem xl:flex hidden items-center justify-center relative xl:-left-5 2xl:-left-15">
            <img src="/img/emblem.png" alt="Award emblem" class="w-full ">
        </div>
    </div>

</div>

<section class="proof">
    <div class="container mx-auto sm:px-6 lg:px-8 grid grid-cols-12 py-10 lg:py-20 text-center">

        <div class="col-span-12">
            <svg class="fill-current inline-block text-white w-20 lg:w-44" id="Capa_1"
                enable-background="new 0 0 512 512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
                <g id="XMLID_1497_">
                    <g id="XMLID_1687_">
                        <path id="XMLID_898_"
                            d="m278.5 512h-45c-16.542 0-30-13.458-30-30 0-13.953 9.575-25.712 22.5-29.051v-12.446c0-2.845-2.067-5.31-4.916-5.864-23.953-4.655-46.383-13.945-66.667-27.612-2.428-1.638-5.651-1.364-7.665.648l-8.878 8.877c6.192 10.778 5.41 24.664-2.732 34.385-5.414 6.463-13.326 10.381-21.71 10.75-8.383.361-16.604-2.822-22.54-8.757l-31.821-31.82c-5.666-5.666-8.786-13.199-8.786-21.213s3.12-15.548 8.786-21.214c5.667-5.666 13.2-8.786 21.214-8.786 5.449 0 10.677 1.442 15.245 4.147l8.796-8.796c2.013-2.012 2.285-5.236.648-7.665-13.667-20.284-22.957-42.714-27.612-66.666-.554-2.85-3.02-4.917-5.864-4.917h-12.435c-1.358 5.317-4.168 10.166-8.231 14.088-5.912 5.706-13.688 8.671-21.917 8.394-16.214-.578-28.915-13.958-28.915-30.461v-44.521c0-8.203 3.248-15.862 9.146-21.566 5.898-5.702 13.681-8.691 21.874-8.416 13.266.442 24.478 9.947 27.904 22.482h12.573c2.845 0 5.311-2.067 5.864-4.916 4.655-23.953 13.945-46.383 27.612-66.667 1.637-2.429 1.364-5.653-.648-7.665l-8.796-8.796c-4.568 2.705-9.796 4.147-15.245 4.147-8.014 0-15.547-3.12-21.214-8.786-11.697-11.697-11.697-30.73 0-42.428l31.82-31.819c11.697-11.698 30.729-11.696 42.427 0 5.666 5.667 8.786 13.2 8.786 21.214 0 5.448-1.442 10.676-4.147 15.245l8.796 8.796c2.014 2.014 5.236 2.285 7.664.648 20.285-13.667 42.715-22.957 66.667-27.612 2.85-.554 4.917-3.02 4.917-5.864v-12.446c-12.925-3.339-22.5-15.098-22.5-29.051 0-16.542 13.458-30 30-30h45c16.542 0 30 13.458 30 30 0 13.953-9.575 25.712-22.5 29.051v12.446c0 2.845 2.067 5.311 4.916 5.864 23.953 4.655 46.383 13.945 66.667 27.612 2.428 1.637 5.652 1.365 7.665-.648l8.804-8.803c-6.779-11.503-5.234-26.587 4.631-36.452 11.696-11.696 30.729-11.698 42.427 0l31.82 31.819c11.697 11.697 11.697 30.73 0 42.428-5.667 5.666-13.2 8.786-21.214 8.786-5.448 0-10.676-1.442-15.245-4.147l-8.796 8.796c-2.013 2.012-2.285 5.236-.648 7.665 13.667 20.284 22.957 42.714 27.612 66.666.554 2.85 3.02 4.917 5.864 4.917h12.552c3.243-12.001 13.616-21.266 26.248-22.381h.001c8.4-.749 16.763 2.084 22.952 7.751 6.192 5.67 9.744 13.736 9.744 22.13v45c0 8.394-3.552 16.46-9.744 22.13-6.189 5.667-14.562 8.491-22.952 7.751-12.633-1.115-23.006-10.38-26.249-22.381h-12.552c-2.845 0-5.31 2.067-5.864 4.916-4.655 23.953-13.945 46.383-27.612 66.667-1.637 2.429-1.364 5.653.648 7.665l8.796 8.796c4.569-2.705 9.797-4.147 15.245-4.147 8.014 0 15.547 3.12 21.214 8.786 5.666 5.666 8.786 13.2 8.786 21.214s-3.12 15.547-8.787 21.213l-31.819 31.82c-5.936 5.936-14.147 9.128-22.541 8.757-8.384-.369-16.296-4.287-21.71-10.749-8.142-9.722-8.926-23.607-2.732-34.386l-8.878-8.877c-2.013-2.013-5.236-2.286-7.664-.648-20.285 13.667-42.715 22.957-66.667 27.612-2.85.554-4.917 3.02-4.917 5.864v12.446c12.925 3.339 22.5 15.098 22.5 29.051-.001 16.542-13.459 30-30.001 30zm-127.54-126.03c5.072 0 10.179 1.469 14.634 4.471 18.046 12.159 38 20.425 59.306 24.565 12.225 2.375 21.1 13.098 21.1 25.497v18.997c0 6.893-5.607 12.5-12.5 12.5-5.514 0-10 4.486-10 10s4.486 10 10 10h45c5.514 0 10-4.486 10-10s-4.486-10-10-10c-6.893 0-12.5-5.607-12.5-12.5v-18.997c0-12.398 8.875-23.122 21.102-25.497 21.305-4.141 41.259-12.406 59.306-24.565 10.347-6.972 24.219-5.673 32.983 3.092l13.755 13.755c4.697 4.697 4.697 12.341 0 17.038-3.811 3.811-4.23 9.858-.955 13.77 1.847 2.203 4.425 3.486 7.259 3.611 2.853.118 5.511-.911 7.519-2.919l31.819-31.82c1.89-1.889 2.929-4.399 2.929-7.07 0-2.672-1.04-5.183-2.929-7.071-3.899-3.899-10.244-3.897-14.142 0l-.32.32c-4.696 4.697-12.34 4.698-17.038 0l-13.755-13.755c-8.764-8.764-10.064-22.636-3.092-32.983 12.159-18.047 20.425-38.001 24.565-59.307 2.375-12.227 13.098-21.102 25.497-21.102h19.448c6.643 0 12.049 5.405 12.049 12.049 0 5.389 3.98 9.961 9.062 10.41 2.862.25 5.595-.664 7.686-2.58 2.097-1.919 3.251-4.54 3.251-7.379v-45c0-2.839-1.154-5.46-3.251-7.379-2.093-1.918-4.837-2.835-7.686-2.58-5.082.449-9.062 5.021-9.062 10.41 0 6.643-5.405 12.049-12.049 12.049h-19.448c-12.398 0-23.122-8.875-25.497-21.102-4.141-21.305-12.406-41.259-24.565-59.306-6.973-10.348-5.672-24.22 3.092-32.983l13.435-13.435c4.875-4.874 12.804-4.873 17.679 0 3.898 3.898 10.243 3.9 14.142 0 3.899-3.899 3.899-10.243 0-14.143l-31.82-31.819c-3.896-3.897-10.241-3.901-14.142 0-3.899 3.898-3.899 10.243 0 14.142 4.874 4.874 4.874 12.805 0 17.679l-13.435 13.435c-8.765 8.764-22.636 10.064-32.984 3.092-18.046-12.159-38-20.425-59.306-24.565-12.227-2.376-21.102-13.099-21.102-25.498v-18.997c0-6.893 5.607-12.5 12.5-12.5 5.514 0 10-4.486 10-10s-4.486-10-10-10h-45c-5.514 0-10 4.486-10 10s4.486 10 10 10c6.893 0 12.5 5.607 12.5 12.5v18.997c0 12.398-8.875 23.122-21.102 25.497-21.305 4.141-41.259 12.406-59.306 24.565-10.347 6.972-24.219 5.673-32.983-3.092l-13.435-13.435c-2.36-2.361-3.661-5.5-3.661-8.839 0-3.341 1.302-6.481 3.665-8.842 3.896-3.896 3.896-10.241-.004-14.14-3.899-3.901-10.244-3.899-14.142 0l-31.82 31.819c-3.899 3.899-3.899 10.243 0 14.143 1.889 1.889 4.4 2.929 7.071 2.929s5.182-1.039 7.07-2.928c4.873-4.875 12.804-4.874 17.679-.001l13.435 13.435c8.764 8.764 10.064 22.636 3.092 32.983-12.159 18.047-20.425 38.001-24.565 59.307-2.375 12.227-13.098 21.102-25.497 21.102h-19.521c-6.604 0-11.976-5.372-11.976-11.976 0-5.622-4.328-10.341-9.647-10.518-2.737-.101-5.339.902-7.303 2.805-1.967 1.901-3.05 4.455-3.05 7.189v44.521c0 5.586 4.318 10.284 9.626 10.473 2.755.101 5.347-.895 7.316-2.796 1.972-1.903 3.058-4.46 3.058-7.198 0-6.893 5.607-12.5 12.5-12.5h18.997c12.398 0 23.122 8.875 25.497 21.102 4.141 21.305 12.406 41.259 24.565 59.306 6.973 10.348 5.672 24.22-3.092 32.983l-13.755 13.755c-4.697 4.698-12.341 4.697-17.038 0l-.32-.32c-1.889-1.89-4.399-2.929-7.07-2.929s-5.183 1.04-7.071 2.929c-1.889 1.889-2.929 4.399-2.929 7.071 0 2.671 1.039 5.182 2.928 7.07l31.821 31.82c2.008 2.007 4.684 3.045 7.518 2.919 2.834-.125 5.412-1.408 7.259-3.612 3.275-3.91 2.856-9.958-.954-13.769-4.698-4.697-4.698-12.341-.001-17.038l13.755-13.755c4.991-4.991 11.64-7.562 18.35-7.562z" />
                    </g>
                    <g id="XMLID_1654_">
                        <path id="XMLID_895_"
                            d="m217.374 213.878c-23.159 0-42-18.841-42-42s18.841-42 42-42 42 18.841 42 42-18.841 42-42 42zm0-64c-12.131 0-22 9.869-22 22s9.869 22 22 22 22-9.869 22-22-9.869-22-22-22z" />
                    </g>
                    <g id="XMLID_1656_">
                        <path id="XMLID_892_"
                            d="m189 355.805c-20.034 0-36.333-16.299-36.333-36.333s16.299-36.334 36.333-36.334 36.333 16.3 36.333 36.334-16.299 36.333-36.333 36.333zm0-52.667c-9.006 0-16.333 7.327-16.333 16.334 0 9.006 7.327 16.333 16.333 16.333s16.333-7.327 16.333-16.333c0-9.007-7.327-16.334-16.333-16.334z" />
                    </g>
                    <g id="XMLID_1104_">
                        <path id="XMLID_891_"
                            d="m325.833 345.855c-31.34 0-57.71-23.445-61.339-54.535-.641-5.485 3.288-10.451 8.773-11.092 5.487-.636 10.451 3.287 11.092 8.774 2.452 21.01 20.282 36.853 41.474 36.853 23.025 0 41.759-18.733 41.759-41.759 0-21.326-15.956-39.17-37.115-41.505-5.489-.605-9.449-5.547-8.843-11.036.606-5.49 5.553-9.438 11.036-8.843 31.311 3.455 54.922 29.845 54.922 61.384 0 34.054-27.705 61.759-61.759 61.759z" />
                    </g>
                    <g id="XMLID_1101_">
                        <path id="XMLID_890_"
                            d="m313 181.88c-2.63 0-5.21-1.07-7.07-2.93s-2.93-4.44-2.93-7.07c0-2.64 1.069-5.21 2.93-7.07 1.86-1.859 4.44-2.93 7.07-2.93s5.21 1.07 7.069 2.93c1.86 1.86 2.931 4.44 2.931 7.07s-1.07 5.21-2.931 7.07c-1.859 1.86-4.439 2.93-7.069 2.93z" />
                    </g>
                    <g id="XMLID_1094_">
                        <path id="XMLID_889_"
                            d="m256 385c-2.63 0-5.21-1.07-7.07-2.931-1.86-1.859-2.93-4.439-2.93-7.069s1.069-5.21 2.93-7.07c1.86-1.86 4.43-2.93 7.07-2.93 2.63 0 5.21 1.069 7.069 2.93 1.86 1.86 2.931 4.44 2.931 7.07s-1.07 5.21-2.931 7.069c-1.859 1.861-4.439 2.931-7.069 2.931z" />
                    </g>
                    <g id="XMLID_1660_">
                        <path id="XMLID_888_"
                            d="m143.67 266.13c-2.64 0-5.21-1.07-7.07-2.93-1.87-1.86-2.93-4.44-2.93-7.07 0-2.64 1.06-5.21 2.93-7.07 1.851-1.87 4.431-2.93 7.07-2.93 2.63 0 5.21 1.06 7.07 2.93 1.859 1.86 2.93 4.44 2.93 7.07s-1.07 5.2-2.93 7.07c-1.86 1.86-4.44 2.93-7.07 2.93z" />
                    </g>
                    <g id="XMLID_1493_">
                        <path id="XMLID_887_"
                            d="m289.12 257.62c-2.63 0-5.21-1.07-7.07-2.931-1.86-1.859-2.93-4.439-2.93-7.069 0-2.641 1.069-5.21 2.93-7.08 1.86-1.86 4.44-2.92 7.07-2.92s5.21 1.06 7.069 2.92c1.86 1.87 2.931 4.44 2.931 7.08 0 2.63-1.07 5.199-2.931 7.069-1.859 1.861-4.439 2.931-7.069 2.931z" />
                    </g>
                </g>
            </svg>
            <h2 class="text-5xl lg:text-7xl font-heading  font-black mt-8">COVID & LOCKDOWN PROOF</h2>
        </div>
        <div class="col-span-12 lg:col-span-10 lg:col-start-2 xl:col-span-8 xl:col-start-3 mt-8">
            <p class="text-xl lg:text-body-2xl leading-7 lg:leading-9 ">During the height of the pandemic in
                <b>2020/21</b> our
                students
                went onto achieve <b>121
                    A*’s</b> & <b>96 A’s</b> at
                A-Level
                & <b>33 Grade 9’s</b> at GCSE’s.</p>
            <p class="text-xl lg:text-body-2xl leading-7 lg:leading-9  mt-8"><b>56</b> of our students went
                onto
                study Medicine &
                Dentistry
                courses in the UK & <b>4</b> accepting offers
                from
                Oxbridge universities</p>
        </div>

    </div>
</section>

<section class="team">
    <div class="container mx-auto sm:px-6 lg:px-8 grid grid-cols-12 py-10 lg:py-20 text-center">
        <div class="col-span-12 lg:col-span-10 lg:col-start-2">
            <h2 class="text-5xl lg:text-7xl xl:text-8xl 2xl:text-9xl font-heading  font-black mt-8 fade-in">AWARD
                WINNING GCSE &
                A-LEVEL
                SPECIALISTS</h2>
        </div>


        <div class="col-span-12 lg:col-span-8 lg:col-start-3 grid grid-cols-3 gap-6 z-10 mt-10 lg:mt-32">
            <div class="flex items-center"><img src="/img/tutors/tutor3.jpg" alt="Tutor one"
                    class="slide-in from-left w-full object-cover"></div>
            <div>
                <img class="" src="/img/tutors/tutor1.jpg" alt="Tutor two">
                <img class="mt-8" src="/img/tutors/tutor2.jpg" alt="Tutor three">
            </div>
            <div class="flex items-center"><img class=" slide-in from-right" src="/img/tutors/tutor4.jpg"
                    alt="Tutor four"></div>
        </div>

        <div class="col-span-12 lg:col-span-10 lg:col-start-2 relative -top-48 xl:-top-64 lg:-top-40">
            <hr class="fade-in border border-ateam-red" />
            <hr class="fade-in mt-10 border border-ateam-blue " />
        </div>
    </div>
</section>

<section class="how-it-works text-center my-16 lg:my-40">
    <div class="container mx-auto">
        <div class="text-center lg:text-2xl font-light">How the A-Team Tutoring Programme works?</div>

        <iframe class="mt-20 inline-block w-full lg:w-1/2 h-96" src="https://www.youtube.com/embed/t_ddi-XP03I"
            title="YouTube video player" frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen></iframe>

        <div class="steps grid grid-cols-12 mt-20 lg:mt-80">
            <div class="col-span-2 col-start-6">
                <span class="text-ateam-2xl font-heading font-bold">1</span>
            </div>
            <div class="col-span-12 lg:col-span-3 lg:col-start-9 flex items-center">
                <p class="text-md  w-full  text-left border-t border-ateam-blue py-4">
                    Following signup – you
                    will be
                    assigned to a
                    subject specialist & attend weekly
                    scheduled
                    classes right from the comfort of your home</p>
            </div>
            <div class="col-span-12 lg:col-span-10 lg:col-start-2 mt-4 lg:mt-20">
                <img class="step-image w-full shadow-lg" src="/img/step1.jpg" alt="Step 1">
            </div>
        </div>

        <div class="steps grid grid-cols-12 mt-4 lg:mt-40">
            <div class="col-span-12 lg:col-span-3 lg:col-start-2 flex items-center order-2 lg:order-1">
                <p class="text-md  w-full  text-left border-t border-ateam-blue py-4">
                    Every 6 weeks you will undertake mock assessments allowing you to keep a track of your own progress
                </p>
            </div>
            <div class="col-span-2 col-start-6 order-1 lg:order-2">
                <span class="text-ateam-2xl font-heading font-bold">2</span>
            </div>
            <div class="col-span-12 lg:col-span-10 lg:col-start-2 mt-4 lg:mt-20 order-3">
                <img class="step-image w-full shadow-lg" src="/img/step2.jpg" alt="Step 2">
            </div>
        </div>

        <div class="steps grid grid-cols-12 mt-4 lg:mt-40">
            <div class="col-span-2 col-start-6">
                <span class="text-ateam-2xl font-heading font-bold">3</span>
            </div>
            <div class="col-span-12 lg:col-span-3 lg:col-start-9 flex items-center">
                <p class="text-md  w-full  text-left border-t border-ateam-blue py-4">
                    You will have the guidance & mentorship to help support you in achieving your best - every step
                    along the way</p>
            </div>
            <div class="col-span-12 lg:col-span-10 lg:col-start-2 mt-4 lg:mt-20">
                <img class="step-image  w-full shadow-lg" src="/img/step3.jpg" alt="Step 3">
            </div>
        </div>

        <div>
            <a href="#signUpForm"
                class="hover:bg-ateam-dark-blue btn inline-block tracking-wider font-medium bg-ateam-red text-white w-full lg:w-auto py-6 lg:px-20 mt-24 lg:mt-54">GET
                STARTED</a>
        </div>
    </div>
</section>

<section class="why relative py-16 lg:py-44 px-10 lg:px-0">

    <div class="grid grid-cols-12">
        <div class="col-span-12">
            <h3 class="text-center lg:text-2xl font-bold">Why A-Team?</h3>
        </div>
        <div class="col-span-12 lg:col-span-5 lg:col-start-2 flex items-center my-16 lg:my-36">
            <div>
                <h2 class="font-heading text-5xl lg:text-6xl leading-tight lg:leading-normal font-black">GETTING YOU TO
                    THE
                    RIGHT PLACE</h2>
                <p class="text-xl lg:text-2xl font-light mt-7 leading-relaxed lg:leading-relaxed">Fact: Our
                    teaching has <span class="font-bold">proven</span> to get students the
                    grades they require to
                    move <span class="font-bold">further</span>. Our tutors will treat you as individual, <span
                        class="font-bold">supporting</span> you along & getting you to where you need to be.
                </p>
                <a target="_blank" href="{{ url('/plans') }}"
                    class="hover:underline text-xl lg:text-2xl inline-flex items-center mt-8 lg:mt-12 tracking-wider font-bold">SEE
                    OUR PLAN
                    <img class="inline-block w-6 h-6 ml-2 lg:ml-4" src="/img/icons/right_arrow.svg" /></a>
            </div>
        </div>
    </div>
</section>

<section>
    <div class="container mx-auto grid grid-cols-12 py-16 lg:py-44">
        <div class="col-span-12 lg:col-span-4">
            <h4 class="font-heading font-black text-4xl lg:text-6xl">HALF THE COST</h4>
        </div>
        <div class="col-span-12 lg:col-span-7 lg:col-start-6">
            <p class="text-ateam-gray text-xl lg:text-2xl font-light leading-relaxed lg:leading-relaxed mt-8 lg:mt-0">
                Good news - You don't have to break the bank to access a high calibre tutoring programme. We've made
                that easy for you to meet the best talented tutors right from the comfort of your own home.</p>

        </div>

        <div class="col-span-12 mt-40">
            <table class="table-auto w-full lg:text-xl  price-table text-ateam-gray">
                <thead>
                    <tr>
                        <th class="text-left w-4/12 text-ateam-black">PLAN</th>
                        <th class="text-center font-normal w-4/12">Traditional Tutoring</th>
                        <th class="text-ateam-blue text-center font-normal w-4/12">
                            <img class="mx-auto my-2 lg:my-0 lg:inline-block lg:mr-4" src="/img/icons/logo.svg" />
                            A-Team Academy
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="font-medium">
                        <td class="text-left">A-Level</td>
                        <td class="text-center">£195 per month</td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue">
                            <img src="/img/icons/checked.svg"
                                class="mx-auto w-8 h-8 lg:w-6 lg:h-6 lg:inline-block lg:mr-4 my-2 lg:my-0" />
                            £125.00
                            per month</td>
                    </tr>
                    <tr class="font-medium">
                        <td class="text-left">GCSE</td>
                        <td class="text-center">£125 per month</td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue">
                            <img src="/img/icons/checked.svg"
                                class="mx-auto w-8 h-8  lg:w-6 lg:h-6 lg:inline-block lg:mr-4 my-2 lg:my-0" />
                            £100.00
                            per month</td>
                    </tr>

                </tbody>
            </table>


            <table class="table-auto w-full lg:text-xl  price-table text-ateam-gray mt-32">
                <thead>
                    <tr>
                        <th class="text-left w-4/12 text-ateam-black">WHAT YOU GET</th>
                        <th class="text-center font-normal w-4/12"></th>
                        <th class="text-ateam-blue text-center font-normal w-4/12">
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="font-medium">
                        <td class="text-left">Weekly structured lessons</td>
                        <td class="text-center"><img src="/img/icons/checked_gray.svg" class="w-10 h-10 inline-block" />
                        </td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue"><img src="/img/icons/checked.svg"
                                class="w-10 h-10 inline-block" /> </td>
                    </tr>
                    <tr class="font-medium">
                        <td class="text-left">Mock exams (exam board specific)</td>
                        <td class="text-center"><img src="/img/icons/checked_gray.svg" class="w-10 h-10 inline-block" />
                        </td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue"><img src="/img/icons/checked.svg"
                                class="w-10 h-10 inline-block " /></td>
                    </tr>


                    <tr class="font-medium">
                        <td class="text-left">Subject specialist tutors</td>
                        <td class="text-center"><img src="/img/icons/checked_gray.svg" class="w-10 h-10 inline-block" />
                        </td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue"><img src="/img/icons/checked.svg"
                                class="w-10 h-10 inline-block " /></td>
                    </tr>
                    <tr class="font-medium">
                        <td class="text-left">Comprehensive feedback</td>
                        <td class="text-center"><img src="/img/icons/checked_gray.svg" class="w-10 h-10 inline-block" />
                        </td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue"><img src="/img/icons/checked.svg"
                                class="w-10 h-10 inline-block " /></td>
                    </tr>
                    <tr class="font-medium">
                        <td class="text-left">Ability to access notes / recorded lessons </td>
                        <td class="text-center"><img src="/img/icons/cancel.svg" class="w-10 h-10 inline-block" /></td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue"><img src="/img/icons/checked.svg"
                                class="w-10 h-10 inline-block " /></td>
                    </tr>
                    <tr class="font-medium">
                        <td class="text-left">Opportunity to participate & ask questions relevant to you</td>
                        <td class="text-center"><img src="/img/icons/cancel.svg" class="w-10 h-10 inline-block" /></td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue"><img src="/img/icons/checked.svg"
                                class="w-10 h-10 inline-block " /></td>
                    </tr>
                    <tr class="font-medium">
                        <td class="text-left">Work alongside like-minded students & a buzzing community</td>
                        <td class="text-center"><img src="/img/icons/cancel.svg" class="w-10 h-10 inline-block" /></td>
                        <td class="text-center bg-ateam-blue-100 text-ateam-blue"><img src="/img/icons/checked.svg"
                                class="w-10 h-10 inline-block " /></td>
                    </tr>

                </tbody>
            </table>
        </div>

        <div class="col-span-12 lg:col-span-6 lg:col-start-4 text-center mt-10 lg:mt-24 ">
            <p class="texl-lg lg:text-2xl text-ateam-gray font-light  leadin leading-7 lg:leading-relaxed">
                GET THE
                GRADES YOU WANT
                WITH HALF THE
                EFFORT.
                <a href="#signUpForm" class="underline hover:text-ateam-black">SIGN UP</a> today for our free lesson.
            </p>
        </div>
    </div>
</section>

<section class="action  px-1  lg:px-0 py-16 lg:py-44">
    <div class="container mx-auto grid grid-cols-12 ">
        <div class="col-span-12 text-center mb-16">
            <h2
                class="fade-in action-heading font-heading font-black text-6xl xl:text-ateam-action-xl 2xl:text-ateam-action-2xl xl:leading-ateam-action-xl 2xl:leading-ateam-action-2xl">
                TIME TO TAKE ACTION</h2>
        </div>
        <div class="col-span-12 lg:col-span-6 relative ">
            <img class="mt-8 lg:mt-0 img-app relative lg:absolute right-20 lg:right-8" src="/img/app.png"
                alt="Ateam's mobile app">
        </div>
        <div class="col-span-12 lg:col-span-6">

            <div>
                <ul class="text-ateam-gray leading-normal text-xl xl:text-2xl">
                    <li><span class="text-ateam-blue font-medium">Online –</span> even though you’re online
                        you’ll
                        have direct
                        access to experienced subject
                        specialised tutors</li>
                    <li><span class="text-ateam-blue font-medium">Exam board specific –</span> tailored lessons
                        to
                        match up to
                        your specification</li>
                    <li><span class="text-ateam-blue font-medium">Access</span> your notes and previous lessons
                        all
                        from one
                        place</li>
                    <li><span class="text-ateam-blue font-medium">Track</span> your progress throughout the
                        programme</li>
                    <li><span class="text-ateam-blue font-medium">Community –</span> be part of the most vibrant
                        online student
                        community</li>
                </ul>

                <div class="block lg:flex items-center w-full lg:mt-15">
                    <div class="text-ateam-gray">
                        <p class="mb-4 text-lg">Start at:</p>
                        <p><span class="font-heading text-ateam-blue text-7xl lg:text-7xl font-bold">£100</span><span
                                class="text-ateam-black ml-2 text-lg">/month</span>
                        </p>
                        <p class="text-lg">*dependent on subject</p>
                    </div>
                    <div class="w-full lg:ml-8">
                        <a href="#signUpForm"
                            class="hover:bg-ateam-dark-blue text-center  block  tracking-wider font-medium bg-ateam-red text-white w-full lg:w-auto py-6  mt-8 lg:mt-0">GET
                            STARTED</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>


<section class="testimonial  px-1 lg:px-0 py-16 lg:py-44 ">
    <div class="container mx-auto grid grid-cols-12 lg:gap-8">
        <div class="col-span-12 lg:col-span-4 flex items-center">
            <div>
                <img src="/img/icons/speaker.svg" alt="Speaker" class="mb-8">
                <p class="font-heading font-black text-4xl lg:text-6xl">What our students say about us</p>
                <a href="#signUpForm"
                    class="hover:bg-ateam-dark-blue mb-8 lg:mb-0 text-center block  tracking-wider font-medium bg-ateam-red text-white w-full lg:w-auto py-6  mt-8 lg:mt-12">FREE
                    TRIAL</a>
            </div>
        </div>
        <div class="col-span-12 lg:col-span-8 flex items-center">
            <iframe class="inline-block w-full h-96 xl:h-128 2xl:h-144 " src="https://www.youtube.com/embed/-WSjHuQdYJ8"
                title="YouTube video player" frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen></iframe>
        </div>
    </div>
</section>

<section class="sign-up-form py-16 lg:py-28" id="signUpForm">
    <div class="container mx-auto grid grid-cols-12 ">
        <div class="col-span-12">
            <h2 class="font-heading font-black text-2xl lg:text-6xl text-center mb-8 fade-in">PLACES GOING FAST</h2>
        </div>
        <div class="col-span-12 md:col-span-8 md:col-start-3 lg:col-span-6 lg:col-start-4 xl:col-span-4 xl:col-start-5">
            <p class="text-center">*Discounts are available for multiple subjects</p>

            @if ($errors->any())
            <div class="bg-red-100  mt-4 mb-4 p-6">
                <ul class="text-left">
                    @foreach ($errors->all() as $error)
                    <li class="text-red-700">{{ $error }}</li>
                    @endforeach
                </ul>
            </div>
            @endif
            <sign-up-form></sign-up-form>
        </div>
    </div>
</section>

@endsection