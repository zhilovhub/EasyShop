<template>
  <div>
    <swiper v-if="productObject?.picture && productObject.picture[0]"
      :slidesPerView="1"
      :modules="modules"
      :navigation="true"
      style="margin: 0"
    >
      <swiper-slide
        v-for="(picture, index) in productObject.picture">
        <img :src="`${this.apiUrl()}/files/get_file/` + (productObject.picture ? productObject.picture[index] : null)" alt="main-picture">
      </swiper-slide>
    </swiper>
    <div class="text">{{productObject?.name}}</div>
    <div class="text">{{priceRub(productObject.price)}}</div>
    <div v-for="(option, type) in productObject?.extra_options">
      <div @click="toggleOption(option)" v-if="option.type === 'block'" class="block extra-options" :style="{ height: option.isSelected ? 'auto' : 'auto' }">
        <div class="span-block">
          <h1>{{option.name}}</h1>
          <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>
          </svg>
        </div>
        <swiper
          :slidesPerView="4.5"
          :spaceBetween="10"
          class="swiper-container"
          v-show="option.isSelected"
        >
          <swiper-slide
            v-for="(value, key) in option.variants"
            :key="key"
            :modules="modules"
            class="option-block"
            @click="chooseOption($event.target)"
            @click.stop
          >
          {{ value }}
        </swiper-slide>
      </swiper>
    </div>
      <div @click="toggleOption(option)" v-else-if="option.type === 'text'" class="block" style="height: auto">
        <div class="span-block">
          <h1 style="margin-bottom: 10px">{{option.name}}</h1>
          <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>
          </svg>
        </div>
        <div v-show="option.isSelected">
          <span>{{option.variants[0]}}</span>
        </div>
      </div>
      <div @click="toggleOption(option)" v-else-if="option.type === 'priced_block'" class="block extra-options" :style="{ height: option.isSelected ? 'auto' : 'auto' }">
        <div class="span-block">
          <h1>{{option.name}}</h1>
          <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
            <path d="M19Z" fill="currentColor"/>
          </svg>
        </div>
        <swiper
          :slidesPerView="4.5"
          :spaceBetween="10"
          class="swiper-container"
          v-show="option.isSelected"
        >
          <swiper-slide
            v-for="(value, key) in option.variants"
            :key="key"
            :modules="modules"
            class="option-block"
            @click="chooseOption($event.target, key)"
            @click.stop
            style="background-color: var(--app-card-background-color); height: 120px"
          >
            <div class="priced_block">
              <div style="background-color: var(--app-background-color); height: 64px; width: 75px; border-radius: 15px; display: flex; justify-content: center; align-items: center">
                <span>{{ value }}</span>
              </div>
              <div style="background-color: var(--app-background-color); height: 42px; width: 75px; border-radius: 15px; margin-top: 5px; display: flex; justify-content: center; align-items: center">
                <span>{{ option.variants_prices[key] }}₽</span>
              </div>
            </div>
          </swiper-slide>
        </swiper>
      </div>

    </div>
  <div v-if="productObject.description && productObject.description.length>0" @click="toggleDescription" class="block block-description" :style="{ height: descriptionVisible ? 'auto' : '68.27px' }">
    <div class="span-block">
      <h1>Описание</h1>
      <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>
      </svg>
    </div>
    <span v-if="descriptionVisible" >{{productObject.description}}</span>
  </div>
<!--  <div @click="toggleFeedback" class="block feedback" :style="{ height: feedbackVisible ? 'auto' : '70px' }">-->
<!--    <div class="span-block">-->
<!--      <h1>Отзывы</h1>-->
<!--      <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">-->
<!--        <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>-->
<!--      </svg>-->
<!--    </div>-->
<!--    <swiper v-if="feedbackVisible"-->
<!--            :slidesPerView="1.6"-->
<!--            :spaceBetween="10"-->
<!--            class="swiper-container">-->
<!--      <swiper-slide class="feedback-block"></swiper-slide>-->
<!--      <swiper-slide class="feedback-block"></swiper-slide>-->
<!--      <swiper-slide class="feedback-block"></swiper-slide>-->
<!--    </swiper>-->
<!--  </div>-->
<!--  <div @click="toggleRanked" class="block ranked" :style="{ height: rankedVisible ? '90px' : '70px' }">-->
<!--    <div class="span-block">-->
<!--      <h1>Оценка</h1>-->
<!--      <svg style="cursor: pointer" width="19" height="9" viewBox="0 0 19 9" fill="currentColor" xmlns="http://www.w3.org/2000/svg">-->
<!--        <path d="M19.0032 0.796349C19.0038 0.900537 18.9839 1.00382 18.9445 1.10028C18.9051 1.19673 18.847 1.28446 18.7737 1.35843L12.3057 7.82635C11.938 8.19497 11.5012 8.48744 11.0203 8.68699C10.5394 8.88654 10.0239 8.98926 9.50324 8.98926C8.98258 8.98926 8.46704 8.88654 7.98614 8.68699C7.50524 8.48744 7.06843 8.19497 6.70074 7.82635L0.232823 1.35843C0.159009 1.28462 0.100456 1.19699 0.0605087 1.10055C0.0205609 1.0041 9.72324e-08 0.900737 9.76995e-08 0.796349C9.81665e-08 0.691959 0.0205609 0.588593 0.0605087 0.492151C0.100456 0.395709 0.159009 0.30808 0.232823 0.234265C0.306636 0.160452 0.394266 0.101898 0.490709 0.0619507C0.587151 0.0220032 0.690517 0.00144292 0.794906 0.00144292C0.899294 0.00144292 1.00266 0.0220032 1.0991 0.0619507C1.19555 0.101898 1.28318 0.160452 1.35699 0.234265L7.82491 6.70218C8.27022 7.14694 8.87386 7.39676 9.50324 7.39676C10.1326 7.39676 10.7363 7.14694 11.1816 6.70218L17.6495 0.234266C17.7231 0.160064 17.8106 0.101168 17.9071 0.0609753C18.0036 0.0207836 18.1071 9.17687e-05 18.2116 9.17699e-05C18.3161 9.17712e-05 18.4196 0.0207836 18.516 0.0609753C18.6125 0.101168 18.7001 0.160064 18.7737 0.234266C18.847 0.308239 18.9051 0.395968 18.9445 0.492422C18.9839 0.588877 19.0038 0.69216 19.0032 0.796349Z" fill="currentColor"/>-->
<!--      </svg>-->
<!--    </div>-->
<!--    <span v-if="rankedVisible">{{productObject.ranked}}★</span>-->
<!--  </div>-->
</div>
</template>

<script>
import { Swiper, SwiperSlide } from '@SwiperVue';
import { Navigation } from '@Swiper'
import { tg } from '@/main.js'
import router from "@/router/router.js";

export default {
  components: { SwiperSlide, Swiper },
  data() {
    return {
      productObject: {},
      productId: parseInt(this.$route.params.id),
      descriptionVisible: true,
      feedbackVisible: true,
      rankedVisible: true,
    }
  },
  setup() {
    console.log("tg", tg)
    return {
      modules: [Navigation],
    };
  },
  methods: {
    apiUrl() {
      return this.$store.state.api_url;
    },
    priceRub(price) {
      if (!price) {
        return
      }
      const parts = price.toString().split(/(?=(?:\d{3})+$)/);
      return parts.join(' ') + '₽';
    },
    chooseOption(target, key) {
      // Ищем родительский элемент с классом 'option-block'
      while (target && !target.classList.contains('option-block')) {
        target = target.parentElement;
      }

      if (!target) return;

      // Удаляем класс 'chosen' у всех опций
      const allOptions = document.querySelectorAll('.option-block');
      allOptions.forEach(option => option.classList.remove('chosen'));

      target.classList.add('chosen');

      if (!this.productObject.chosenOption) {
        this.productObject.chosenOption = [];
      }

      const selectedText = target.innerText.split('\n')[0].trim();
      let optionName = null;
      for (let option of this.productObject.extra_options) {
        if (option.variants.includes(selectedText)) {
          optionName = option.name;
          break;
        }
      }

      if (optionName) {
        this.productObject.chosenOption.push({name: optionName, selected_variant: target.innerText.split("\n")[0]});
      }

      if (this.productObject.extra_options[0].variants_prices[key]) {
        this.productObject.price = this.productObject.extra_options[0].variants_prices[key];
      }
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
      if (this.productObject.extra_options.length > 0 && this.productObject.chosenOption) {
        // return  TODO raise window that user need choose an option
      }

      let matchingItem = this.$store.state.items.find(item => item.id === this.productId);
      matchingItem.countInCart += 1

      let matchingItemInCartArrayIndex = this.$store.state.itemsAddToCartArray.findIndex(
          item => item.id === matchingItem.id
      )

      if (matchingItemInCartArrayIndex !== -1) {
        this.$store.state.itemsAddToCartArray[matchingItemInCartArrayIndex] = matchingItem
      } else {
        this.$store.state.itemsAddToCartArray.push(matchingItem)
      }

      router.router.replace({ name: router.PRODUCTS_PAGE, query: { bot_id: this.$store.state.bot_id }});
    },
    backButtonMethod() {
      router.router.replace({ name: router.PRODUCTS_PAGE, query: { bot_id: this.$store.state.bot_id }});
    },
    setFirstOptionChosen() {
      let firstOption = document.querySelector('.option-block');
      if (firstOption) {
        firstOption.classList.add('chosen');
      }
      if (this.productObject.extra_options) {
        const firstKey = Object.keys(this.productObject.extra_options)[0];
        const firstInnerKey = Object.keys(this.productObject.extra_options[firstKey])[0];
      }
    },
    toggleOption(option) {
      option.isSelected = !option.isSelected;
    }
  },
  mounted() {
    this.$store.dispatch('itemsInit', false);
    this.$store.dispatch('getProduct',  {
      productId: this.productId,
      botId: this.$store.state.bot_id
    }).then((item) => {
      this.productObject = item;
    });
    tg.BackButton.show();  // показываем всегда самой первой строчкой
    if (this.productObject.extra_options) {
      this.productObject.extra_options = this.productObject.extra_options.map(item => ({ ...item, isSelected: true }));
    }
    console.log(this.productObject);
    this.$nextTick(this.setFirstOptionChosen);

    tg.MainButton.text = "Добавить";  // сначала назначаем цвета и текст кнопкам
    tg.MainButton.textColor = "#0C0C0C";


    tg.onEvent('mainButtonClicked', this.addToShoppingCart);  // затем навешиваем листенеры
    tg.onEvent('backButtonClicked', this.backButtonMethod);

    tg.MainButton.show();  // и только после всех настроек кнопок показываем главную кнопку
  },
  unmounted() {
    tg.offEvent('mainButtonClicked', this.addToShoppingCart);
    tg.offEvent('backButtonClicked', this.backButtonMethod);
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
  line-height: 26px;
  font-weight: bold;
  color: var(--app-text-color);
  word-wrap: break-word;
  padding: 10px 5% 5px;
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
    h1 {
      white-space: preserve;
    }
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

.extra-options {
  margin: 10px 0;
  padding: 0 0 20px 0;
  .span-block {
    padding: 20px 5% 10px;
    text-wrap: wrap;
  }
  .swiper-container {
    margin: 0 0 0 5%;
  }
}

.swiper-container {
  margin: 10px 0;
  .option-block {
    background-color: var(--app-background-color);
    width: 75px;
    height: 65px;
    padding: 0 5px;
    border-radius: 15px;
    word-break: break-word;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
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

.priced_block {
  display: flex;
  flex-direction: column;
}

span {
  white-space: preserve;
}

</style>