<script>

</script>

<template>
  <header>
    <svg width="1920" height="343" viewBox="0 0 1920 343" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="39.6416" y="-201.808" width="394.523" height="390.959" rx="43.5" transform="rotate(45 39.6416 -201.808)" stroke="url(#paint0_linear_0_1)" stroke-width="13"/>
      <rect x="302.821" y="-69.636" width="223.296" height="221.264" rx="45.5" transform="rotate(45 302.821 -69.636)" stroke="url(#paint1_linear_0_1)" stroke-width="9"/>
      <rect x="1817.82" y="-108.808" width="219.296" height="217.264" rx="43.5" transform="rotate(45 1817.82 -108.808)" stroke="url(#paint2_linear_0_1)" stroke-width="13"/>
      <rect x="1649.41" y="91.5355" width="94.0274" height="93.1613" rx="17.5" transform="rotate(45 1649.41 91.5355)" stroke="url(#paint3_linear_0_1)" stroke-width="5"/>
      <rect x="497.41" y="123.536" width="94.0274" height="93.1613" rx="17.5" transform="rotate(45 497.41 123.536)" stroke="url(#paint4_linear_0_1)" stroke-width="5"/>
      <rect x="858.913" y="-64.4645" width="137.546" height="136.299" rx="17.5" transform="rotate(45 858.913 -64.4645)" stroke="url(#paint5_linear_0_1)" stroke-width="5"/>
      <defs>
        <linearGradient id="paint0_linear_0_1" x1="243.403" y1="-211" x2="243.403" y2="192.959" gradientUnits="userSpaceOnUse">
          <stop stop-color="#168ECD"/>
          <stop offset="1" stop-color="#8705AB"/>
        </linearGradient>
        <linearGradient id="paint1_linear_0_1" x1="418.969" y1="-76" x2="418.969" y2="154.264" gradientUnits="userSpaceOnUse">
          <stop stop-color="#168ECD"/>
          <stop offset="1" stop-color="#8705AB"/>
        </linearGradient>
        <linearGradient id="paint2_linear_0_1" x1="1933.97" y1="-118" x2="1933.97" y2="112.264" gradientUnits="userSpaceOnUse">
          <stop stop-color="#168ECD"/>
          <stop offset="1" stop-color="#8705AB"/>
        </linearGradient>
        <linearGradient id="paint3_linear_0_1" x1="1698.92" y1="88" x2="1698.92" y2="186.161" gradientUnits="userSpaceOnUse">
          <stop stop-color="#168ECD"/>
          <stop offset="1" stop-color="#8705AB"/>
        </linearGradient>
        <linearGradient id="paint4_linear_0_1" x1="546.924" y1="120" x2="546.924" y2="218.161" gradientUnits="userSpaceOnUse">
          <stop stop-color="#168ECD"/>
          <stop offset="1" stop-color="#8705AB"/>
        </linearGradient>
        <linearGradient id="paint5_linear_0_1" x1="930.186" y1="-68" x2="930.186" y2="73.2988" gradientUnits="userSpaceOnUse">
          <stop stop-color="#168ECD"/>
          <stop offset="1" stop-color="#8705AB"/>
        </linearGradient>
      </defs>
    </svg>
    <img class="phones" src="@/assets/landing/phones.png">
    <div class="title-div">
      <img src="@/assets/landing/logo.svg" alt="logo">
      <div>Ваш магазин в Telegram <br> за 5 минут <br> <span>без программирования</span></div>
      <button>Попробовать <br> <span>бесплатно 7 дней</span></button>
    </div>
  </header>
</template>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 15px;
  line-height: 18.29px;
  color: #FFFFFF;
}

header{
  width: 100vw;
  height: 100vh;
  background-color: #0A1526;
  .title-div {
    display: flex;
    flex-direction: column;
    align-items: baseline;
    position: absolute;
    color: #DBE0E9;
    top: 30%;
    left: 10%;
    max-width: 750px;
    div {
      font-family: 'Montserrat', sans-serif;
      font-size: 55px;
      font-weight: 500;
      line-height: 67px;
      span {
        font-size: 55px;
        font-weight: 800;
        line-height: 67px;
      }
    }
    img {
      width: 750px;
      margin: 10px;
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
}
</style>