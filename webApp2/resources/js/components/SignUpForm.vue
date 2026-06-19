<template>
    <form action="/landing/signup" method="POST" class="w-full">
        <input :value="csrfToken" type="hidden" name="_token" />
        <input
            type="text"
            class="w-full mt-6 border-gray-300 shadow-sm"
            placeholder="Name*"
            name="name"
            v-model="name"
        />
        <input
            type="email"
            class="w-full mt-6 border-gray-300 shadow-sm"
            placeholder="Email*"
            name="email"
            v-model="email"
        />

        <div class="mt-6 relative">
            <input type="hidden" name="option" id="option" v-model="option" />
            <select-menu
                menu="GCSE or A-level"
                :data="options"
                v-on:selected="updateOption($event)"
            ></select-menu>
        </div>

        <div :class="!option ? 'noClick-wrapper' : ''" class="mt-6 relative">
            <input
                type="hidden"
                name="subject"
                id="subject"
                v-model="subject"
            />
            <select-menu
                menu="Please select a Course first"
                :class="!option ? 'noClick' : ''"
                :data="shownSubjects"
                v-on:selected="updateSubject($event)"
            ></select-menu>
        </div>

        <textarea
            placeholder="Additional information…"
            name="message"
            id=""
            cols="30"
            rows="10"
            class="w-full mt-6 border-gray-300 shadow-sm"
            v-model="message"
        ></textarea>
        <button
            name="signup-btn"
            class="hover:bg-ateam-dark-blue tracking-wider font-medium bg-ateam-red text-white w-full py-6 mt-6 shadow-sm"
        >
            SUBMIT
        </button>
    </form>
</template>

<script>
import { ref, watch, computed } from "vue";
import { useStore } from "vuex";

const options = [
    { id: 1, name: "GCSE" },
    { id: 2, name: "A-level" }
];

const gcse_subjects = [
    {
        id: 1,
        name: "Maths"
    },
    {
        id: 2,
        name: "English Language"
    },
    {
        id: 3,
        name: "English Literature"
    },
    {
        id: 4,
        name: "Science (Double Award)"
    },
    {
        id: 5,
        name: "Biology"
    },
    {
        id: 6,
        name: "Chemistry"
    },
    {
        id: 7,
        name: "Physics"
    }
];

const alevel_subjects = [
    {
        id: 1,
        name: "Biology"
    },
    {
        id: 2,
        name: "Chemistry"
    },
    {
        id: 3,
        name: "Physics"
    },
    {
        id: 4,
        name: "Maths"
    },
    {
        id: 5,
        name: "Further Maths"
    },
    {
        id: 6,
        name: "Psychology"
    },
    {
        id: 7,
        name: "Sociology"
    },
    {
        id: 8,
        name: "Economics"
    },
    {
        id: 9,
        name: "Business Studies"
    },
    {
        id: 10,
        name: "English Literature"
    },
    {
        id: 11,
        name: "Religious Studies"
    },
    {
        id: 12,
        name: "History"
    },
    {
        id: 13,
        name: "Geography"
    }
];

export default {
    setup() {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')
            .content;

        const name = ref();
        const email = ref();
        const message = ref();
        const option = ref("");
        const subject = ref();
        const store = useStore();

        const updateOption = r => {
            option.value = r.name;
        };

        const updateSubject = r => {
            subject.value = r.name;
        };

        const shownSubjects = computed(() => {
            // if (option.value.length > 0) {
            return option.value == "GCSE" ? gcse_subjects : alevel_subjects;
            // }
        });

        return {
            name,
            email,
            message,
            option,
            subject,
            options,
            gcse_subjects,
            updateOption,
            updateSubject,
            csrfToken,
            alevel_subjects,
            shownSubjects
        };
    }
};
</script>

<style lang="scss">
.noClick {
    pointer-events: none;
    button {
        background-color: #d6cfcf;
        color: #7b7b7b;
    }
}

.noClick-wrapper {
    cursor: not-allowed;
}
</style>
