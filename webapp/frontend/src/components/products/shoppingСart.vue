<script>
import { tg } from '@/main.js'
import router from "@/router/router.js";

export default {
    name: 'ShoppingCart',
    data() {
      return {
        inputValue: ''
      }
    },
    computed: {
      itemsAddToCartArray() {
        return this.$store.state.itemsAddToCartArray;
      },
    },
    methods: {
      backButtonMethod() {
        router.router.back();
      },
      mainButtonMethod() {
        router.router.push({ name: router.ORDER_DETAILS });
      },
      priceRub(price, count) {
        let totalValue = price * count
        const parts = totalValue.toString().split(/(?=(?:\d{3})+$)/);
        return parts.join(' ') + ' ₽';
      },
      incrementCount(item) {
        if (item && typeof item.countInCart === 'number') {
          item.countInCart += 1;
          this.totalPriceCalc();
        } else {
          console.error('Ошибка: объект item или count не определены.');
        }
      },
      decrementCount(item) {
        if (item && typeof item.countInCart === 'number') {
          if (item.countInCart > 1)
          {
            item.countInCart -= 1;
          } else {
            item.countInCart = 1
          }
          this.totalPriceCalc();
        } else {
          console.error('Ошибка: объект item или count не определены.');
        }
      },
      totalPriceCalc() {
        let price = this.itemsAddToCartArray.reduce((total, item) => total + item.price*item.countInCart, 0);
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
        router.router.replace({ name: router.PRODUCTS_PAGE, query: { bot_id: this.$store.state.bot_id }});
      }
    },
    mounted() {
      tg.BackButton.show();

      tg.MainButton.text = "Начать оформление";

      tg.onEvent('backButtonClicked', this.backButtonMethod);
      tg.onEvent('mainButtonClicked', this.mainButtonMethod);
    },
    unmounted() {
      tg.offEvent('backButtonClicked', this.backButtonMethod);
      tg.offEvent('mainButtonClicked', this.mainButtonMethod);

      this.$store.state.comment = this.inputValue;
    }
}
</script>

<template>
  <div class="wrapper">
  <div class="container-items">
    <div class="title">
      <span style="font-weight: bold; font-size: 20px">Ваш заказ</span>
      <svg @click="backToMainPage" width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
        <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
        <g id="SVGRepo_iconCarrier"> <path d="M15 13L12 13M12 13L9 13M12 13L12 10M12 13L12 16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path> <path d="M21.6359 12.9579L21.3572 14.8952C20.8697 18.2827 20.626 19.9764 19.451 20.9882C18.2759 22 16.5526 22 13.1061 22H10.8939C7.44737 22 5.72409 22 4.54903 20.9882C3.37396 19.9764 3.13025 18.2827 2.64284 14.8952L2.36407 12.9579C1.98463 10.3208 1.79491 9.00229 2.33537 7.87495C2.87583 6.7476 4.02619 6.06234 6.32691 4.69181L7.71175 3.86687C9.80104 2.62229 10.8457 2 12 2C13.1543 2 14.199 2.62229 16.2882 3.86687L17.6731 4.69181C19.9738 6.06234 21.1242 6.7476 21.6646 7.87495" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"></path>
      </g>
      </svg>
    </div>

    <ul class="items-styles">
      <li
        v-for="item in itemsAddToCartArray"
        :key="item.id"
        class="item-block"
      >
        <img style="border-radius: 7px; width: 150px; height: 150px; object-fit: cover;" v-if="item.picture && item.picture[0]" :src="`${this.$store.state.api_url}/files/` + (item.picture ? item.picture[0] : null)" alt="img">
        <img style="border-radius: 7px; width: 150px; height: 150px; object-fit: cover;" v-else src="@/assets/productArt.png" alt="img">
        <div style="display: flex; flex-direction: column; justify-content: space-between; padding: 0 2.5%">
          <div class="text-block">
            <span style="font-size: 15px; margin-bottom: 10px">{{ shortenName(item.name) }}</span>
            <span style="font-weight: bold; font-size: 20px;">{{priceRub(item.price, item.countInCart)}}</span>
          </div>
          <div class="buttons">
            <div class="countDivBtn">
              <div
                @click="decrementCount(item)"
              >-</div>
              {{item.countInCart}}
              <div
                @click="incrementCount(item)"
              >+</div>
            </div>
          </div>
        </div>
      </li>
    </ul>
  </div>
    <hr style="border: 1px solid var(--app-hr-border-color); width: 90%; margin: 0 auto">
  </div>

<!--  <textarea v-model="inputValue" placeholder="Добавить комментарий..."/>-->

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
