import Vuex from 'vuex'
import { tg } from '@/main.js'
import '@/assets/base.css'
import heic2any from "heic2any";


export const Store = new Vuex.Store({
  state: {
    bot_id: null,
    api_url: `https://ezbots.ru:${import.meta.env.VITE_API_PORT}/api`,
    itemsAddToCartArray: [],
    items: [],
    filters: [],
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
    }
  },
  actions: {
    async itemsInit({ commit }, is_admin_request) {
      try {
        let filters = {
          "filter_name": "price",
          "is_category_filter": false,
          "reverse_order": Store.state.reverse_order
        }
        const response = await fetch(`${Store.state.api_url}/products/get_all_products/?bot_id=${Store.state.bot_id}&price_min=${Store.state.price_min}&price_max=${Store.state.price_max}&is_admin_request=${is_admin_request}`, {
          method: 'Post',
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'authorization-data': tg.initData,
          },
          body: JSON.stringify(Store.state.reverse_order === true || Store.state.reverse_order === false ? [filters] : [])
        });
        if (response.status === 406) {
          console.log(406)
        }
        if (!response.ok) {
          return 406;
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
        await fetch(`${Store.state.api_url}/products/del_product/${Store.state.bot_id}/${productId}`, {
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
        const response = await fetch(`${Store.state.api_url}/categories/get_all_categories/${Store.state.bot_id}`, {
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
        await fetch(`${Store.state.api_url}/categories/add_category`, {
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
    async convertHEIC(t, dt) {
      console.log("dt", dt)
      let vm = dt[3];
      vm.reasonLoading = "Обработка HEIC файла...";
      let file = dt[0];
      console.log("file", file)
      let imagePreviews = dt[1];
      console.log("imagePreviews", imagePreviews)
      let imageFiles = dt[2];
      try {
        let converted_file = await heic2any({
          blob: file,
          toType: "image/jpeg",
          quality: 1.0
      })
        vm.reasonLoading = "HEIC файл конвертирован.";
        console.log(converted_file)
        converted_file.name = file.name.substring(0, file.name.lastIndexOf('.')) + '.jpeg';
        return [converted_file, imagePreviews, imageFiles, vm]
      } catch (err) {
        alert(err)
        vm.isLoading = false;
        vm.reasonLoading = '';
      }


      // ).then(function (convertedFile) {
      //   alert("convert heic then called")
      //     convertedFile.name = file.name.substring(0, file.name.lastIndexOf('.')) + '.jpeg';
      //     return [convertedFile, imagePreviews, imageFiles];
      // }).catch(err => {
      //   alert("convert heic catch called")
      //   alert(err)
      //     console.log("file type is not heic, skipping converting..");
      //     return [file, imagePreviews, imageFiles]
      // });
    },
    async addProduct({commit, dispatch}, productInformation) {
      try {
        const { name , category, description, article, price, count, extra_options, images } = productInformation;
        const response = await fetch(`${Store.state.api_url}/products/add_product`, {
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
        if (response.status === 409) {
          return 409;
        }

        console.log("addProduct Test picture", images)
        const formData = new FormData();
        for (let i = 0; i< images.length; i++) {
          console.log("addProduct foreach picture", images[i])
           formData.append(`files`, images[i]);
        }
        const productId = await response.json()
        if (productId && typeof productId !== 'object') {
          try {
            await fetch(`${Store.state.api_url}/products/add_product_photo?bot_id=${Store.state.bot_id}&product_id=${productId}`, {
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
      async getProduct({commit}, productInformation) {
        try{
          const {productId, botId} = productInformation;
          let response = await fetch(`${Store.state.api_url}/products/get_product/${botId}/${productId}`)
          response = await response.json();
          console.log(response)
          return response;
        } catch (error) {
          console.error(error);
        }
      },
      async editProduct({commit}, productInformation) {
        try {
          const { name , category, description, article, price, count, extra_options, picture, id} = productInformation;
          const response = await fetch(`${Store.state.api_url}/products/edit_product`, {
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
              "extra_options": extra_options || {},
              "id": id,
            })
          });


          console.log("editProduct Test picture", picture)
          const formData = new FormData();
          for (let i = 0; i< picture.length; i++) {
            console.log("editProduct foreach picture", picture[i])
            formData.append(`files`, picture[i]);
          }
          const productId = id
          console.log("editProduct Test productId", productId)

          if (productId) {
            try {
              await fetch(`${Store.state.api_url}/products/add_product_photo?bot_id=${Store.state.bot_id}&product_id=${productId}`, {
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

        } catch (error) {
          console.error('There was a problem with the fetch operation:', error);
        }
      },
      async getWebAppOptions() {
        console.log(Store.state.bot_id);
        try {
          const response = await fetch(`${Store.state.api_url}/settings/get_web_app_options/${Store.state.bot_id}`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*',
            },
          });
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          const data = await response.json();

          if (data.bg_color && data.bg_color.length>0) {
            document.documentElement.style.setProperty('--app-background-color', data.bg_color);
            document.body.removeAttribute('data-theme');
          }

        } catch (error) {
          console.error('There was a problem with the fetch operation:', error);
        }
      },
      async postData({commit}, orderInformation) {
        const {name, phone_number, town, address, time, comment, delivery_method, mainButtonFunction} = orderInformation;
        let data = {
          'bot_id': Store.state.bot_id,
          'raw_items': Store.state.itemsAddToCartArray.reduce((cartItemsById, item) => {
            cartItemsById[item.id] = {"amount": item.countInCart, "chosen_options": item.chosenOption};
            return cartItemsById;
          }, {}),
          'ordered_at': new Date().toISOString(),
          'name': name,
          'phone_number': phone_number,
          'town': town,
          'address': address,
          'time': time || '',
          'comment': comment || '',
          'delivery_method': delivery_method || ''
        };
        try {
          tg.offEvent('mainButtonClicked', mainButtonFunction);
          if (tg.initDataUnsafe.query_id) {
            data.query_id = tg.initDataUnsafe.query_id;
          }
          if (tg.initDataUnsafe.user.id) {
            data.from_user = tg.initDataUnsafe.user.id;
          }

          const response = await fetch(`${Store.state.api_url}/orders/send_order_data_to_bot`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Access-Control-Allow-Origin': '*',
              'authorization-data': tg.initData,
            },
            body: JSON.stringify(data)
          });
          if (!response.ok) {
            throw new Error('Network response was not ok');
          } else {
            const resp_data = await response.json()
            console.log(resp_data)
            let invoice_url = resp_data.invoice_url
            if (invoice_url) {
              tg.openInvoice(invoice_url)
            } else {
              tg.close();
            }
          }
        } catch (error) {
          console.error('There was a problem with the fetch operation:', error);
          alert("Произошла ошибка при создании заказа :(")
          tg.onEvent('mainButtonClicked', mainButtonFunction);
        }
      },
      async postColorData({commit}, sent_color_data){
        const {color} = sent_color_data;
        console.log(color)
        try {
            const response = await fetch(`${Store.state.api_url}/settings/send_hex_color_to_bot`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
              },
              body: JSON.stringify({
                color: color,
                query_id: tg.initDataUnsafe.query_id
              })
            });
            if (!response.ok) {
              throw new Error('Network response was not ok');
            } else {
              tg.close();
            }
          } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
            alert("Произошла ошибка при отправке цвета :(")
          }
      }
  },
  getters: {

  }
});
