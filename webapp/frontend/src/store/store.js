import Vuex from 'vuex'

let tg = window.Telegram.WebApp;
tg.expand();
tg.MainButton.text = "В корзину";
tg.MainButton.color = "#59C0F9";
tg.MainButton.textColor = "#0C0C0C";
const url = new URL(window.location.href);
export const bot_id = url.searchParams.get('bot_id');
export const apiUrl = `https://ezbots.ru:2024`;
// export const apiUrl = `https://ezbots.ru:${import.meta.env.VITE_API_PORT}`
if (tg.colorScheme === 'dark') {
  document.body.setAttribute('data-theme', 'dark');
} else {
  document.body.setAttribute('data-theme', 'light');
}
export const Store = new Vuex.Store({
  state: {
    bot_id: bot_id,
    itemsAddToCartArray: [],
    items: [],
// {
//   "bot_id": 1,
//   "name": "модель кроссовок",
//   "description": "Шикарные кроссы с технологией air, позваляющие почувствовать ходьбу по-новому, на разработки были потрачены года - оно того стоило.... Шикарные кроссы с технологией air, позваляющие почувствовать ходьбу по-новому, на разработки были потрачены года - оно того стоило.... а разработки были потрачены года - оно того стоило... а разработки были потрачены года - оно того стоило...",
//   "price": 5000,
//   "count": 0,
//   "picture": 'https://th.bing.com/th/id/OIP.3S7vYZFSXZvIL89KCcpNoAHaHa?rs=1&pid=ImgDetMain',
//   "id": 1,
//   "sizes": [36, 36, 36, 36, 36, 36, 36, 36, 36],
//   "ranked": 4.5
// },
// {
//   "bot_id": 2,
//   "name": "nike air 2",
//   "description": "Посиругоисовриымиигуыивмивигивормгукынмршырмшгуышкщрммтшукршгкурмщкушкрмшугкмшуткршуршаркгрмуощышроркшгршытсршгрыырсощшуы",
//   "price": 3200,
//   "count": 0,
//   "picture": 'https://th.bing.com/th/id/OIP.3S7vYZFSXZvIL89KCcpNoAHaHa?rs=1&pid=ImgDetMain',
//   "id": 2,
//   "sizes": [36, 36, 36, 36, 36, 36, 36, 36, 36],
//   "ranked": 5.0
// }],
// filteredItems: [],
//   brands: [
//   {
//     "name": "Gucci",
//     "IsActive": false
//   },
//   {
//     "name": "Gucci",
//     "IsActive": false
//   },
//   {
//     "name": "Gucci",
//     "IsActive": false
//   },
//   {
//     "name": "Gucci",
//     "IsActive": false
//   },
//   {
//     "name": "Gucci",
//     "IsActive": false
//   },
    generatedOrderId: '',
    paymentMethod: '',
    address: '',
    comment: '',
  },
  services: {
    serviceItems: []
  },
  mutations: {
    addToSessionStorage(state) {
      if (state.itemsAddToCartArray.length>0) {
        sessionStorage.setItem('itemsAddToCartArray', JSON.stringify(state.itemsAddToCartArray));
      } else {
        let items = sessionStorage.getItem('itemsAddToCartArray');
        state.itemsAddToCartArray = JSON.parse(items) || [];
      }
    },
    setItems(state, items) {
      state.items = items;

    },
    // checkOrderId() {
    //   if (Store.state.generatedOrderId !== '') {
    //     sessionStorage.setItem('generatedOrderId', Store.state.generatedOrderId);
    //   } else {
    //     Store.state.generatedOrderId = sessionStorage.getItem('generatedOrderId');
    //   }
    // },
    // fetchOrderId() {
    //   async function fetchData () {
    //     try{
    //       const response = await fetch(`${apiUrl}/api/orders/generate_order_id`, {
    //         method: 'GET',
    //         headers: {
    //           'Content-Type': 'application/json',
    //           'Access-Control-Allow-Origin': '*'
    //         }
    //       });
    //       if(!response.ok) {
    //         new Error('Network response was not ok')
    //       }
    //       return await response.json()
    //     } catch (error) {
    //       console.error('There was a problem with the fetch operation:', error);
    //       return null;
    //     }
    //   }
    //   fetchData().then(data => {
    //     if (data) {
    //       Store.state.generatedOrderId = data;
    //     } else {
    //       console.log('No generatedOrderId received');
    //     }
    //   })
    // },
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
        const response = await fetch(`${apiUrl}/api/products/get_all_products/?bot_id=${bot_id}&price_min=0&price_max=2147483647`, {
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
        console.log(data);
        commit('setItems', data);
      } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
      }
    },
  },
  getters: {
  }
});


