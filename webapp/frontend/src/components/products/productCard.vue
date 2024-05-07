<template>
  <div>
    <img :src="productObject.picture" alt="main-picture">
    <div class="text">{{productObject.name}}</div>
    <div class="price text">{{priceRub(productObject.price)}}</div>
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
          v-for="size in  productObject.sizes"
          :modules="modules"
          class="size-block"
          @click="chooseSize($event.target)"
        >{{size}}</swiper-slide>
      </swiper>
    </div>
    <div @click="toggleDescription" class="block block-description" :style="{ height: descriptionVisible ? 'auto' : '140px' }">
      <div class="span-block">
        <h1>Описание</h1>
        <img src="@/assets/arrow-down.svg" alt="arrow-down" style="width: 19px; height: 9px; z-index: 10; cursor: pointer">
      </div>
      <span >{{productObject.description}}</span>
    </div>
    <div class="block feedback">
      <div class="span-block">
        <h1>Отзывы</h1>
        <img src="@/assets/arrow-down.svg" alt="arrow-down" style="width: 19px; height: 9px; z-index: 10; cursor: pointer">
      </div>
      <swiper
        :slidesPerView="1.6"
        :spaceBetween="10"
        class="swiper-container">
        <swiper-slide class="feedback-block"></swiper-slide>
        <swiper-slide class="feedback-block"></swiper-slide>
        <swiper-slide class="feedback-block"></swiper-slide>
      </swiper>
    </div>
    <div class="block ranked">
      <div class="span-block">
        <h1>Оценка</h1>
        <img src="@/assets/arrow-down.svg" alt="arrow-down" style="width: 19px; height: 9px; z-index: 10; cursor: pointer">
      </div>
      <span>{{productObject.ranked}}★</span>
    </div>
    <RouterLink :to="`/products-page`"><button @click="addToShoppingCart">Начать оформление</button></RouterLink>
  </div>
</template>

<script>
import { Swiper, SwiperSlide } from '@SwiperVue';
import { Navigation } from '@Swiper'
export default {
  components: { SwiperSlide, Swiper },
  data() {
    return {
      productId: parseInt(this.$route.params.id),
      descriptionVisible: false
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
  font-size: 24px;
  font-weight: bold;
  color: var(--app-text-color);
  padding: 10px 5%;
}

.price {
  font-size: 32px;
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
  min-height: 140px;
  word-wrap: normal;
  overflow-wrap: break-word;
  h1 {
    margin-bottom: 10px;
  }
}

.feedback {
  height: 230px;
  .feedback-block {
    width: 209px;
    height: 166px;
    border-radius: 15px;
    background-color: var(--app-background-color);
  }
}

.ranked {
  height: 90px;
  margin-bottom: 80px;
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