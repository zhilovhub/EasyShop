import Vuex from 'vuex'
import { tg } from '@/main.js'


export const Store = new Vuex.Store({
  state: {
    bot_id: null,
    api_url: `https://ezbots.ru:${import.meta.env.VITE_API_PORT}`,
    itemsAddToCartArray: [],
    items: [],
    filters: [],
    name: '',
    town: '',
    address: '',
    comment: '',
    phoneNumber: '',
    price_min: 0,
    price_max: 2147483647,
    reverse_order: null,
    categories: [],
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
    setFilters(state, filters) {
      state.filters = filters
    },
    setCategories(state, categories) {
      state.categories = categories;
      state.categories = state.categories.map(item => ({...item, isSelected: false }));
    },
    postData() {
      let data = {
        'bot_id': Store.state.bot_id,
        'raw_items': Store.state.itemsAddToCartArray.reduce((cartItemsById, item) => {
          cartItemsById[item.id] = {"amount": item.countInCart, "chosen_options": item.chosenOption};
          return cartItemsById;
        }, {}),
        'ordered_at': new Date().toISOString(),
        'name': Store.state.name,
        'phone_number': Store.state.phoneNumber,
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
        let filters = {
          "filter_name": "price",
          "is_category_filter": false,
          "reverse_order": Store.state.reverse_order
        }
        const response = await fetch(`${Store.state.api_url}/api/products/get_all_products/?bot_id=${Store.state.bot_id}&price_min=${Store.state.price_min}&price_max=${Store.state.price_max}`, {
          method: 'Post',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          },
          body: JSON.stringify(Store.state.reverse_order === true || Store.state.reverse_order === false ? [filters] : [])
        });
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        commit('setItems', data);
        console.log(data);
      } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
      }
    },
    async deleteProduct({commit}, productId) {
      try {
        await fetch(`${Store.state.api_url}/api/products/del_product/${Store.state.bot_id}/${productId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'authorization-data': tg.initData,
          },
        });
      } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        if ("Unauthorized" in error.toString()){
          console.error("Ошибка авторизации. Попробуйте переоткрыть окно MiniApp.") // TODO заменить на задизайненую менюшку
        }
      }
    },
    async getCategories({commit}) {
      try {
        const response = await fetch(`${Store.state.api_url}/api/categories/get_all_categories/${Store.state.bot_id}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'authorization-data': tg.initData,
          },
        });
        const data = await response.json();
        commit('setCategories', data);
      } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        if ("Unauthorized" in error.toString()){
          console.error("Ошибка авторизации. Попробуйте переоткрыть окно MiniApp.") // TODO заменить на задизайненую менюшку
        }
      }
    },
    async addCategory({commit}, name) {
      try {
        await fetch(`${Store.state.api_url}/api/categories/add_category`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'authorization-data': tg.initData,
          },
          body: JSON.stringify({
            "bot_id": Store.state.bot_id,
            "name": name
          })
        });
      } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        if ("Unauthorized" in error.toString()){
          alert("Ошибка авторизации. Попробуйте переоткрыть окно MiniApp.") // TODO заменить на задизайненую менюшку
        }
        return {msg: "error", cat_id: -1}
      }
    },
    async addProduct({commit, dispatch}, productInformation) {
      try {
        const { name , category, description, article, price, count, extra_options, images } = productInformation;
        const response = await fetch(`${Store.state.api_url}/api/products/add_product`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'authorization-data': tg.initData,
          },
          body: JSON.stringify({
            "bot_id": parseInt(Store.state.bot_id),
            "name": name,
            "category": category,
            "description": description,
            "article": article,
            "price": price || 0,
            "count": count || 0,
            "extra_options": extra_options || []
          })
        });

        const formData = new FormData();
        for (let i = 0; i< images.length; i++) {
           formData.append(`files`, images[i]);
        }
        const productId = await response.json()
        if (productId) {
          try {
            await fetch(`${Store.state.api_url}/api/products/add_product_photo?bot_id=${Store.state.bot_id}&product_id=${productId}`, {
              method: 'POST',
              headers: {
                'Access-Control-Allow-Origin': '*',
                'authorization-data': tg.initData,
              },
                body: formData
              });
            } catch (error) {
              console.error('There was a problem with the fetch operation:', error);
            }
          }
        }  catch (error) {
          console.error('There was a problem with the fetch operation:', error);
        }
      },
      async editProduct({commit}, productInformation) {
        try {
          const { name , category, description, article, price, count, extra_options, pictures, id} = productInformation;
          const response = await fetch(`${Store.state.api_url}/api/products/edit_product`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*',
              'authorization-data': tg.initData,
            },
            body: JSON.stringify({
              "bot_id": parseInt(Store.state.bot_id),
              "name": name,
              "category": category,
              "description": description,
              "article": article,
              "price": price || 0,
              "count": count || 0,
              "picture": pictures,
              "extra_options": extra_options || {},
              "id": id,
            })
          });
        } catch (error) {
          console.error('There was a problem with the fetch operation:', error);
        }
      }
    },
  getters: {
}
});