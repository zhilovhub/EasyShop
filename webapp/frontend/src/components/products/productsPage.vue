<template>
  <div class="wrapper">
    <div v-if="isLoading" class="loading-message">
      Загрузка...
    </div>
    <div v-else-if="items.length === 0"
         style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -75%); text-align: center; width: 350px"
    >
      <div style="font-size: 24px; color: #FFFFFF; font-weight: 600; word-wrap: break-word; margin-bottom: 20px">Товары в магазине отсутствуют</div>
      <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_349_452)">
          <path d="M36 72C28.8799 72 21.9197 69.8887 15.9995 65.9329C10.0793 61.9772 5.46511 56.3548 2.74035 49.7766C0.0155983 43.1985 -0.697322 35.9601 0.691746 28.9768C2.08081 21.9935 5.50948 15.5789 10.5442 10.5442C15.5789 5.50948 21.9935 2.08081 28.9768 0.691746C35.9601 -0.697322 43.1985 0.0155983 49.7766 2.74035C56.3548 5.46511 61.9772 10.0793 65.9329 15.9995C69.8887 21.9197 72 28.8799 72 36C71.9897 45.5446 68.1935 54.6954 61.4445 61.4445C54.6954 68.1935 45.5446 71.9897 36 72ZM36 6.00002C30.0666 6.00002 24.2664 7.75949 19.3329 11.0559C14.3994 14.3524 10.5543 19.0377 8.28363 24.5195C6.013 30.0013 5.4189 36.0333 6.57646 41.8527C7.73402 47.6722 10.5912 53.0177 14.7868 57.2132C18.9824 61.4088 24.3279 64.266 30.1473 65.4236C35.9667 66.5811 41.9987 65.987 47.4805 63.7164C52.9623 61.4458 57.6477 57.6006 60.9441 52.6671C64.2405 47.7337 66 41.9335 66 36C65.9913 28.0462 62.8278 20.4207 57.2036 14.7965C51.5794 9.17226 43.9538 6.00875 36 6.00002ZM53.238 53.001C53.5009 52.7071 53.7032 52.3642 53.8334 51.9919C53.9636 51.6197 54.0192 51.2255 53.9969 50.8318C53.9746 50.4381 53.8749 50.0526 53.7035 49.6975C53.5321 49.3423 53.2924 49.0244 52.998 48.762C48.2344 44.6924 42.2574 42.3147 36 42C29.7427 42.3147 23.7656 44.6924 19.002 48.762C18.4077 49.2911 18.0478 50.0347 18.0017 50.8291C17.9556 51.6235 18.2269 52.4037 18.756 52.998C19.2851 53.5924 20.0287 53.9522 20.8231 53.9983C21.6175 54.0445 22.3977 53.7731 22.992 53.244C26.6594 50.1562 31.2164 48.3191 36 48C40.7835 48.3195 45.3404 50.1566 49.008 53.244C49.6016 53.7717 50.3803 54.0425 51.1733 53.9969C51.9662 53.9514 52.7087 53.5932 53.238 53.001ZM18 30C18 33 20.685 33 24 33C27.315 33 30 33 30 30C30 28.4087 29.3679 26.8826 28.2427 25.7574C27.1174 24.6322 25.5913 24 24 24C22.4087 24 20.8826 24.6322 19.7574 25.7574C18.6322 26.8826 18 28.4087 18 30ZM42 30C42 33 44.685 33 48 33C51.315 33 54 33 54 30C54 28.4087 53.3679 26.8826 52.2427 25.7574C51.1174 24.6322 49.5913 24 48 24C46.4087 24 44.8826 24.6322 43.7574 25.7574C42.6322 26.8826 42 28.4087 42 30Z" fill="#71CBFF"/>
        </g>
        <defs>
          <clipPath id="clip0_349_452">
            <rect width="72" height="72" fill="white"/>
          </clipPath>
        </defs>
      </svg>
    </div>
    <ul v-else class="items-styles">
      <li
          v-for="item in items"
          :key="item.id"
          class="item-block"
          style="position: relative;"
      >
        <img style="border-radius: 10px; width: 100%; height: 100%; object-fit: cover; margin: 5px auto;" v-if="item.picture" :src="'https://ezbots.ru:8080/files/' + item.picture" alt="img">
        <div style="margin-bottom: 10px">
        <span style="color: #71CBFF; font-size: 15px;">
          {{ shortenName(item.name) }}
        </span>
          <br>
          <span style="font-weight: 600; color: #FFFFFF; font-size: 15px;">
          {{priceComma(item.price)}}
        </span>
        </div>
        <button
            type="button"
            v-if="item.count === 0"
            @click="incrementCount(item)"
            style="height: 17.5%;"
        >
          Добавить
        </button>
        <div
            v-else
            style="display: flex; justify-content: space-between; height: 17.5%"
        >
          <button
              style="background-color: #FF7171; display: flex; align-items: center; justify-content: center; width: 45%;"
              @click="decrementCount(item)"
          >
            <svg width="22" height="4" viewBox="0 0 22 4" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20.625 3.875H1.375C0.615613 3.875 0 3.03553 0 2C0 0.964473 0.615613 0.125 1.375 0.125H20.625C21.3844 0.125 22 0.964473 22 2C22 3.03553 21.3844 3.875 20.625 3.875Z" fill="white"/>
            </svg>
          </button>
          <button
              style="background-color:#71CBFF; display: flex; align-items: center; justify-content: center; width: 45%;"
              @click="incrementCount(item)"
          >
            <svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19.6875 9.1875H11.8125V1.3125C11.8125 0.587631 11.2249 0 10.5 0C9.77513 0 9.1875 0.587631 9.1875 1.3125V9.1875H1.3125C0.587631 9.1875 0 9.77513 0 10.5C0 11.2249 0.587631 11.8125 1.3125 11.8125H9.1875V19.6875C9.1875 20.4124 9.77513 21 10.5 21C11.2249 21 11.8125 20.4124 11.8125 19.6875V11.8125H19.6875C20.4124 11.8125 21 11.2249 21 10.5C21 9.77513 20.4124 9.1875 19.6875 9.1875Z" fill="white"/>
            </svg>
          </button>
        </div>
        <div v-if="item.count > 0" class="circle">
          {{item.count}}
        </div>
      </li>
    </ul>
  </div>
  <RouterLink :to="`/products-page/shopping-cart/?bot_id=${bot_id()}`" v-if="itemsAddToCartArray.length>0"><button class="addToCartBtn">В Корзину</button></RouterLink>
</template>

<script>

import { bot_id } from '@/store/store.js'
import * as https from 'https'

export default {
  name: 'productsPage',
  data() {
    return {
      isLoading: true
    }
  },
  methods: {
    bot_id() {
      return bot_id
    },
    priceComma(price) {
      return price + ' ₽'
    },
    incrementCount(item) {
      if (item && typeof item.count === 'number') {
        item.count += 1;
        this.itemsAddToCart();
      } else {
        console.error('Ошибка: объект item или count не определены.');
      }
    },
    decrementCount(item) {
      if (item && typeof item.count === 'number') {
        item.count -= 1;
        this.itemsAddToCart()
      } else {
        console.error('Ошибка: объект item или count не определены.');
      }
    },
    itemsAddToCart() {
      this.$store.state.itemsAddToCartArray = this.$store.state.items.filter(item => item.count > 0);
    },
    shortenName(name) {
      if (!name) return '';
      return name.length > 15 ? name.substring(0, 15) + '...' : name;
    }
  },
  computed: {
    https() {
      return https
    },
    items() {
      return this.$store.state.items;
    },
    itemsAddToCartArray() {
      return this.$store.state.itemsAddToCartArray;
    },
  },
  mounted() {
    this.$store.dispatch('itemsInit').then(() => {
      this.isLoading = false;
      let tempCheckItems = sessionStorage.getItem('itemsAddToCartArray');
      tempCheckItems = JSON.parse(tempCheckItems);
      if (tempCheckItems && tempCheckItems.length > 0 && tempCheckItems.length !== this.items.length) {
        //Проверка совпадает ли длина из хранилища сессии с длиной из сервера, если не совпадает, то заменяется только совпадающий элемент(т.е его поле count).
        let resultArray = [];
        for (let i = 0; i < this.$store.state.items.length; i++) {
          let matchingItem = tempCheckItems.find(item => item.id === this.$store.state.items[i].id);
          resultArray.push(matchingItem || this.$store.state.items[i]);
        }
        this.$store.state.items = resultArray;
        this.itemsAddToCart();
      }
      else if(tempCheckItems && tempCheckItems.length > 0) {
        //Если все элементы из локального хранилища совпадают с теми, что на сервере, то приоритет отдаётся тем, что в хранилище сессии.
        let itemsMatch = true;
        for (let i = 0; i < this.items.length; i++) {
          if (this.items[i].id !== tempCheckItems[i].id) {
            itemsMatch = false;
            break;
          }
        }
        if (itemsMatch) {
          this.$store.state.items = tempCheckItems;
          this.itemsAddToCart();
        }
      }
    });
    this.$store.commit("fetchOrderId");
    this.$store.commit("checkOrderId");
  }
};
</script>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 15px;
  line-height: 18.29px;
}

.items-styles{
  width: 90%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(40vw, 1fr));
  grid-column: 1;
  grid-gap: 15px;
  padding: 0;
  margin: 20px auto 50px;

  .item-block{
    aspect-ratio: 1/1;
    white-space: nowrap;
    background-color: #293C47;
    list-style-type: none;
    display: flex;
    flex-direction: column;
    justify-content: end;
    border-radius: 10px;
    padding: 12px;
  }
}

.loading-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #FFFFFF;
  font-size: 24px;
}

button {
  width: 100%;
  aspect-ratio: 5/1;
  background-color: #71CBFF;
  border-radius: 5px;
  cursor: pointer;
  box-shadow: none;
  border: none;
  &:hover {
    background-color: #3F5C6D;
    color:  #293C47;
  }
}

.circle {
  border-radius: 100%;
  background-color: #71CBFF;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  right: 10px;
  top: 10px;
}

.addToCartBtn {
  width: 100%;
  height: 52px;
  color: #293C47;
  background-color: #59FFAF;
  position: fixed;
  bottom: 0;
  left: 0;
  cursor: pointer;
  box-shadow: none;
  border: none;
  font-size: 24px;
  font-weight: 600;
  font-family: 'Montserrat', sans-serif;
  z-index: 10;
  &:hover{
    background-color: #55A27D;
  }
}
@media (min-width: 1400px) {
  .addToCartBtn{
    height: 100px;
  }
}

@media (max-width: 300px) {
  .items-styles {
    grid-template-columns: repeat(auto-fill, minmax(95vw, 1fr));
    margin: 10px auto 40px;
    justify-content: center;
  }
}
@media (min-width: 700px) {
  .items-styles {
    grid-template-columns: repeat(auto-fill, minmax(35vw, 1fr));
    margin: 30px auto 40px;
    justify-content: center;
    width: 95%
  }
}
@media (min-width: 950px) and (max-width: 1400px) {
  .items-styles {
    grid-template-columns: repeat(2, minmax(20vw, 1fr));
    margin: 30px auto 50px;
  }
  .wrapper {
    margin: 0 auto;
  }
}
@media (min-width: 1400px) {
  .items-styles {
    grid-template-columns: repeat(auto-fill, minmax(20vw, 1fr));
    margin: 30px auto 120px;
    width: 1200px;
  }
}
</style>
