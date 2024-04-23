<script>
// Import Swiper Vue.js components
import { Swiper, SwiperSlide } from '@SwiperVue';
import { Navigation } from '@Swiper'

export default {
  data () {
    return {
      comments: [
        {
          name: 'Иван',
          comment: 'Впечатлен конструктором EzShop! Он удобен и легок в использовании. Особенно удобно, что можно делать покупки и заказывать услуги прямо в мессенджере. Спасибо за такой замечательный сервис, который делает жизнь проще, а коммуникацию с клиентом более удобной!',
          id: 1
        },
        {
          name: 'Мария',
          comment: 'Очень довольна работой магазина внутри Телеграм, который был создан в конструкторе Ezshop. Удобно выбирать и заказывать товары, быстрая обработка заказов. Спасибо за качественный продукт! ',
          id: 2
        },
        {
          name: 'Дмитрий',
          comment: 'Я рад поделиться положительным отзывом о сервисе Ezshop! Этот конструктор стал для меня незаменимым инструментом для развития моего магазина. Благодарю команду за отличный продукт, который делает мой бизнес более продвинутым и уникальным!',
          id: 3
        },
        {
          name: 'Саша',
          comment: 'Я рад поделиться положительным отзывом о сервисе Ezshop! Этот конструктор стал для меня незаменимым инструментом для развития моего магазина. Благодарю команду за отличный продукт, который делает мой бизнес более продвинутым и уникальным!',
          id: 4
        }
      ]
    }
  },
  components: {
    Swiper,
    SwiperSlide,
  },
  setup() {
    return {
      modules: [Navigation],
    };
  },
}
</script>

<template>
  <div class="main">
    <div class="block">
      <div class="text-block">
        <span class="gradient">Продажа в 2 касания</span>
        <span>Ваш клиент сможет оформить заказ
          за 15 секунд, не выходя из Telegram!</span>
      </div>
      <img style="position: relative; right: 0" src="@/assets/landing/arm.svg">
    </div>

    <img class="arrow" src="@/assets/landing/arrow-right-down.svg" alt="arrow">

    <div style="padding-right: 150px" class="block">
      <img style="position: relative; right: 0" src="@/assets/landing/puzzles.svg" alt="puzzles">
      <div style="width: 50vw; text-align: right" class="text-block">
        <span class="gradient">Повышайте вовлеченность и возвращаемость</span>
        <span>Рассылки - напоминания о скидках и подарках,
а также встроенная система бонусов для клиентов</span>
      </div>
    </div>

    <img class="arrow" src="@/assets/landing/arrow-left-down.svg" alt="arrow">

    <div class="block">
      <div class="text-block">
        <span class="gradient">Создайте уникальный бренд</span>
        <span>Магазин через Telegram в web-app позволяет выгодно выделить ваш бизнес среди конкурентов!</span>
      </div>
      <img src="@/assets/landing/man-with-brand.svg" alt="man-with-brand">
    </div>

    <img style="margin: 0" class="arrow" src="@/assets/landing/arrow-right-down.svg" alt="arrow">

    <div class="block">
      <img src="@/assets/landing/arm-with-money.svg" alt="arm-with-money">
      <div class="text-block">
        <span class="gradient">Максимизируйте объем продаж</span>
        <span>Конверсия в 9.8 раз больше, чем через магазин в браузере!</span>
      </div>
    </div>
  </div>

  <div class="custom">
    <div class="custom-text">
      <span class="gradient">Кастомизация</span>
      <span class="custom-description">Выберите дизайн, который подходит для вашего бизнеса*</span>
    </div>

    <div class="swiper-container">
      <swiper
        :slidesPerView="3"
        :spaceBetween="50"
        :navigation="{
          prevEl: '.swiper-button-prev',
          nextEl: '.swiper-button-next'
        }"
        :breakpoints="{
        '1024': {
          slidesPerView: 3,
          spaceBetween: 40
      },
        '768': {
          slidesPerView: 3,
          spaceBetween: 30
      },
        '640': {
          slidesPerView: 2,
          spaceBetween: 20
      },
        '320': {
          slidesPerView: 1,
          spaceBetween: 10
        }
      }"
        :modules="modules"
        class="themes-selector">
        <swiper-slide><img src="@/assets/landing/themes/blue-theme-phone.png" alt="blue-phone" draggable="false"></swiper-slide>
        <swiper-slide><img src="@/assets/landing/themes/green-theme-phone.png" alt="green-phone" draggable="false"></swiper-slide>
        <swiper-slide><img src="@/assets/landing/themes/purple-theme-phone.png" alt="purple-phone" draggable="false"></swiper-slide>
        <swiper-slide><img src="@/assets/landing/themes/purple-theme-phone.png" alt="purple-phone" draggable="false"></swiper-slide>
      </swiper>
      <div class="swiper-button-prev"><img src="@/assets/landing/themes/arrow-left.png" draggable="false" alt="arrow-left"></div>
      <div class="swiper-button-next"><img src="@/assets/landing/themes/arrow-right.png" draggable="false" alt="arrow-right"></div>
    </div>
    <div class="themes-description">
      <div class="text-wrapper">
        <span>*или закажите индивидуальный дизайн у нас!</span>
      </div>
    </div>
  </div>

  <div class="button-selector">
    <button>Попробовать сейчас</button>
    <span>7 дней бесплатно без ввода карточки!</span>
  </div>

  <div class="additionally">
    <span class="gradient">Дополнительные <br> преумущества:</span>
    <img src="@/assets/landing/additional-benefits.svg" alt="additional-benefits">
    <span class="gradient">Появится очень скоро:</span>
    <img src="@/assets/landing/coming-soon.svg" alt="coming-soon">
    <span class="gradient"> Планируется:</span>
    <img src="@/assets/landing/planned.svg" alt="coming-soon">
  </div>

  <div class="wrapper-selector">
    <span class="gradient">Отзывы</span>
    <div class="swiper-container">
      <swiper
        :slidesPerView="3"
        :spaceBetween="30"
        :navigation="{
          prevEl: '.swiper-button-prev',
          nextEl: '.swiper-button-next'
      }"
        :breakpoints="{
        '1400': {
          slidesPerView: 3,
          spaceBetween: 10
      },
        '768': {
          slidesPerView: 3,
          spaceBetween: 20
      },
        '640': {
          slidesPerView: 2,
          spaceBetween: 10
      },
        '320': {
          slidesPerView: 1,
          spaceBetween: 10
        }
      }"
        :modules="modules"
        class="themes-selector">
        <swiper-slide
          v-for="comment in comments"
          :key="comment.id"
          class="comment-block"
        >
          <div class="comment-title">
            <img src="../../assets/landing/comments/user-logo.png" alt="user-logo">
            <span class="title-text">{{comment.name}}</span>
          </div>
          <div class="comment-text">{{comment.comment}}</div>
        </swiper-slide>
      </swiper>
      <div class="swiper-button-prev"><img src="@/assets/landing/themes/arrow-left.png" alt="arrow-left"></div>
      <div class="swiper-button-next"><img src="@/assets/landing/themes/arrow-right.png" alt="arrow-right"></div>
    </div>
  </div>

  <div class="tariffs">
    <span class="gradient">Тарифы</span>
    <span class="tariffs-description">Бесплатно 7 дней, а затем по доступной цене индивидуально для вас!</span>
    <img style="margin: 50px 0" src="@/assets/landing/tariffs.svg" alt="tariffs">
  </div>

  <footer>
    <div class="wrapper-contacts">
      <img src="@/assets/landing/revert-logo.svg" alt="revert-logo">
      <span>Контакты</span>
      <div style="margin: 25px 0">
        <span><img src="@/assets/landing/tg.svg" alt="tg">TG - @<a href="https://t.me/EzShopOfficial">EzShopOfficial</a></span>
        <span><img src="@/assets/landing/mail.svg" alt="mail">Почта - EzShopMax398@ya.ru</span>
      </div>
    </div>
    <div class="licensor">
      <span>© 2024, EzShop</span>
      <span>Использованы ресурсы Freepik</span>
    </div>
  </footer>
</template>

<style scoped lang="scss">
.main {
  padding: 150px 0;
  background-color: #E3EAFD;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
  align-items: center;

  .arrow {
    margin: -75px;
  }
}

.block {
  width: 100%;
  display: flex;
  justify-content: space-between;

  .text-block:nth-child(even) {
    text-align: right;
  }

  .text-block:nth-child(odd) {
    text-align: left;
  }

  .text-block {
    white-space: normal; /* or break-spaces */
    display: flex;
    flex-direction: column;
    width: 45vw;
    overflow-wrap: break-word;

    .gradient {
      color: transparent;
      -webkit-background-clip: text;
      font-size: 96px;
      line-height: 116px;
      font-family: "Exo 2", sans-serif;
      font-weight: 800;
      background-clip: text;
      background-image: linear-gradient(89.57deg, #810CAD -0.55%, #0C96D1 68.69%);
      padding-bottom: 50px;
    }

    span {
      font-family: Montserrat, sans-serif;
      font-size: 48px;
      font-weight: 500;
      line-height: 58px;
      color: #0A1526;
    }

    span:first-child {
      padding-top: 150px;
    }
  }
}

.block:first-child {
  padding-left: 150px;

  .text-block {
    padding-top: 50px;
  }

  margin-bottom: -250px;
}

.block:not(:first-child) {
  padding: 0 100px;
}

.custom {
  background-color: #E3EAFD;
  padding: 150px;

  .custom-text {
    display: flex;
    flex-direction: column;
    width: 50vw;

    .custom-description {
      color: #7A14AF;
      font-weight: 500;
      font-size: 48px;
      font-family: Montserrat, sans-serif;
    }
  }

  .themes-description {
    max-width: 100%;
    margin: 0 auto;
    color: #4156C0;
    font-size: 40px;
    font-weight: 500;
    font-family: Montserrat, sans-serif;
  }

  .text-wrapper {
    padding-left: 125px;
  }
}

.button-selector {
  background-color: #E3EAFD;
  padding: 0 150px 150px;
  display: flex;
  flex-direction: column;
  align-items: center;

  button {
    font-family: "Exo 2", sans-serif;
    font-weight: 800;
    line-height: 52px;
    font-size: 48px;
    border: none;
    outline: none;
    width: 55%;
    height: 136px;
    border-radius: 100px;
    cursor: pointer;
    color: white;
    margin: 50px 0;
    background: linear-gradient(93.61deg, #8C00AA -0.76%, #02A3D4 100%);

    &:hover, &:active {
      background: linear-gradient(93.61deg, #8C00AA80 -0.76%, #02A3D480 100%)
    }
  }

  span {
    max-width: 400px;
    font-family: Montserrat, sans-serif;
    font-weight: 400;
    font-size: 36px;
    line-height: 44px;
    color: #3D5DC2;
    text-align: center;
  }
}

.additionally {
  background-color: #FFFFFF;
  padding: 150px;

  .gradient {
    color: transparent;
    -webkit-background-clip: text;
    font-size: 96px;
    line-height: 116px;
    font-family: "Exo 2", sans-serif;
    font-weight: 800;
    background-clip: text;
    background-image: linear-gradient(89.57deg, #810CAD -0.55%, #0C96D1 68.69%);
  }

  img {
    display: block;
    margin: 75px auto;
  }
}

.gradient {
  color: transparent;
  -webkit-background-clip: text;
  font-size: 96px;
  font-family: "Exo 2", sans-serif;
  font-weight: 800;
  background-clip: text;
  background-image: linear-gradient(89.57deg, #810CAD -0.55%, #0C96D1 68.69%);
}

.tariffs {
  background-color: #FFFFFF;
  padding: 50px 150px;

  .tariffs-description {
    display: block;
    font-family: Montserrat, sans-serif;
    font-weight: 700;
    font-size: 48px;
    color: #7A14AF;
  }
}

footer {
  padding: 50px 150px 150px;
  max-width: 100%;
  background-color: #0A1526;
  position: relative;

  span {
    display: block;
    color: #ACBBD5;
    font-family: Montserrat, sans-serif;
    font-size: 40px;
    font-weight: 700;
    a {
      color: #ACBBD5;
      font-weight: 700;
    }
    img {
      margin-right: 15px;
    }
  }

  .licensor {
    position: absolute;
    bottom: 50px;
    right: 150px;
    left: 150px;
    display: flex;
    justify-content: space-between;
    align-items: center;

    span {
      font-size: 32px;
      font-weight: 500;
    }
  }
}


.swiper-container {
  position: relative;
  width: 95%;
  margin: 50px 75px 0;

  .swiper {
    width: 95%;
    height: 95%;

    .swiper-slide {
      text-align: center;
      display: flex;
      justify-content: center;
      align-items: center;

      img {
        display: block;
        width: 100%;
      }
    }
  }

  .swiper-button-prev {
    width: 84px;
    left: -75px;
  }

  .swiper-button-next {
    width: 84px;
    right: -75px;
  }

  .swiper-button-prev::after, .swiper-button-next::after {
    content: '';
  }
}

.wrapper-selector {
  background-color: #E3EAFD;
  padding: 50px 150px 150px;
  .swiper-container {
    width: 100%;
    .swiper-button-prev {
      width: 84px;
      left: -75px;
    }
    .swiper-button-next {
      width: 84px;
      right: -75px;
    }
    .swiper {
      width: 100%;
      .comment-block {
        display: flex;
        flex-direction: column;
        max-width: 570px;
        height: 570px;
        background-color: #F2F6FF;
        border-radius: 50px;
        white-space: nowrap;
        list-style-type: none;
        justify-content: start;
        padding: 50px 25px 10px;
        .comment-title {
          display: flex;
          flex-direction: row;
          align-items: center;
          width: 100%;
          text-align: left;

          .title-text {
            font-size: 36px;
            font-family: "Exo 2", sans-serif;
            font-weight: 800;
            color: #5D36B8;
            margin-left: 10px;
          }
        }

        .comment-text {
          text-align: left;
          white-space: normal;
          font-size: 24px;
          font-family: Montserrat, sans-serif;
          font-weight: 400;
          margin: 30px 0;
        }

        img {
          width: 110px;
        }
      }
    }
  }
}

img {
  max-width: 100%;
  user-drag: none;
  -webkit-user-drag: none;
  user-select: none;
  -moz-user-select: none;
  -webkit-user-select: none;
  -ms-user-select: none;
}

@media screen and (max-width: 1400px) {
  .block {
    .text-block {
      .gradient {
        font-size: 72px;
        line-height: 72px;
      }
      span {
        font-size: 36px;
      }
    }
    img {
      max-width: 50%;
    }
    margin: 50px 0;
  }
  main{
    .arrow {
      max-width: 300px;
      margin: -75px;
    }
  }
  .arrow {
    max-width: 300px;
    margin: -75px;
  }
  .block:first-child {
    margin-bottom: 0;
  }
  .block:nth-child(2) {
    margin: 100px 0;
  }
  .custom {
    padding: 50px 150px;
    .custom-text {
      .custom-description {
        font-size: 32px;
      }
    }
    .text-wrapper {
      font-size: 28px;
    }
  }
  .tariffs {
    .tariffs-description {
      font-size: 36px;
    }
  }
  .additionally {
    .gradient {
      font-size: 72px;
    }
  }
  .gradient {
    font-size: 72px;
  }
  .wrapper-selector .swiper-container {
    margin: 50px 40px 0;
    .swiper{
      .comment-block {
        padding: 25px 15px 10px;
        .comment-title {
          .title-text {
            font-size: 32px;
            font-family: "Exo 2", sans-serif;
            font-weight: 800;
            color: #5D36B8;
          }
        }
        .comment-text {
          font-size: 19px;
          margin: 30px 0;
        }
        img {
          width: 96px;
        }
      }
    }
  }
}

@media screen and (max-width: 1200px) {
  .main {
    padding: 0;
  }
  .block {
    .text-block {
      .gradient {
        font-size: 58px;
        line-height: 58px;
      }
      span {
        font-size: 24px;
        line-height: 24px;
      }
    }
    img {
      max-width: 50%;
    }
    margin: 50px 0;
  }
  main{
    .arrow {
      max-width: 175px;
      margin: -75px;
    }
  }
  .arrow {
    max-width: 175px;
    margin: -75px;
  }
  .swiper-container {
    width: 95%;
    margin: 50px 40px 0;

    .swiper-button-prev {
      left: -60px;
    }

    .swiper-button-next {
      right: -60px;
    }
  }
  .custom {
    .text-wrapper {
      padding-left: 60px;
    }
  }
  .button-selector {
    button {
      font-size: 32px;
      line-height: 32px;
    }
  }
  .additionally {
    padding: 50px 150px;
    .gradient {
      font-size: 64px;
      line-height: 64px;
    }
  }
  .gradient {
    font-size: 64px;
    line-height: 64px;
  }
  .tariffs {
    .tariffs-description {
      font-size: 32px;
    }
  }
  .custom {
    padding: 0 150px;
  }
  .button-selector {
    padding: 50px 150px;
  }
  .wrapper-selector .swiper-container {
    margin: 40px 30px 0;
    .swiper{
      .comment-block {
        padding: 25px 15px 10px;
        .comment-title {
          .title-text {
            font-size: 24px;
            font-family: "Exo 2", sans-serif;
            font-weight: 800;
            color: #5D36B8;
          }
        }
        .comment-text {
          font-size: 16px;
          margin: 30px 0;
        }
        img {
          width: 72px;
        }
      }
    }
  }
}
</style>