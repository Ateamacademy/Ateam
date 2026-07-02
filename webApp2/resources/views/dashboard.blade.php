<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-gray-800 leading-tight">
            {{ __('Dashboard') }}
        </h2>
    </x-slot>


    <div class="py-12">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            <div class="mb-5">{{ $visitors->links() }}</div>
            <div class="bg-white overflow-hidden shadow-sm sm:rounded-lg">
                <div class="p-6 bg-white border-b border-gray-200">

                    @if (count($visitors) > 0)

                    <table class="table-auto w-full  price-table ">
                        <thead>
                            <tr class="border-b border-gray-200 text-ateam-black ">
                                <th class="text-left py-4 ">Name</th>
                                <th class="text-center py-4 ">Email</th>
                                <th class=" text-center py-4  ">
                                    Option</th>
                                <th class=" text-center py-4 ">
                                    Subject</th>
                                <th class=" text-center py-4 ">
                                    Signed up at</th>
                                <th class="hidden xl:table-cell text-left py-4 pl-4  w-1/2 lg:w-1/4">
                                    Message</th>
                            </tr>
                        </thead>
                        <tbody>
                            @foreach ( $visitors as $visitor)
                            <tr class="border-b border-gray-200 hover:bg-gray-100">
                                <td class="text-left  py-4">
                                    @if ( $visitor['name'])
                                    {{  $visitor['name'] }}
                                    @else
                                    <i class="text-ateam-gray">Email signup</i>
                                    @endif

                                </td>
                                <td class="text-center  py-4">{{ $visitor['email'] }}</td>
                                <td class="text-center  py-4">{{ $visitor['option'] }}</td>
                                <td class="text-center  py-4">{{ $visitor['subject'] }}</td>
                                <td class="text-center  py-4">
                                    {{-- Convert the stored UTC timestamp to London time (the old code
                                         re-labelled UTC as London, showing times 1h off during BST). --}}
                                    {{ $visitor['created_at']->copy()->timezone('Europe/London')->format('d M Y H:i:s') }}
                                </td>
                                <td style="word-break: break-word;"
                                    class="hidden xl:table-cell pl-4 text-left  text-xs py-8">
                                    {{ $visitor['message'] }}
                                </td>
                            </tr>
                            @endforeach
                        </tbody>
                    </table>
                    @endif


                </div>
            </div>
            <div class="mt-5">{{ $visitors->links() }}</div>
        </div>
    </div>
</x-app-layout>