<script>
  export default {
    name: 'order-details',
    data() {
      return {
        inputValue: '',
        imageSrc: ''
      }
    },
    computed: {
      itemsAddToCartArray() {
        return this.$store.state.itemsAddToCartArray;
      },
      totalPrice() {
        let price = this.itemsAddToCartArray.reduce((total, item) => total + item.price*item.count, 0);
        if (price <= 0) {
          return '0 ₽'
        }
        return price + ' ₽'
      },
      totalPriceForButton() {
        let price = this.itemsAddToCartArray.reduce((total, item) => total + item.price*item.count, 0);
        if (price <= 0) {
          return 'Заказать: 0 ₽'
        }
        return 'Заказать: ' + price + ' ₽'
      },
      totalCount() {
        let count = this.itemsAddToCartArray.reduce((total, item) => total + item.count, 0);
        return count + ' товаров на сумму'
      }
    },
    mounted() {
      if (this.$store.state.itemsAddToCartArray && this.$store.state.itemsAddToCartArray.length > 0) {
        // Если условие выполняется, присваиваем imageSrc значение первой картинки в массиве
        this.imageSrc = this.$store.state.items[0][0].picture;
      }
      this.$store.commit("addToLocalStorage");
      this.inputValue = 'г. Москва, Большой Строченовский переулок 5'
    },
    methods: {
      orderBtnClicked() {
        this.$store.state.address = this.inputValue;
        this.$store.commit("postData");
      }
    }
  }
</script>

<template>
  <div class="main-body">
  <div class="title-div">
    <img style="width: 134px; height: 134px; border-radius: 7px;" src="../../src/assets/logo.png" alt="image">
    <div class="title-text">
      <span style="font-size: 24px; margin-bottom: 15px">Заказ №63782</span>
      <span style="color: #71CBFF; font-size: 15px; font-weight: 500">Название заказа</span>
    </div>
  </div>

  <div class="address-container">
    <span style="color: #71CBFF;">Адрес доставки</span>
    <textarea v-model="inputValue"></textarea>
  </div>

  <div class="pay-container">
    <span style="color: #71CBFF;">Способы оплаты</span>
    <select>
      <option value="card-online">Картой онлайн</option>
      <option value="usdt">USDT</option>
      <option value="bitcoin">Bitcoin</option>
      <option value="cash">Cash</option>
    </select>
  </div>
  </div>
  <div class="footer">
    <div style="margin: 0 0 10px">
      <span style="font-size: 20px; color: #FFFFFF">Итого</span>
      <span style="font-size: 20px; color: #FFFFFF">{{totalPrice}}</span>
    </div>
    <div>
      <span>{{totalCount}}</span>
      <span>{{totalPrice}}</span>
    </div>
    <div>
      <span>Скидка</span>
      <span>0 ₽</span>
    </div>
    <div>
      <span>Доставка</span>
      <span>0 ₽</span>
    </div>
  </div>
  <button @click="orderBtnClicked()" class="btnTotalPrice">{{this.totalPriceForButton}}</button>
</template>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 15px;
  line-height: 18.29px;
  color: #FFFFFF;
}

.main-body {
  position: relative;
}

.title-div {
  background-color: #20282C;
  width: 100%;
  position: relative;
  left: 0;
  top: 0;
  padding: 4%;
  display: flex;
  justify-content: start;
  margin-bottom: 40px;
  .title-text {
    margin-left: 30px;
    display: flex;
    flex-direction: column;
    justify-content: start;
    font-size: 24px;
    font-weight: 600;
  }
}

.address-container {
  background-color: #20282C;
  display: flex;
  flex-direction: column;
  padding: 2.5% 4%;
  margin-bottom: 40px;
  textarea {
    background-color: #293C47;
    width: 100%;
    height: 65px;
    border-radius: 7px;
    margin: 10px auto;
    white-space: pre-wrap;
    resize: none;
    color: #FFFFFF;
    padding: 12px 20px;
    align-items: center;
    border: 1px solid #20282C;
    font-family: 'Montserrat', sans-serif;
    font-weight: 500;
    font-size: 15px;
    &::placeholder{
      border: 1px solid #20282C;
    }
    &:focus {
      outline: none;
    }
  }
}

.pay-container {
  background-color: #20282C;
  display: flex;
  flex-direction: column;
  padding: 2.5% 4%;
  select {
    width: 100%;
    height: 50px;
    background-color: #293C47;
    border: 1px solid #20282C;
    border-radius: 7px;
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    background-image: url('../assets/arrow-down.png') !important;
    background-position: center right 20px;
    background-repeat: no-repeat;
    background-size: auto 15%;
    padding-left: 20px;
    margin: 10px auto;
    &:hover, :focus, :active {
      outline: none;
    }
  }
}

.btnTotalPrice {
  width: 100%;
  height: 52px;
  color: #293C47;
  background-color: #FF9F59;
  position: fixed;
  bottom: 0;
  left: 0;
  cursor: pointer;
  box-shadow: none;
  border: none;
  font-size: 24px;
  font-weight: 600;
  padding: 20px;
  font-family: 'Montserrat', sans-serif;
  z-index: 999;
  &:hover{
    background-color: #965F37;
  }
}

.footer {
  display: flex;
  width: 100%;
  flex-direction: column;
  position: relative;
  margin-top: 30vh;
  padding: 10px 20px;
  div {
    display: flex;
    justify-content: space-between;
    span {
      margin: 3px;
      color: #577B8F;
      font-size: 16px;
    }
  }
}

@media (max-width: 600px) {
  .footer {
    bottom: 70px;
  }
}
@media (max-width: 300px) {
  .footer {
    bottom: 50px;
  }
  .btnTotalPrice {
    font-size: 22px;
  }
}
@media (min-width: 1400px) {
  .btnTotalPrice {
    height: 100px;
  }
}
</style>