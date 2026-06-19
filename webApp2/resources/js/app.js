require('./bootstrap');
require('alpinejs');

import { createApp } from 'vue'
import { createStore } from 'vuex'
import createPersistedState from "vuex-persistedstate";

const app = createApp({});

const store = createStore({
    state: {
        course_option:[],
        course_subjects:[]
    },
    getters:{
       
    },
    mutations:{
        updateCourseOption(state, option){
            state.course_option = option;
        },
    },
    actions:{
       
    },
    // plugins: [createPersistedState()]
})


app.component('logo', require('./components/Logo.vue').default);
app.component('select-menu', require('./components/SelectMenu.vue').default);
app.component('sign-up-form', require('./components/SignUpForm.vue').default);
app.use(store)
app.mount('#app')
