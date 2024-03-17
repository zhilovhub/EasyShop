<script>
  export default {
    name: 'orderDetails',
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
      },
      orderId () {
        this.$store.commit("checkOrderId");
        return this.$store.state.generatedOrderId
      }
    },
    mounted() {
      this.$store.commit("addToSessionStorage");
      let WebApp = window.Telegram.WebApp;
      const BackButton = WebApp.BackButton;
      const vm = this;
      BackButton.show();
      WebApp.onEvent('backButtonClicked', function() {
        window.location.href = "/products-page/shopping-cart?bot_id=" + vm.$store.state.bot_id;
      });
    },
    methods: {
      orderBtnClicked() {
        const addressInput = document.getElementById('addressInput');
        const paymentMethod = document.getElementById('payment-method')
        const selectedOption = paymentMethod.options[paymentMethod.selectedIndex].value
        if (addressInput.value === '') {
          addressInput.style.border = '1px solid #ff003c';
          addressInput.placeholder = 'Поле адрес не может быть пустым';
          addressInput.classList.add('red-placeholder');
          return
        }
        this.$store.state.paymentMethod = selectedOption;
        this.$store.state.address = this.inputValue;
        this.$store.commit("postData");
        sessionStorage.setItem('itemsAddToCartArray', JSON.stringify([]));
      }
    },
    watch: {
      inputValue(newValue) {
        const addressInput = document.getElementById('addressInput');
        if (newValue === '') {
          addressInput.style.border = '1px solid #ff003c';
          addressInput.placeholder = 'Поле адрес не может быть пустым';
          addressInput.classList.add('red-placeholder');
        } else {
          addressInput.style.border = '';
          addressInput.placeholder = '';
          addressInput.classList.remove('placeholder');
        }
      }
    }
  }
</script>

<template>
  <div class="main-body">
  <div class="title-div">
    <img style="width: 134px; height: 134px; border-radius: 7px;" src="../../assets/logo.png" alt="image">
    <div class="title-text">
      <span style="font-size: 24px; margin-bottom: 15px; line-height: 1.5rem">Заказ №{{orderId}}</span>
      <span style="color: #71CBFF; font-size: 15px; font-weight: 500">Название заказа</span>
    </div>
  </div>

  <div class="address-container">
    <span style="color: #71CBFF;">Адрес доставки</span>
    <textarea placeholder="г. Москва, Большой Строченовский переулок 5" id="addressInput" v-model="inputValue"></textarea>
  </div>

  <div class="pay-container">
    <span style="color: #71CBFF;">Способы оплаты</span>
    <select id="payment-method">
      <option value="card-online">Картой онлайн</option>
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
    padding: 12px 20px;
    align-items: center;
    border: 1px solid #20282C;
    font-family: 'Montserrat', sans-serif;
    font-weight: 500;
    font-size: 15px;
    &:focus {
      outline: none;
    }
  }
}

.red-placeholder::placeholder{
  color: #ff003c;
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
    background-image: url('../../assets/arrow-down.png') !important;
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

@media (max-height: 1000px) {
  .footer {
    margin-top: 10vh;
  }
}
@media (max-height: 700px) {
  .footer {
    margin-top: 0;
  }
  .address-container {
    margin-bottom: 5px;
  }
  .title-div {
    margin-bottom: 5px;
  }
  .btnTotalPrice {
    font-size: 22px;
  }
}

</style>