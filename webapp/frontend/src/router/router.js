import { createRouter, createWebHistory } from 'vue-router'
import shoppingCart from "@/components/products/shoppingСart.vue";
import orderDetails from '@/components/products/orderDetails.vue'
import choosingBranch from '@/components/services/choosingBranch.vue'
import productsPage from '@/components/products/productsPage.vue'


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/products-page/',
      name: 'productsPage',
      component: productsPage
    },
    {
      path: `/products-page/shopping-cart/`,
      name: 'shopping-cart',
      component: shoppingCart
    },
    {
      path: `/products-page/order-details/`,
      name: 'order-details',
      component: orderDetails
    },
    {
      path: '/services/choose-branch/',
      name: 'order-details',
      component: choosingBranch
    }
  ]
});
export default router
