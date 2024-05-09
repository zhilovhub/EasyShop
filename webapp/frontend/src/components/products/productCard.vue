<template>
  <div>
    <img :src="productObject.picture" alt="main-picture">
    <div class="text">{{productObject.name}}</div>
    <div class="text">{{priceRub(productObject.price)}}</div>
    <div class="block size">
      <div class="span-block">
        <h1>Размер</h1>
        <span class="src">Размерная сетка</span>
      </div>
      <swiper
        :slidesPerView="4.5"
        :spaceBetween="10"
        class="swiper-container">
        <swiper-slide
          v-for="size in productObject.sizes"
          :modules="modules"
          class="size-block"
          @click="chooseSize($event.target)"
        >{{size}}</swiper-slide>
      </swiper>
    </div>
    <div @click="toggleDescription" class="block block-description" :style="{ height: descriptionVisible ? 'auto' : '70px' }">
      <div class="span-block">
        <h1>Описание</h1>
        <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>
        </svg>
      </div>
      <span v-if="descriptionVisible" >{{productObject.description}}</span>
    </div>
    <div @click="toggleFeedback" class="block feedback" :style="{ height: feedbackVisible ? 'auto' : '70px' }">
      <div class="span-block">
        <h1>Отзывы</h1>
        <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>
        </svg>
      </div>
      <swiper v-if="feedbackVisible"
        :slidesPerView="1.6"
        :spaceBetween="10"
        class="swiper-container">
        <swiper-slide class="feedback-block"></swiper-slide>
        <swiper-slide class="feedback-block"></swiper-slide>
        <swiper-slide class="feedback-block"></swiper-slide>
      </swiper>
    </div>
    <div @click="toggleRanked" class="block ranked" :style="{ height: rankedVisible ? '90px' : '70px' }">
      <div class="span-block">
        <h1>Оценка</h1>
        <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>
        </svg>
      </div>
      <span v-if="rankedVisible">{{productObject.ranked}}★</span>
    </div>
  </div>
</template>

<script>
import { Swiper, SwiperSlide } from '@SwiperVue';
import { Navigation } from '@Swiper'

let tg = window.Telegram.WebApp;
tg.MainButton.text = "Начать оформление";
Telegram.WebApp.onEvent('mainButtonClicked', function(){
  console.log(1);
  console.log(2);
  console.log(3);
});


tg.MainButton.show();

export default {
  components: { SwiperSlide, Swiper },
  data() {
    return {
      productId: parseInt(this.$route.params.id),
      descriptionVisible: false,
      feedbackVisible: false,
      rankedVisible: false,
    }
  },
  setup() {
    return {
      modules: [Navigation],
    };
  },
  computed: {
    productObject() {
      return this.$store.state.items.find(item => item.id === this.productId);
    }
  },
  methods: {
    priceRub(price) {
      const parts = price.toString().split(/(?=(?:\d{3})+$)/);
      return parts.join(' ') + '₽';
    },
    chooseSize(target) {
      const allSizes = document.querySelectorAll('.size-block');
      allSizes.forEach(size => {
        size.classList.remove('chosen');
      });
      target.classList.add('chosen');
    },
    toggleDescription() {
      this.descriptionVisible = !this.descriptionVisible;
    },
    toggleFeedback() {
      this.feedbackVisible = !this.feedbackVisible;
    },
    toggleRanked() {
      this.rankedVisible = !this.rankedVisible;
    },
    addToShoppingCart() {
      this.$store.state.items = this.$store.state.items.map(
        item => item.id === this.productId ? ({ ...item, count: item.count + 1 }) : item);
      this.$store.commit("addToSessionStorage");
    }
  }
};
</script>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 15px;
  font-weight: 500;
  line-height: 18.29px;
  color: var(--app-text-color);
}

img {
  width: 100%;
  height: 280px;
  object-fit: cover;
  border-radius: 0 0 15px 15px;
  z-index: -1;
  display: block;
}
.text {
  font-size: 32px;
  font-weight: bold;
  color: var(--app-text-color);
  padding: 10px 5%;
}

.block {
  background-color: var(--app-card-background-color);
  width: 100%;
  height: 130px;
  border-radius: 15px;
  margin: 20px 0;
  padding: 20px 5%;
  .span-block {
    display: flex;
    justify-content: space-between;
    .src {
      font-size: 14px;
      font-weight: normal;
      color: #2F94CE;
      cursor: pointer;
      &:hover {
        opacity: 0.7;
      }
    }
  }
}

.size {
  margin: 10px 0;
  padding: 0;
  .span-block {
    padding: 20px 5% 10px;
  }
  .swiper-container {
    margin: 0 0 0 5%;
  }
}

.swiper-container {
  margin: 10px 0;
  .size-block {
    background-color: var(--app-background-color);
    width: 75px;
    height: 65px;
    border-radius: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

.chosen {
  border: 3px solid #9EDCFF;
}

h1 {
  font-size: 20px;
  font-weight: bold;
}

.block-description {
  overflow-y: hidden;
  transition: height 0.3s ease;
  min-height: 55px;
  word-wrap: normal;
  overflow-wrap: break-word;
  h1 {
    margin-bottom: 10px;
  }
}

.feedback {
  margin: 10px 0;
  padding: 0 0 5% 0;
  height: 230px;
  .span-block {
    padding: 20px 5% 10px;
  }
  .swiper-container {
    margin: 0 0 0 5%;
  }
  .feedback-block {
    width: 209px;
    height: 166px;
    border-radius: 15px;
    background-color: var(--app-background-color);
  }
}

.ranked {
  min-height: 55px;
  margin-bottom: 40px;
  h1 {
    margin-bottom: 10px;
  }
  span {
    font-size: 20px;
  }
}

button {
  width: 100%;
  height: 62px;
  color: #0C0C0C;
  background-color: #59C0F9;
  position: fixed;
  bottom: 0;
  left: 0;
  cursor: pointer;
  box-shadow: none;
  border: none;
  font-size: 20px;
  font-weight: bold;
  font-family: 'Montserrat', sans-serif;
  z-index: 10;
  &:hover{
    background-color: #82ccec;
  }
}
</style>