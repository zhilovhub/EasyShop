<script>
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
          window.location.href = "/?bot_id=" + vm.$store.state.bot_id;
      });
    },
    computed: {
      itemsAddToCartArray() {
        return this.$store.state.itemsAddToCartArray;
      },
      totalPrice() {
        let price = this.itemsAddToCartArray.reduce((total, item) => total + item.price*item.count, 0);
        if (price <= 0) {
          return 'Заказать: 0 ₽'
        }
        return 'Заказать: ' + price + ' ₽'
      }
    },
    methods: {
      priceRub(price) {
        return price + ' ₽'
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
        return name.length > 15 ? name.substring(0, 12) + '...' : name;
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
      <span style="font-weight: 600; font-size: 24px">Ваш заказ</span>
      <svg style="cursor: pointer" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_31_564)">
          <path d="M0.484955 8.08803L10.347 14.005C10.857 14.311 11.428 14.464 12 14.464C12.571 14.464 13.143 14.311 13.653 14.005L23.514 8.08803C23.815 7.90703 23.999 7.58203 23.999 7.23103C23.999 6.88003 23.815 6.55403 23.514 6.37403L13.654 0.456027C12.633 -0.156973 11.367 -0.156973 10.347 0.456027L0.484955 6.37303C0.183955 6.55403 -4.46418e-05 6.87903 -4.46418e-05 7.23003C-4.46418e-05 7.58103 0.183955 7.90703 0.484955 8.08703V8.08803ZM11.376 2.17103C11.76 1.94103 12.239 1.94103 12.624 2.17103L21.056 7.23103L12.624 12.291C12.239 12.521 11.76 12.521 11.375 12.291L2.94396 7.23003L11.376 2.17103ZM24 20C24 20.553 23.552 21 23 21H21V23C21 23.553 20.552 24 20 24C19.448 24 19 23.553 19 23V21H17C16.448 21 16 20.553 16 20C16 19.447 16.448 19 17 19H19V17C19 16.447 19.448 16 20 16C20.552 16 21 16.447 21 17V19H23C23.552 19 24 19.447 24 20ZM12.857 23.286C12.669 23.598 12.338 23.771 11.999 23.771C11.824 23.771 11.646 23.725 11.485 23.628L0.484955 17.029C0.0109554 16.745 -0.142045 16.131 0.141955 15.657C0.424955 15.183 1.03896 15.029 1.51396 15.314L12.514 21.914C12.988 22.198 13.141 22.812 12.857 23.286ZM23.857 11.09C24.141 11.564 23.988 12.178 23.514 12.462L12.514 19.062C12.355 19.157 12.178 19.205 11.999 19.205C11.82 19.205 11.643 19.157 11.484 19.062L0.484955 12.462C0.0109554 12.178 -0.142045 11.564 0.141955 11.09C0.424955 10.615 1.03896 10.462 1.51396 10.747L11.999 17.038L22.484 10.747C22.958 10.463 23.573 10.616 23.857 11.09Z" fill="#71CBFF"/>
        </g>
        <defs>
          <clipPath id="clip0_31_564">
            <rect width="24" height="24" fill="white"/>
          </clipPath>
        </defs>
      </svg>
    </div>

    <ul class="items-styles">
      <li
        v-for="item in itemsAddToCartArray"
        :key="item.id"
        class="item-block"
      >
        <img style="border-radius: 7px; width: 67px; height: 67px; object-fit: cover;" v-if="item.picture" :src="'https://ezbots.ru:8080/files/' + item.picture" alt="img">
        <div v-else style="width: 67px; height: 67px; border-radius: 7px; background-color: #293C47;"></div>
        <div class="text-block">
          <span style="color: #71CBFF; font-size: 15px;">{{ shortenName(item.name) }}</span>
          <span style="font-weight: 600; color: #FFFFFF; font-size: 15px;">{{priceRub(item.price)}}</span>
        </div>
        <div class="buttons">
          <div class="countDivBtn">{{item.count}} шт.</div>
          <div class="calcBtn">
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
        </div>
      </li>
    </ul>
  </div>
  </div>
  <textarea v-model="inputValue" placeholder="Добавить комментарий..."/>
  <RouterLink to="/order-details"><button class="btnTotalPrice">{{this.totalPrice}}</button></RouterLink>
</template>

<style scoped lang="scss">
#app {
  padding: 0;
}

*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 15px;
  line-height: 18.29px;
  color: #FFFFFF;
}

.wrapper {
  width: 100%;
  height: 100%;
  background-color: #1E1E1E;
}

.container-items{
  background-color: #20282C;
  width: 100%;
  position: relative;
  left: 0;
  top: 0;
  padding: 2%;
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
    justify-content: space-between;
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
  justify-content: flex-end;
  padding: 5px;
}

.title {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.countDivBtn {
  border-radius: 7px;
  background-color: #293C47;
  width: 100px;
  aspect-ratio: 4/1;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 500;
  font-size: 15px;
}

.btnTotalPrice {
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
  z-index: 999;
  &:hover{
    background-color: #55A27D;
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