import Vuex from 'vuex'
import { tg } from '@/main.js'

export const Store = new Vuex.Store({
  state: {
    bot_id: undefined,
    api_url: `https://ezbots.ru:2024`,
    // api_url: `https://ezbots.ru:${import.meta.env.VITE_API_PORT}`,
    itemsAddToCartArray: [],
    items: [],
    town: '',
    address: '',
    comment: '',
  },
  services: {
    serviceItems: []
  },
  mutations: {
    setItems(state, items) {
      state.items = items;
      state.items = state.items.map(item => ({ ...item, countInCart: 0 }));
      state.items = state.items.map(item => ({ ...item, isSelected: false }));
      state.items = state.items.map(item => ({...item, isActive: false}));
    },
    postData() {
      let data = {
        'bot_id': Store.state.bot_id,
        'raw_items': Store.state.itemsAddToCartArray.reduce((cartItemsById, item) => {
          cartItemsById[item.id] = {"amount": item.countInCart, "used_extra_options": item.used_extra_options, "chosen_option": item.chosenOption};
          return cartItemsById;
        },{}),
        'ordered_at': new Date().toISOString(),
        'town': Store.state.town,
        'address': Store.state.address,
        'comment': Store.state.comment
      };
      tg.sendData(JSON.stringify(data));
      tg.close();
    }
  },
  actions: {
    async itemsInit({ commit }) {
      try {
        const response = await fetch(`${Store.state.api_url}/api/products/get_all_products/?bot_id=${Store.state.bot_id}&price_min=0&price_max=2147483647`, {
          method: 'Post',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          },
          body: JSON.stringify([])
        });
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        commit('setItems', data);
      } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
      }
    },
  },
  getters: {
  }
});


