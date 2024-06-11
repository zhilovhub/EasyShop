<script>
  import { tg } from '@/main.js'
  import router from "@/router/router.js";

  export default {
    name: 'orderDetails',
    data() {
      return {
        townValue: '',
        addressValue: '',
        commentValue: '',
        imageSrc: ''
      }
    },
    computed: {
      itemsAddToCartArray() {
        return this.$store.state.itemsAddToCartArray;
      },
      totalPrice() {
        let price = this.itemsAddToCartArray.reduce((total, item) => total + item.price*item.countInCart, 0);
        if (price <= 0) {
          return '0 ₽'
        }
        const parts = price.toString().split(/(?=(?:\d{3})+$)/);
        return parts.join(' ') + ' ₽';
      },
    },
    methods: {
      orderBtnClicked() {
        const townValue = document.getElementById('townValue');
        const addressValue = document.getElementById('addressValue');
        const commentValue = document.getElementById('commentValue')
        if (townValue.value === '' && addressValue.value === '') {
          townValue.style.border = '1px solid #ff003c';
          townValue.placeholder = 'Поле не может быть пустым';
          townValue.classList.add('red-placeholder');
          addressValue.style.border = '1px solid #ff003c';
          addressValue.placeholder = 'Поле не может быть пустым';
          addressValue.classList.add('red-placeholder');
          return
        }
        if (townValue.value === '') {
          townValue.style.border = '1px solid #ff003c';
          townValue.placeholder = 'Поле не может быть пустым';
          townValue.classList.add('red-placeholder');
          return
        }
        if (addressValue.value === '') {
          addressValue.style.border = '1px solid #ff003c';
          addressValue.placeholder = 'Поле не может быть пустым';
          addressValue.classList.add('red-placeholder');
          return
        }
        this.$store.state.town = this.townValue;
        this.$store.state.address = this.addressValue;
        this.$store.state.comment = this.commentValue;
        this.$store.commit("postData");
      },
      backButtonMethod() {
        router.router.back();
      }
    },
    mounted() {
      tg.BackButton.show();

      tg.MainButton.text = "Заказать";

      tg.onEvent('backButtonClicked', this.backButtonMethod);
      tg.onEvent('mainButtonClicked', this.orderBtnClicked);

      tg.MainButton.show();
    },
    unmounted() {
      tg.offEvent('backButtonClicked', this.backButtonMethod);
      tg.offEvent('mainButtonClicked', this.orderBtnClicked);
    }
  }
</script>

<template>
  <div class="main-body">
    <br>
    <div style="font-size: 20px; font-weight: bold; margin: 0 5%;">Заказ</div>
    <div class="title-div">
    <img style="width: 150px; height: 150px; border-radius: 15px; object-fit: cover;" :src="`${this.$store.state.api_url}/files/` + itemsAddToCartArray[0].picture[0]" alt="image">
    <div class="title-text">
      <div style="display: flex; flex-direction: column">
        <span style="font-size: 20px; font-weight: bold; line-height: 1.5rem">{{ itemsAddToCartArray[0].name }}</span>
<!--        <span style="font-size: 16px;">Краткое описание || {{itemsAddToCartArray[0].description}}</span>-->
      </div>
      <div style="font-size: 20px; font-weight: bold; margin: 15px 15px 15px 0">{{totalPrice}}</div>
    </div>
  </div>

    <hr style="border: 1px solid var(--app-hr-border-color); width: 90%; margin: 2.5% auto;">

  <div class="address-container">
    <span>Город</span>
    <textarea placeholder="г.Москва" id="townValue" v-model="townValue" required></textarea>
  </div>

  <div class="pay-container">
    <span>Адрес доставки</span>
    <textarea placeholder="Дмитровское шоссе, 81" id="addressValue" v-model="addressValue" required></textarea>
    <!--    <select id="payment-method">-->
<!--      <option value="card-online">Картой онлайн</option>-->
<!--    </select>-->
  </div>

  <div class="comment-block">
    <span>Комментарий</span>
    <textarea placeholder="Добавьте комментарий" v-model="commentValue"></textarea>
  </div>
  </div>
<!--  <div class="footer">-->
<!--    <div style="margin: 0 0 10px">-->
<!--      <span style="font-size: 20px; color: #FFFFFF">Итого</span>-->
<!--      <span style="font-size: 20px; color: #FFFFFF">{{totalPrice}}</span>-->
<!--    </div>-->
<!--    <div>-->
<!--      <span>{{totalCount}}</span>-->
<!--      <span>{{totalPrice}}</span>-->
<!--    </div>-->
<!--    <div>-->
<!--      <span>Скидка</span>-->
<!--      <span>0 ₽</span>-->
<!--    </div>-->
<!--    <div>-->
<!--      <span>Доставка</span>-->
<!--      <span>0 ₽</span>-->
<!--    </div>-->
<!--  </div>-->
</template>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 16px;
  line-height: 18.29px;
  color: var(--app-text-color);
}

.main-body {
  position: relative;
}

.title-div {
  background-color: var(--app-background-color);
  width: 100%;
  position: relative;
  left: 0;
  top: 0;
  padding: 2.5% 5%;
  display: flex;
  justify-content: start;
  .title-text {
    max-width: 200px;
    margin-left: 15px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    font-size: 24px;
    font-weight: 600;
  }
}

.address-container {
  background-color: var(--app-background-color);
  display: flex;
  flex-direction: column;
  padding: 5% 5% 0;
  span {
    font-size: var(--app-text-color);
    font-weight: 750;
  }
}

textarea {
  background-color: var(--app-card-background-color);
  width: 100%;
  height: 43px;
  border-radius: 15px;
  display: flex;
  align-items: center;
  margin: 10px auto;
  white-space: pre-wrap;
  resize: none;
  padding: 11px 20px;
  border: 1px solid var(--app-card-background-color);
  font-family: 'Montserrat', sans-serif;
  font-weight: 600;
  font-size: 15px;
  &:focus {
    outline: none;
  }
}

.red-placeholder::placeholder{
  color: #ff003c;
}

.pay-container {
  background-color: var(--app-background-color);
  display: flex;
  flex-direction: column;
  padding: 5% 5% 0;
  span {
    font-size: var(--app-text-color);
    font-weight: 750;
  }
  //select {
  //  width: 100%;
  //  height: 50px;
  //  background-color: #293C47;
  //  border: 1px solid #20282C;
  //  border-radius: 7px;
  //  -webkit-appearance: none;
  //  -moz-appearance: none;
  //  appearance: none;
  //  background-image: url('../../assets/arrow-down.png') !important;
  //  background-position: center right 20px;
  //  background-repeat: no-repeat;
  //  background-size: auto 15%;
  //  padding-left: 20px;
  //  margin: 10px auto;
  //  &:hover, :focus, :active {
  //    outline: none;
  //  }
  //}
}

.comment-block {
  background-color: var(--app-background-color);
  display: flex;
  flex-direction: column;
  padding: 5% 5%;
  span {
    font-size: var(--app-text-color);
    font-weight: 750;
  }
}

//.footer {
//  display: flex;
//  width: 100%;
//  flex-direction: column;
//  position: relative;
//  margin-top: 30vh;
//  padding: 2.5% 5%;
//  div {
//    display: flex;
//    justify-content: space-between;
//    span {
//      margin: 3px;
//      color: #577B8F;
//      font-size: 16px;
//    }
//  }
//}


@media screen and (max-height: 625px) {
  .address-container {
   padding-top: 10px;
  }
  .pay-container {
    padding-top: 10px;
  }
  .comment-block {
    padding-top: 10px;
  }
}

</style>