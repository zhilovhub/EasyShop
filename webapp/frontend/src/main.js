let tg = window.Telegram.WebApp;
import "@SwiperBundleCss"; //import css
import { Swiper, SwiperSlide } from "@SwiperVue"; //import component
import SwiperCore, { Pagination, Scrollbar, Navigation } from "swiper"; //import swiper core and plugins
SwiperCore.use([Pagination, Scrollbar, Navigation]); //declare two plugins
tg.expand();

import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router/router.js'
import Vuex from "vuex";
import {Store} from "./store/store.js"

const app = createApp(App)
// eslint-disable-next-line vue/multi-word-component-names
app.component("swiper", Swiper)
app.component("swiper-slide", SwiperSlide)
app.use(router)
app.use(Vuex)
app.use(Store)
app.mount('#app')





