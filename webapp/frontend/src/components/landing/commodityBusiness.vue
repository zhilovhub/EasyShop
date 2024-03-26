<script>
export default {
  data() {
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
        }
      ]
    }
  }
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

    <div class="themes-selector">
      <img src="@/assets/landing/themes/blue-theme-phone.png" alt="blue-theme-phone">
      <img src="@/assets/landing/themes/green-theme-phone.png" alt="green-theme-phone">
      <img src="@/assets/landing/themes/purple-theme-phone.png" alt="purple-theme-phone">
    </div>
    <span class="themes-description">*или закажите индивидуальный дизайн у нас!</span>
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
    <ul class="comment-selector">
      <li
        v-for="comment in comments"
        :key="comment.id"
        class="comment-block"
        style="position: relative;">
        <div class="comment-tile">
          <img src="../../assets/landing/user-logo.png" alt="user-logo">
          <span class="title-text">{{comment.name}}</span>
        </div>
        <div class="comment-text">{{comment.comment}}</div>
      </li>
    </ul>
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
      <span><img src="@/assets/landing/tg.svg" alt="tg">TG - @EzShopOfficial </span>
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
    margin: -150px;
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
  .themes-selector {
    display: flex;
    justify-content: space-around;
    z-index: 1;
    position: relative;
    padding: 50px 100px 25px;
    img {
      width: 30%;
    }
    &::before {
      content: '';
      width: 10%;
      height: 100%;
      background-image: url("@/assets/landing/themes/arrow-left.svg");
      background-repeat: no-repeat;
      background-position: center left;
      position: absolute;
      cursor: pointer;
      left: 0;
      top: 0;
    }
    &::after {
      content: '';
      width: 10%;
      height: 100%;
      background-image: url("@/assets/landing/themes/arrow-right.svg");
      background-repeat: no-repeat;
      background-position: center right;
      position: absolute;
      cursor: pointer;
      right: 0;
      top: 0;
    }
  }
  .themes-description {
    margin: 0 125px;
    color: #4156C0;
    font-size: 40px;
    font-weight: 500;
    font-family: Montserrat, sans-serif;
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
    &:hover, &:active{
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

.wrapper-selector {
  background-color: #E3EAFD;
  padding: 50px 150px 150px;
  .comment-selector {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(33%, 1fr));
    width: 100%;
    position: relative;
    padding-left: 0;
    flex-wrap: nowrap;
    margin-top: 50px;
    &::before {
      content: '';
      width: 10%;
      height: 100%;
      background-image: url("@/assets/landing/themes/arrow-left.svg");
      background-repeat: no-repeat;
      background-position: center left;
      position: absolute;
      cursor: pointer;
      left: -50px;
      top: 0;
      z-index: 1;
    }
    &::after {
      content: '';
      width: 10%;
      height: 100%;
      background-image: url("@/assets/landing/themes/arrow-right.svg");
      background-repeat: no-repeat;
      background-position: center right;
      position: absolute;
      cursor: pointer;
      right: -50px;
      top: 0;
      z-index: 1;
    }
    .comment-block:first-child {
      margin-left: 50px;
    }
    .comment-block:last-child {
      margin-right: 50px;
    }
    .comment-block {
      white-space: nowrap;
      background-color: #F2F6FF;
      list-style-type: none;
      display: flex;
      flex-direction: column;
      justify-content: start;
      border-radius: 50px;
      margin: 0 10px;
      padding: 50px 25px 10px;
      .title-text {
        font-size: 36px;
        font-family: "Exo 2", sans-serif;
        font-weight: 800;
        color: #5D36B8;
        margin-left: 10px;
      }
      .comment-tile {
        display: flex;
        align-items: center;
      }
      .comment-text {
        white-space: normal;
        font-size: 24px;
        font-family: Montserrat, sans-serif;
        font-weight: 400;
        margin: 15px 0;
      }
      img {
        width: 110px;
      }
    }
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
</style>