<script>
  import { bot_id, apiUrl } from '@/store/store.js'

  export default {
    name: 'ShoppingCart',
    data() {
      return {
        inputValue: ''
      }
    },
    mounted() {
      this.$store.commit("addToSessionStorage");
      let WebApp = window.Telegram.WebApp;
      const BackButton = WebApp.BackButton;
      const vm = this;
      BackButton.show();
      BackButton.onClick(function() {
        BackButton.hide();
      });
      WebApp.onEvent('backButtonClicked', function() {
          let tempItemsAddToCartArray = sessionStorage.getItem('itemsAddToCartArray')
          tempItemsAddToCartArray = JSON.parse(tempItemsAddToCartArray);
          sessionStorage.setItem('itemsAddToCartArray', JSON.stringify(tempItemsAddToCartArray));
          window.location.href = "/products-page?bot_id=" + vm.$store.state.bot_id;
      });
    },
    computed: {
      itemsAddToCartArray() {
        return this.$store.state.itemsAddToCartArray;
      },
    },
    methods: {
      apiUrl() {
        return apiUrl
      },
      bot_id() {
        return bot_id
      },
      priceRub(price, count) {
        let totalValue = price * count
        const parts = totalValue.toString().split(/(?=(?:\d{3})+$)/);
        return parts.join(' ') + ' ₽';
      },
      incrementCount(item) {
        if (item && typeof item.count === 'number') {
          item.count += 1;
          this.itemsAddToCart();
          this.totalPriceCalc();
        } else {
          console.error('Ошибка: объект item или count не определены.');
        }
      },
      decrementCount(item) {
        if (item && typeof item.count === 'number') {
          if (item.count > 1)
          {
            item.count -= 1;
          } else {
            item.count = 1
          }
          this.totalPriceCalc();
          this.itemsAddToCart();
        } else {
          console.error('Ошибка: объект item или count не определены.');
        }
      },
      itemsAddToCart() {
        this.$store.commit("addToSessionStorage");
      },
      totalPriceCalc() {
        let price = this.itemsAddToCartArray.reduce((total, item) => total + item.price*item.count, 0);
        if (price <= 0) {
          return 'Закать: 0 ₽'
        }
        return 'Заказать: ' + price.toFixed(2) + ' ₽'
      },
      shortenName(name) {
        if (!name) return '';
        return name.length > 20 ? name.substring(0, 15) + '...' : name;
      },
      backToMainPage() {
        let tempItemsAddToCartArray = sessionStorage.getItem('itemsAddToCartArray')
        tempItemsAddToCartArray = JSON.parse(tempItemsAddToCartArray);
        sessionStorage.setItem('itemsAddToCartArray', JSON.stringify(tempItemsAddToCartArray));
        window.location.href = "/products-page?bot_id=" + vm.$store.state.bot_id;
      }
    },
    beforeUnmount() {
      this.$store.state.comment = this.inputValue;
    }
  }
</script>

<template>
  <div class="wrapper">
  <div class="container-items">
    <div class="title">
      <span @click="backToMainPage" style="font-weight: bold; font-size: 20px">Ваш заказ</span>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path d="M0.4852 8.08809L10.3472 14.0051C10.8572 14.3111 11.4282 14.4641 12.0002 14.4641C12.5712 14.4641 13.1432 14.3111 13.6532 14.0051L23.5142 8.08809C23.8152 7.90709 23.9992 7.58209 23.9992 7.23109C23.9992 6.88009 23.8152 6.55409 23.5142 6.37409L13.6542 0.456088C12.6332 -0.156912 11.3672 -0.156912 10.3472 0.456088L0.4852 6.37309C0.1842 6.55409 0.000199499 6.87909 0.000199499 7.23009C0.000199499 7.58109 0.1842 7.90709 0.4852 8.08709V8.08809ZM11.3762 2.17109C11.7602 1.94109 12.2392 1.94109 12.6242 2.17109L21.0562 7.23109L12.6242 12.2911C12.2392 12.5211 11.7602 12.5211 11.3752 12.2911L2.9442 7.23009L11.3762 2.17109ZM24.0002 20.0001C24.0002 20.5531 23.5522 21.0001 23.0002 21.0001H21.0002V23.0001C21.0002 23.5531 20.5522 24.0001 20.0002 24.0001C19.4482 24.0001 19.0002 23.5531 19.0002 23.0001V21.0001H17.0002C16.4482 21.0001 16.0002 20.5531 16.0002 20.0001C16.0002 19.4471 16.4482 19.0001 17.0002 19.0001H19.0002V17.0001C19.0002 16.4471 19.4482 16.0001 20.0002 16.0001C20.5522 16.0001 21.0002 16.4471 21.0002 17.0001V19.0001H23.0002C23.5522 19.0001 24.0002 19.4471 24.0002 20.0001ZM12.8572 23.2861C12.6692 23.5981 12.3382 23.7711 11.9992 23.7711C11.8242 23.7711 11.6462 23.7251 11.4852 23.6281L0.4852 17.0291C0.0111995 16.7451 -0.141801 16.1311 0.1422 15.6571C0.4252 15.1831 1.0392 15.0291 1.5142 15.3141L12.5142 21.9141C12.9882 22.1981 13.1412 22.8121 12.8572 23.2861ZM23.8572 11.0901C24.1412 11.5641 23.9882 12.1781 23.5142 12.4621L12.5142 19.0621C12.3552 19.1571 12.1782 19.2051 11.9992 19.2051C11.8202 19.2051 11.6432 19.1571 11.4842 19.0621L0.4852 12.4621C0.0111995 12.1781 -0.141801 11.5641 0.1422 11.0901C0.4252 10.6151 1.0392 10.4621 1.5142 10.7471L11.9992 17.0381L22.4842 10.7471C22.9582 10.4631 23.5732 10.6161 23.8572 11.0901Z" fill="currentColor"/>
      </svg>
    </div>

    <ul class="items-styles">
      <li
        v-for="item in itemsAddToCartArray"
        :key="item.id"
        class="item-block"
      >
        <img style="border-radius: 7px; width: 150px; height: 150px; object-fit: cover;" v-if="item.picture" :src="item.picture" alt="img">
        <div v-else style="width: 150px; height: 150px; border-radius: 7px; background-color: #293C47;"></div>
        <div style="display: flex; flex-direction: column; justify-content: space-between; padding: 0 2.5%">
          <div class="text-block">
            <span style="font-size: 15px; margin-bottom: 10px">{{ shortenName(item.name) }}</span>
            <span style="font-weight: bold; font-size: 20px;">{{priceRub(item.price, item.count)}}</span>
          </div>
          <div class="buttons">
            <div class="countDivBtn">
              <div
                @click="decrementCount(item)"
              >-</div>
              {{item.count}}
              <div
                @click="incrementCount(item)"
              >+</div>
            </div>
<!--            <div class="calcBtn">-->
<!--              <button-->
<!--                style="background-color: #FF7171; display: flex; align-items: center; justify-content: center; width: 45%;"-->
<!--                @click="decrementCount(item)"-->
<!--              >-->
<!--                <svg width="22" height="4" viewBox="0 0 22 4" fill="none" xmlns="http://www.w3.org/2000/svg">-->
<!--                  <path d="M20.625 3.875H1.375C0.615613 3.875 0 3.03553 0 2C0 0.964473 0.615613 0.125 1.375 0.125H20.625C21.3844 0.125 22 0.964473 22 2C22 3.03553 21.3844 3.875 20.625 3.875Z" fill="white"/>-->
<!--                </svg>-->
<!--              </button>-->
<!--              <button-->
<!--                style="background-color:#71CBFF; display: flex; align-items: center; justify-content: center; width: 45%;"-->
<!--                @click="incrementCount(item)"-->
<!--              >-->
<!--                <svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">-->
<!--                  <path d="M19.6875 9.1875H11.8125V1.3125C11.8125 0.587631 11.2249 0 10.5 0C9.77513 0 9.1875 0.587631 9.1875 1.3125V9.1875H1.3125C0.587631 9.1875 0 9.77513 0 10.5C0 11.2249 0.587631 11.8125 1.3125 11.8125H9.1875V19.6875C9.1875 20.4124 9.77513 21 10.5 21C11.2249 21 11.8125 20.4124 11.8125 19.6875V11.8125H19.6875C20.4124 11.8125 21 11.2249 21 10.5C21 9.77513 20.4124 9.1875 19.6875 9.1875Z" fill="white"/>-->
<!--                </svg>-->
<!--              </button>-->
<!--            </div>-->
          </div>
        </div>
      </li>
    </ul>
  </div>
    <hr style="border: 1px solid var(--app-hr-border-color); width: 90%; margin: 0 auto">
  </div>
<!--  <textarea v-model="inputValue" placeholder="Добавить комментарий..."/>-->
  <RouterLink :to="`/products-page/order-details?bot_id=${bot_id()}`" ><button class="btnTotalPrice">Начать оформление</button></RouterLink>
</template>

<style scoped lang="scss">
#app {
  padding: 0;
}

*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 16px;
  line-height: 18.29px;
  color: var(--app-text-color);
}

.wrapper {
  width: 100%;
  height: 100%;
  background-color: var(--app-background-color);
}

.container-items{
  width: 100%;
  position: relative;
  left: 0;
  top: 0;
  padding: 2.5% 5%;
}

.items-styles{
  width: 100%;
  display: grid;
  grid-column: 1;
  grid-template-columns: repeat(auto-fill, minmax(95vw, 1fr)) ;
  grid-gap: 15px;
  padding: 0;
  margin-bottom: 15px;

  .item-block{
    display: flex;
    width: 100%;
    list-style-type: none;
  }
}
.order-wrapper{
  background-color: #20282C;
}

.text-block {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 5px;
}

.title {
  display: flex;
  justify-content: space-between;
  margin: 2.5% 0;
}

.countDivBtn {
  border-radius: 20px;
  background-color: var(--app-card-background-color);
  width: 126px;
  height: 41px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  font-weight: 500;
  font-size: 20px;
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  -khtml-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
  div {
    font-size: 36px;
    background-color: var(--app-card-background-color);
    cursor: pointer;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    -khtml-user-select: none;
    -moz-user-select: none;
    -ms-user-select: none;
    user-select: none;
    &:hover {
      opacity: 0.7;
    }
  }
}

.btnTotalPrice {
  width: 100%;
  height: 62px;
  color: #0C0C0C;
  background-color: #59C0F9;
  position: fixed;
  bottom: 0;
  left: 0;
  cursor: pointer;
  box-shadow: none;
  border: none;
  font-size: 20px;
  font-weight: bold;
  font-family: 'Montserrat', sans-serif;
  z-index: 10;
  &:hover{
    background-color: #82ccec;
  }
}

.buttons {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.calcBtn {
  display: flex;
  justify-content: space-evenly;
  margin-top: 5px;
}

button {
  cursor: pointer;
  box-shadow: none;
  border: none;
  border-radius: 5px;
}

textarea {
  background-color: #20282C;
  width: 100%;
  height: 53px;
  margin: 20px 0 40px;
  white-space: pre-wrap;
  resize: none;
  padding: 10px 20px;
  align-items: center;
  border: 1px solid #20282C;
  color: #46738D;
  font-family: 'Montserrat', sans-serif;
  font-weight: 500;
  font-size: 15px;
  position: relative;
  &:focus {
    outline: none;
  }
  &::placeholder{
    border: 1px solid #20282C;
    color: #46738D;
  }
}

@media (min-width: 1400px) {
  .items-styles {
    grid-template-columns: repeat(auto-fill, minmax(20vw, 1fr));
    margin: 30px auto 120px;
    width: 1200px;
  }
  .btnTotalPrice {
    height: 100px;
  }
}
</style>
