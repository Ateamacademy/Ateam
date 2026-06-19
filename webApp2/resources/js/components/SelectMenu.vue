<!-- This example requires Tailwind CSS v2.0+ -->
<template>
    <Listbox as="div" v-model="selected">
        <!-- <ListboxLabel class="block text-sm font-medium text-gray-700">
            Assigned to
        </ListboxLabel> -->
        <div class="mt-1 relative">
            <ListboxButton
                class="relative w-full bg-white border border-gray-300  shadow-sm pl-3 pr-10 py-2 text-left cursor-default focus:outline-none focus:ring-1 focus:ring-ateam-blue focus:border-ateam-blue sm:text-sm"
            >
                <span class="flex items-center">
                    <span class="block truncate">{{ selected.name }}</span>
                </span>
                <span
                    class="ml-3 absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none"
                >
                    <SelectorIcon
                        class="h-5 w-5 text-gray-400"
                        aria-hidden="true"
                    />
                </span>
            </ListboxButton>

            <transition
                leave-active-class="transition ease-in duration-100"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0"
            >
                <ListboxOptions
                    class="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-56  py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm"
                >
                    <ListboxOption
                        as="template"
                        v-for="item in data"
                        :key="item.id"
                        :value="item"
                        v-slot="{ active, selected }"
                    >
                        <li
                            :class="[
                                active
                                    ? 'text-white bg-ateam-blue'
                                    : 'text-gray-900',
                                'cursor-default select-none relative py-2 pl-3 pr-9'
                            ]"
                        >
                            <div class="flex items-center">
                                <span
                                    :class="[
                                        selected
                                            ? 'font-semibold'
                                            : 'font-normal',
                                        'ml-3 block truncate'
                                    ]"
                                >
                                    {{ item.name }}
                                </span>
                            </div>

                            <span
                                v-if="selected"
                                :class="[
                                    active ? 'text-white' : 'text-ateam-blue',
                                    'absolute inset-y-0 right-0 flex items-center pr-4'
                                ]"
                            >
                                <CheckIcon class="h-5 w-5" aria-hidden="true" />
                            </span>
                        </li>
                    </ListboxOption>
                </ListboxOptions>
            </transition>
        </div>
    </Listbox>
</template>

<script>
import { ref, watch } from "vue";
import { useStore } from "vuex";
import {
    Listbox,
    ListboxButton,
    ListboxLabel,
    ListboxOption,
    ListboxOptions
} from "@headlessui/vue";
import { CheckIcon, SelectorIcon } from "@heroicons/vue/solid";

export default {
    components: {
        Listbox,
        ListboxButton,
        ListboxLabel,
        ListboxOption,
        ListboxOptions,
        CheckIcon,
        SelectorIcon
    },
    props: ["data", "menu"],
    setup(props, { emit }) {
        const selected = ref({ id: 0, name: props.menu });
        const store = useStore();

        watch(
            //getter
            () => selected.value,
            //callback
            (newSelected, oldSelected) => {
                emit("selected", newSelected);
            },
            //watch options
            {
                lazy: false
            }
        );

        watch(
            //getter
            () => props.data,
            //callback
            (newSelected, oldSelected) => {
                selected.value = newSelected[0];
            },
            //watch options
            {
                lazy: false
            }
        );

        if (store.state.course_option.length > 0) {
            console.log("Option is selected");
        }

        return {
            selected
        };
    }
};
</script>
