export let tg = window.Telegram.WebApp;

import "@SwiperBundleCss"; //import css
import { Swiper, SwiperSlide } from "@SwiperVue"; //import component
import SwiperCore, { Pagination, Scrollbar, Navigation } from "@Swiper"; //import swiper core and plugins
SwiperCore.use([Pagination, Scrollbar, Navigation]); //declare two plugins


 if (tg.colorScheme === 'dark') {
     document.body.setAttribute('data-theme', 'dark');
 } else {
     document.body.setAttribute('data-theme', 'light');
 }

tg.expand();

import './assets/main.css'
import { createApp } from 'vue'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import App from './App.vue'
import router from './router/router.js'
import Vuex from "vuex";
import {Store} from "./store/store.js"


const vuetify = createVuetify({
  components,
  directives,
})


Store.state.bot_id = new URL(window.location.href).searchParams.get('bot_id');

const app = createApp(App)
// eslint-disable-next-line vue/multi-word-component-names

app.component("swiper", Swiper)
app.component("swiper-slide", SwiperSlide)
app.use(router.router)
app.use(Vuex)
app.use(Store)
app.use(vuetify)
app.mount('#app')





