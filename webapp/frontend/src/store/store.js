import Vuex from 'vuex'

let tg = window.Telegram.WebApp;
tg.expand();
const bot_id_local = localStorage.getItem('bot_id')
const apiUrl = `https://ezbots.ru:${import.meta.env.VITE_API_PORT}`

export const Store = new Vuex.Store({
  state: {
    bot_id: bot_id_local,
    itemsAddToCartArray: [],
    items: [],
    generatedOrderId: '',
    paymentMethod: '',
    address: '',
    comment: '',
  },
  mutations: {
    addToLocalStorage(state) {
      if (state.itemsAddToCartArray.length>0) {
        localStorage.setItem('itemsAddToCartArray', JSON.stringify(state.itemsAddToCartArray));
      } else {
        let items = localStorage.getItem('itemsAddToCartArray');
        state.itemsAddToCartArray = JSON.parse(items) || [];
      }
    },
    setItems(state, items) {
      state.items = items;
      state.items = state.items.map(item => ({ ...item, count: 0 }));
    },
    checkOrderId() {
      if (Store.state.generatedOrderId !== '') {
        localStorage.setItem('generatedOrderId', Store.state.generatedOrderId);
      } else {
        Store.state.generatedOrderId = localStorage.getItem('generatedOrderId');
      }
    },
    fetchOrderId() {
      async function fetchData () {
        try{
          const response = await fetch(`${apiUrl}/api/orders/generate_order_id`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*'
            }
          });
          if(!response.ok) {
            new Error('Network response was not ok')
          }
          return await response.json()
        } catch (error) {
          console.error('There was a problem with the fetch operation:', error);
          return null;
        }
      }
      fetchData().then(data => {
        if (data) {
          Store.state.generatedOrderId = data;
        } else {
          console.log('No generatedOrderId received');
        }
      })
    },
    postData() {
      let data = {
        'order_id': Store.state.generatedOrderId,
        'bot_id': Store.state.bot_id,
        'products': Store.state.itemsAddToCartArray.reduce((acc, item) => {
          acc[item.id] = item.count;
          return acc;
        },{}),
        'payment_method': Store.state.paymentMethod,
        'ordered_at': new Date().toISOString(),
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
        const response = await fetch(`${apiUrl}/api/products/get_all_products/${Store.state.bot_id}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
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