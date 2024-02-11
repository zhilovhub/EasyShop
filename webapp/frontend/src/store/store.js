import Vuex from "vuex";
export const Store = new Vuex.Store({
  state: {
    orderNumber: "",
    itemsAddToCartArray: [],
    items: [
      {
        name: "Название товара",
        price: 1050.09,
        id: 1,
        img: null,
      },
      {
        name: "Название товара",
        price: 5025.40,
        id: 2,
        img: null
      },
      {
        name: "Название товара",
        price: 3200.10,
        id: 3,
        img: null
      },
      {
        name: "Название товара",
        price: 400.10,
        id: 4,
        img: null
      },
      {
        name: "Название товара",
        price: 15000.77,
        id: 1,
        img: null
      },
      {
        name: "Название товара",
        price: 2000.10,
        id: 2,
        img: null
      },
      {
        name: "Название товара",
        price: 1200.10,
        id: 3,
        img: null
      },
      {
        name: "Название товара",
        price: 500.00,
        id: 4,
        img: null
      },
      {
        name: "Название товара",
        price: 5020.00,
        id: 1,
        img: null
      },
      {
        name: "Название товара",
        price: 5200.00,
        id: 2,
        img: null
      },
      {
        name: "Название товара",
        price: 1200.10,
        id: 3,
        img: null
      },
      {
        name: "Название товара",
        price: 6100.00,
        id: 4,
        img: null
      }
    ],
  },
  mutations: {
    addToLocalStorage(state) {
      if (state.itemsAddToCartArray.length>0) {
        localStorage.setItem('itemsAddToCartArray', JSON.stringify(state.itemsAddToCartArray));
      } else {
        let items = localStorage.getItem('itemsAddToCartArray');
        state.itemsAddToCartArray = JSON.parse(items) || [];
      }
    }
  },
  actions: {

  },
  getters: {
    // Добавьте геттеры для получения данных из хранилища
  }
});
