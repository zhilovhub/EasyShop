import Vuex from 'vuex'
let tg = window.Telegram.WebApp;
tg.expand();
const url = new URL(window.location.href);
const token = url.searchParams.get('token');
const apiUrl = 'https://ezbots.ru:8080'

export const Store = new Vuex.Store({
  state: {
    token: "",
    itemsAddToCartArray: [],
    items: [],
    address: ''
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
    itemsInit() {
      async function fetchItems() {
        try {
          const response =  await fetch(`${apiUrl}/api/products/get_all_products/${token}`,
            {
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
      fetchItems().then(data => {
        if (data) {
          console.log('Data received')
          Store.state.items = data
          Store.state.items = Store.state.items.map(item => ({ ...item, count: 0 }));
        } else {
          console.log('No data received');
        }
      });
      Store.state.token = token;
    },
    postData() {
      let data = {
        "order_id": Number,
	"token": String
      };
      async function fetchData() {
        try {
          const response = await fetch(`${apiUrl}/api/orders/add_order`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              'bot_token': Store.state.token,
              'from_user': 0,
              'products_id': Store.state.itemsAddToCartArray.map(item => item.id),
              'ordered_at': new Date().toISOString(),
              'address': Store.state.address,
              'status': 'backlog',
            })
          });
          if (!response.ok) {
            new Error('Network response was not ok');
          }
          return await response.json();
        } catch (error) {
          console.error('There was a problem with the fetch operation:', error);
          return null;
        }
      }
      fetchData().then(response => {
        if (response) {
          data.order_id = response.id;
	  data.token = token;
          tg.sendData(JSON.stringify(data));
          tg.close();
        } else {
          console.log('No data received');
        }
      });
    },
  },
  actions: {

  },
  getters: {
  }
});
