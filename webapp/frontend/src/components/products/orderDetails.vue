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
        phoneNumber: '',
        nameValue: '',
        timeValue: '',
        imageSrc: '',
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
        const commentValue = document.getElementById('commentValue');
        const nameValue = document.getElementById('nameValue');
        const phoneValue = document.getElementById('phoneNumberValue');

        const validateField = (field) => {
          if (field.value === '') {
            field.style.border = '1px solid #ff003c';
            field.placeholder = 'Поле не может быть пустым';
            field.classList.add('red-placeholder');
            return false;
          }
          return true;
        };

        const isTownValid = validateField(townValue);
        const isAddressValid = validateField(addressValue);
        const isNameValid = validateField(nameValue);
        const isPhoneValueValid = validateField(phoneValue);
        if (!isTownValid || !isAddressValid || !isNameValid || !isPhoneValueValid) {
          return;
        }

        this.$store.state.town = townValue.value;
        this.$store.state.address = addressValue.value;
        this.$store.state.comment = commentValue.value;
        this.$store.state.name = nameValue.value;
        this.$store.state.phoneNumber = phoneValue.value;
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
      <img v-if="itemsAddToCartArray[0].picture && itemsAddToCartArray[0].picture[0]" style="width: 150px; height: 150px; border-radius: 15px; object-fit: cover;" :src="`${this.$store.state.api_url}/files/` + itemsAddToCartArray[0].picture[0]" alt="image">
      <img style="width: 150px; height: 150px; border-radius: 15px; object-fit: cover;" v-else src="@/assets/productArt.png" alt="img">
      <div class="title-text">
      <div style="display: flex; flex-direction: column">
        <span style="font-size: 20px; font-weight: bold; line-height: 1.5rem">{{ itemsAddToCartArray[0].name }}</span>
<!--        <span style="font-size: 16px;">Краткое описание || {{itemsAddToCartArray[0].description}}</span>-->
      </div>
      <div style="font-size: 20px; font-weight: bold; margin: 15px 15px 15px 0">{{totalPrice}}</div>
    </div>
  </div>

    <hr style="border: 1px solid var(--app-hr-border-color); width: 90%; margin: 2.5% auto;">

    <div class="input-container">
      <span>Ваше имя</span>
      <textarea placeholder="Иванов Иван" id="nameValue" v-model="nameValue" required></textarea>
    </div>

    <div class="input-container">
      <span>Номер телефона</span>
      <textarea placeholder="Номер телефона" id="phoneNumberValue" v-model="phoneNumber" required></textarea>
    </div>

    <div class="input-container">
      <span>Город</span>
      <textarea placeholder="г.Москва" id="townValue" v-model="townValue" required></textarea>
    </div>

    <div class="input-container">
      <span>Адрес доставки</span>
      <textarea placeholder="Дмитровское шоссе, 81" id="addressValue" v-model="addressValue" required></textarea>
    </div>

    <div class="input-container">
      <span>Время</span>
      <textarea placeholder="Предпочтения по времени доставки" v-model="timeValue"></textarea>
    </div>

    <div class="input-container">
      <span>Комментарий</span>
      <textarea placeholder="Добавьте комментарий" v-model="commentValue"></textarea>
    </div>
  </div>
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

.input-container {
  background-color: var(--app-background-color);
  display: flex;
  flex-direction: column;
  padding: 5% 5% 0;
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
  .input-container {
   padding-top: 10px;
  }
}
</style>