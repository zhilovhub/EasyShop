<script>
import CommodityBusiness from './commodityBusiness.vue';
// import ServicesSector from './servicesSector.vue';
export default {
  data() {
    return {
      selectedComponent: 'commodity-business'
    }
  },
  components: {
    CommodityBusiness,
    // ServicesSector
  },
  mounted() {
    document.getElementById('scrollArrow').addEventListener('click', function() {
      document.getElementById('why-tg').scrollIntoView({ behavior: 'smooth' });
    });
  },
  methods: {
    redirectToBot() {
      window.location.href = "https://t.me/ezShopOfficial_bot";
    },
    // Логика для смены компонентов
    // toggle(event, componentName) {
    //   this.selectedComponent = componentName;
    //   const element = event.target;
    //   const elements = document.querySelectorAll('.choosing-for-what div');
    //
    //   elements.forEach(el => {
    //     if (el.classList.contains('isActive')) {
    //       el.classList.remove('isActive');
    //     }
    //   });
    //
    //   element.classList.add('isActive');
    // }
  }
}

</script>

<template>
  <header>
    <img style="position: absolute; top: 0; left: 0; width: 100%" src="@/assets/landing/squares-background.svg" alt="squares-background">
    <img class="phones" src="@/assets/landing/phones.png" alt="phones">
    <div class="title-div">
      <img src="@/assets/landing/logo.svg" alt="logo">
      <div>Ваш магазин в Telegram <br> за 5 минут <br> <span>без программирования</span></div>
      <button @click="redirectToBot">Попробовать <br> <span>бесплатно 7 дней</span></button>
    </div>
    <a id="scrollArrow"><img class="arrow-down" src="@/assets/arrow-down.png" alt="arrow-down-with-animation"></a>
  </header>
  <div id="why-tg" class="why-telegram">
    <span>Почему Telegram?</span>
    <img src="@/assets/landing/why-telegram.svg" alt="why-telegram">
    <button @click="redirectToBot">Открыть новый отдел продаж</button>
  </div>
  <div class="choosing-for-what">
    <div @click="toggle($event, 'commodity-business')" data-text="Для товарного бизнеса" class="isActive">Для товарного бизнеса</div>
<!--    <div @click="toggle($event, 'services-sector')" data-text="Для сферы услуг">Для сферы услуг</div>-->
  </div>
  <component :is="selectedComponent"></component>
</template>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  line-height: 18.29px;
  color: #FFFFFF;
}

header{
  position: relative;
  height: 100vh;
  background-color: #0A1526;
  padding: 0 150px;
  .title-div {
    display: flex;
    flex-direction: column;
    align-items: baseline;
    position: relative;
    color: #DBE0E9;
    top: 50%;
    transform: translateY(-50%);
    max-width: 750vw;
    div {
      font-family: 'Montserrat', sans-serif;
      font-size: 55px;
      font-weight: 500;
      line-height: 67px;
      margin: 20px 0;
      span {
        font-size: 55px;
        font-weight: 800;
        line-height: 67px;
      }
    }
    img {
      width: 750px;
    }
    button {
      font-family: "Exo 2", sans-serif;
      font-weight: 800;
      line-height: 52px;
      font-size: 48px;
      border: none;
      outline: none;
      width: 575px;
      height: 136px;
      margin: 50px 0;
      border-radius: 100px;
      cursor: pointer;
      color: white;
      background: linear-gradient(93.61deg, #8C00AA -0.76%, #02A3D4 100%);
      &:hover, &:active{
        background: linear-gradient(93.61deg, #8C00AA80 -0.76%, #02A3D480 100%)
      }
      span {
        font-family: "Exo 2", sans-serif;
        font-weight: 700;
        font-size: 32px;
      }
    }
  }
  .phones {
    width: 40%;
    position: absolute;
    right: 5%;
    top: 10%;
  }
  .arrow-down {
    position: absolute;
    cursor: pointer;
    right: 47.5%;
    top: 95vh;
    animation: moveArrow 1s alternate-reverse infinite;
  }
}

@keyframes moveArrow {
  from{
    transform: translateY(-20px);
  }
  to{
    transform: translateY(0);
  }
}

.why-telegram {
  background-color: #FFFFFF;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-around;
  padding: 0 150px;
  span {
    color: transparent;
    -webkit-background-clip: text;
    font-size: 96px;
    line-height: 116px;
    font-family: "Exo 2", sans-serif;
    font-weight: 800;
    background-clip: text;
    margin: 50px 0;
    background-image: linear-gradient(89.57deg, #810CAD -0.55%, #0C96D1 68.69%);
  }
  img {
    width: 80%;
    margin: 50px 0;
  }
  button {
    border: none;
    outline: none;
    width: 55%;
    height: 136px;
    border-radius: 100px;
    cursor: pointer;
    color: white;
    margin: 50px 0;
    font-family: "Exo 2", sans-serif;
    font-weight: 800;
    line-height: 52px;
    font-size: 48px;
    background: linear-gradient(93.61deg, #8C00AA -0.76%, #02A3D4 100%);
    &:hover, &:active{
      background: linear-gradient(93.61deg, #8C00AA80 -0.76%, #02A3D480 100%)
    }
  }
}

.choosing-for-what {
  //display: grid;
  //grid-template-columns: repeat(auto-fill, minmax(50%, 2fr));
  //justify-content: space-around;
  font-family: "Exo 2", sans-serif;
  font-weight: 800;
  font-size: 48px;
  line-height: 58px;
  background-color: white;
  padding-top: 100px;
  div {
    width: 100%;
    padding-top: 50px;
    text-align: center;
    position: relative;
    z-index: 1;
    border-bottom: 25px solid;
    cursor: pointer;
    height: 175px;
    border-image: linear-gradient(89.92deg, rgba(128, 13, 173, 0.3) 0%, rgba(13, 149, 208, 0.3) 100%);
    border-image-slice: 1;
    font-family: "Exo 2", sans-serif;
    font-weight: 800;
    font-size: 48px;
    line-height: 58px;
    background: linear-gradient(89.57deg, #810CAD -0.55%, #0C96D1 68.69%);
    color: transparent;
    -webkit-background-clip: text;
    background-clip: text;
    &:not(.isActive)::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: #E3EAFD4D;
    }
  }
  .isActive {
    z-index: 1;
    background: #E3EAFD;
    border-image: linear-gradient(89.92deg, #800DAD 0%, #0D95D0 100%);
    border-image-slice: 1;
    color: transparent;
    //не удалять
    &::before {
      font-weight: 800;
      padding-top: 50px;
      content: attr(data-text);
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: -1;
      /* Применяем градиент к тексту */
      background: linear-gradient(89.57deg, #810CAD -0.55%, #0C96D1 68.69%);
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
    }
  }
}

@media screen and (max-width: 1600px) {
  header {
    .title-div {
      max-width: 50%;
      div {
        font-size: 40px;
        span {
          font-size: 36px;
          font-weight: 800;
          line-height: 67px;
        }
      }
      img {
        width: 75%;
      }
      button {
        line-height: 26px;
        margin: 0;
        font-size: 26px;
        width: 75%;
        height: 130px;
      }
    }
  }
  .why-telegram {
    button {
      line-height: 36px;
      font-size: 36px;
    }
  }
}

@media screen and (max-width: 1200px) {
  header {
    .title-div {
      max-width: 37.5%;
      div {
        margin: 10px 0;
        font-size: 24px;
        line-height: 40px;
        span {
          font-size: 36px;
          font-weight: 800;
          line-height: 40px;
        }
      }
      img {
        width: 75%;
      }
      button {
        margin: 0;
        font-size: 24px;
        width: 100%;
        height: 100px;
      }
    }
  }
  .choosing-for-what {
    div {
      border-bottom: 15px solid;
    }
  }
  .why-telegram {
    button {
      line-height: 32px;
      font-size: 32px;
    }
  }
}
</style>