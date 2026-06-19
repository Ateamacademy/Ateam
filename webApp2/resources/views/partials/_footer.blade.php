<footer class="bg-ateam-dark-blue text-white">
    <div class="grid grid-cols-12 container mx-auto py-10 lg:py-20 text-md lg:text-xl">
        <div class="col-span-12 mb-4 lg:mb-12">
            <img class="h-10 lg:h-14" src="/img/logo_white.svg" alt="A-team academy's logo">
        </div>
        <div class="font-bold col-span-12 lg:col-span-4">
            <p class="mt-4 lg:mt-0"><a href="https://ateamacademy.co.uk/about-us/">About us</a></p>
            <p class="mt-4"><a href="mailto:info@ateamacademy.co.uk?subject=ATEAM ENQUIRY">Contact</a></p>
        </div>
        <div class="col-span-12 lg:col-span-4">
            <p class="mt-4 lg:mt-0 font-bold">Social</p>
            <ul class="mt-4">
                <li class="inline-block"><a target="_blank" href="https://www.tiktok.com/@ateamacad"><img
                            src="/img/icons/tiktok.svg" alt="Tiktok social account"></a></li>
                <li class="inline-block ml-7"><a target="_blank" href="https://www.instagram.com/ateamacad"><img
                            src="/img/icons/ig.svg" alt="Instagram social account"></a></li>
                <li class="inline-block ml-7"><a target="_blank"
                        href="https://www.youtube.com/channel/UC3zADP8T2IEiJpqOWcaxHCA"><img
                            src="/img/icons/youtube.svg" alt="Youtube social account"></a>
                </li>
                <li class="inline-block ml-7"><a target="_blank" href="https://www.facebook.com/ateamacad"><img
                            src="/img/icons/facebook.svg" alt="Facebook social account"></a>
                </li>
            </ul>
        </div>
        <div class="col-span-12 lg:col-span-4">
            <p class="font-bold mt-4 lg:mt-0">Stay in the loop</p>
            <form action="/email/signup" method="POST" class="w-full mt-4 border-b border-white">
                @csrf
                <input name="email"
                    class="pl-0 text-md lg:text-xl w-3/5 h-15 focus:ring-white bg-transparent placeholder-gray-400  border-0"
                    type="email" placeholder="Your email">
                <button class="h-15 w-2/5 font-bold  footer-sbmt-btn">SUBMIT</button>
            </form>
        </div>
    </div>

    <div class="text-center py-6 col-span-12 copyright">&copy; A-Team Academy 2021</div>
</footer>
</div>
</body>

</html>