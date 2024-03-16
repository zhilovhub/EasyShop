import { createRouter, createWebHistory } from 'vue-router'


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/products-page',
      name: 'products-page',
      component: () => import('@/components/products/productsPage.vue')
    },
    {
      path: `/products-page/shopping-cart`,
      name: 'shopping-cart',
      component: () => import ('@/components/products/shoppingСart.vue')
    },
    {
      path: `/products-page/order-details`,
      name: 'order-details',
      component: () => import('@/components/products/orderDetails.vue')
    },
    {
      path: '/services/choose-branch',
      name: 'choosing-branch',
      component: () => import('@/components/services/choosingBranch.vue')
    },
    {
      path: '/services/choose-speciality',
      name: 'choosing-speciality',
      component: () => import('@/components/services/choosingSpeciality.vue')
    },
    {
      path: '/services/choose-employee',
      name: 'choosing-employee',
      component: () => import('@/components/services/chooseEmployee.vue')
    },
    {
      path: '/services/choose-service',
      name: 'choosing-service',
      component: () => import('@/components/services/choosingTypeOfService.vue')
    }
  ]
});
export default router
