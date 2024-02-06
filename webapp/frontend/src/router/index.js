import { createRouter, createWebHistory } from 'vue-router'
import shoppingCart from "@/components/shoppingСart.vue";
import mainPage from "@/components/mainPage.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: mainPage
    },
    {
      path: '/shopping-cart',
      name: 'shopping-cart',
      component: shoppingCart
    }
  ]
});
export default router
