import { createRouter, createWebHistory } from 'vue-router'

const PRODUCTS_PAGE = 'products-page'
const PRODUCT_CARD = 'product-card'
const SHOPPING_CART = 'shopping-cart'
const ORDER_DETAILS = 'order-details'
const ADMIN_PANEL = 'admin-panel'
const ADDING_PRODUCT = 'adding-product'
const HEX_SELECTOR = 'hex-selector'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/products-page',
      name: PRODUCTS_PAGE,
      component: () => import('@/components/products/productsPage.vue')
    },
    {
      path: '/products-page/:id',
      name: PRODUCT_CARD,
      component: () => import('@/components/products/productCard.vue')
    },
    {
      path: `/products-page/shopping-cart`,
      name: SHOPPING_CART,
      component: () => import ('@/components/products/shoppingСart.vue')
    },
    {
      path: `/products-page/order-details`,
      name: ORDER_DETAILS,
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
    },
    {
      path: '/landing-page',
      name: 'landing-page',
      component: () => import('@/components/landing/landingPage.vue')
    },
    {
      path: '/admin-panel',
      name: ADMIN_PANEL,
      component: () => import('@/components/admin-panel/adminPanel.vue')
    },
    {
      path: '/hex-selector',
      name: HEX_SELECTOR,
      component: () => import('@/components/hex-selector/hexSelector.vue')
    },
  ]
});
export default { router, PRODUCTS_PAGE, PRODUCT_CARD, SHOPPING_CART, ORDER_DETAILS, ADMIN_PANEL, HEX_SELECTOR}
