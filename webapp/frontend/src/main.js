export let tg = window.Telegram.WebApp;

import "@SwiperBundleCss"; //import css
import { Swiper, SwiperSlide } from "@SwiperVue"; //import component
import SwiperCore, { Pagination, Scrollbar, Navigation } from "@Swiper"; //import swiper core and plugins
SwiperCore.use([Pagination, Scrollbar, Navigation]); //declare two plugins


if (tg.colorScheme === 'dark') {
    document.body.setAttribute('data-theme', 'dark');
} else {
    document.body.setAttribute('data-theme', 'light');

}tg.expand();

import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router/router.js'
import Vuex from "vuex";
import {Store} from "./store/store.js"


Store.state.bot_id = new URL(window.location.href).searchParams.get('bot_id');

async function getWebAppOptions() {
    try {
        console.log(Store.state.bot_id);
        const response = await fetch(`${Store.state.api_url}/api/settings/get_web_app_options/${Store.state.bot_id}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'authorization-data': 'DEBUG',
            },
        });
        console.log(response);
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
    }
}
getWebAppOptions();

const app = createApp(App)
// eslint-disable-next-line vue/multi-word-component-names

app.component("swiper", Swiper)
app.component("swiper-slide", SwiperSlide)
app.use(router.router)
app.use(Vuex)
app.use(Store)
app.mount('#app')





