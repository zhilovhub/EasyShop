import Vuex from 'vuex'

export const Store = new Vuex.Store({
  state: {
    itemsAddToCartArray: [],
    items: [],
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
      const url = new URL(window.location.href);
      let token = url.searchParams.get('token');
      const apiUrl = 'http://92.118.114.106:8000'
      async function fetchItems() {
        try {
          token = "1843147988_AAGpwpOZSn8SLAEnWPQwWo7MjoTZR2aBv0o";
          const response =  await fetch(`${apiUrl}/api/products/get_all_products/${token}`,
            {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
              }
            });
          console.log(response)
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
          console.log(data)
          console.log('Data received')
          Store.state.items = data
          Store.state.items = Store.state.items.map(item => ({ ...item, count: 0 }));
        } else {
          console.log('No data received');
        }
      });
    }
  },
  actions: {

  },
  getters: {
  }
});
