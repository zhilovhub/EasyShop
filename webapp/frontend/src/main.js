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
app.use(Swiper, SwiperSlide, Navigation)
app.use(router)
app.use(Vuex)
app.use(Store)
app.mount('#app')





