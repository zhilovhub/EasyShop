export let tg = window.Telegram.WebApp;

import "@SwiperBundleCss"; //import css
import { Swiper, SwiperSlide } from "@SwiperVue"; //import component
import SwiperCore, { Pagination, Scrollbar, Navigation } from "@Swiper"; //import swiper core and plugins
SwiperCore.use([Pagination, Scrollbar, Navigation]); //declare two plugins

document.documentElement.style.setProperty('--app-background-color', tg.bgColor);
document.documentElement.style.setProperty('--app-text-color', tg.textColor);

// if (tg.colorScheme === 'dark') {
//     document.body.setAttribute('data-theme', 'dark');
// } else {
//     document.body.setAttribute('data-theme', 'light');
//
// }

tg.expand();

import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router/router.js'
import Vuex from "vuex";
import {Store} from "./store/store.js"


Store.state.bot_id = new URL(window.location.href).searchParams.get('bot_id');

const app = createApp(App)
// eslint-disable-next-line vue/multi-word-component-names

app.component("swiper", Swiper)
app.component("swiper-slide", SwiperSlide)
app.use(router.router)
app.use(Vuex)
app.use(Store)
app.mount('#app')





