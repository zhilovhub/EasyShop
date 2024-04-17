let tg = window.Telegram.WebApp;
import 'swiper/swiper.min.css'
tg.expand();

import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router/router.js'
import Vuex from "vuex";
import {Store} from "./store/store.js"

const app = createApp(App)
app.use(router)
app.use(Vuex)
app.use(Store)
app.mount('#app')





