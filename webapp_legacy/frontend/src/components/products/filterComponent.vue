<template>
  <div class="wrapper" :style="{ opacity: isMounted ? 1 : 0 }">
    <div class="block">
      <div class="span-block">
        <h1>Фильтры</h1>
      </div>
    </div>
    <div class="block">
      <span>Цена, ₽</span>
      <div class="block-textarea">
        <input v-model="fromPrice" type="number" min="0" placeholder="От">
        <input v-model="toPrice" type="number" :min="this.fromPrice" placeholder="До">
      </div>
    </div>
    <div class="block based-filter">
      <div
        v-for="filter in filters"
        :id="filter"
        @click="chooseOption($event.target)"
        class="filterOnBased"
      >{{filter}}</div>
    </div>
    <hr style="border: 1px solid var(--app-hr-border-color); width: 90%; margin: 2.5% auto;">
    <div class="block">
      <span>Категории</span>
      <div class="brand-filter">
        <div class="brand" v-for="brand in brands" :id="brand" @click="toggleImage($event, brand)">
          <img v-if="brand.isActive" src="@/assets/markedcircle.png" alt="brand image">
          <img v-else src="@/assets/circle.png" alt="brand image">
          <span>{{brand.name}}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { tg } from '@/main.js'
export default {
  data() {
    return {
      imageCircle: '',
      imageMarkedCircle: '',
      fromPrice: this.$store.state.price_min !== 0 ? this.$store.state.price_min : null,
      toPrice: this.$store.state.price_max !== 2147483647 ? this.$store.state.price_max : null,
      filters: ['По убыванию', 'По возрастанию'],
      chosenBasedFilter:  '',
      isMounted: false
    }
  },
  name: "filterComponent",
  methods: {
    mainButtonClickedEvent() {
      if (this.fromPrice) {
        this.$store.state.price_min = this.fromPrice;
      }
      if (this.toPrice) {
        this.$store.state.price_max = this.toPrice;
      }
      this.chosenBasedFilter === 'По убыванию' ? this.$store.state.reverse_order = true : this.$store.state.reverse_order = false;
      setTimeout(() => {
        this.isMounted = false;
        this.$emit("close");
      }, 100);
    },
    backButtonClickedEvent() {
      setTimeout(() => {
        this.isMounted = false;
        this.$emit("close");
      }, 100);
    },
    toggleImage(event, brand) {
      brand.isActive = !brand.isActive;
    },
    chooseOption(target) {
      const allSizes = document.querySelectorAll('.filterOnBased');
      allSizes.forEach(size => {
        size.classList.remove('chosen');
      });
      target.classList.add('chosen');
      this.chosenBasedFilter = target.innerText;
    }
  },
  computed: {
    brands() {
      return this.$store.state.brands;
    },
  },
  mounted() {
    tg.BackButton.show();

    tg.MainButton.text = "Применить";
    tg.MainButton.color = "#59C0F9";
    tg.MainButton.textColor = "#0C0C0C";

    tg.onEvent('mainButtonClicked', this.mainButtonClickedEvent);
    tg.onEvent('backButtonClicked', this.backButtonClickedEvent);

    tg.MainButton.show();

    this.$store.state.reverse_order === true ? this.chosenBasedFilter = 'По убыванию' : this.chosenBasedFilter = 'По возрастанию';
    if (this.chosenBasedFilter === 'По возрастанию') {
      let permElement = document.getElementById('По возрастанию');
      permElement.classList.add('chosen');
    } else if (this.chosenBasedFilter === 'По убыванию') {
      let permElement = document.getElementById('По убыванию');
      permElement.classList.add('chosen');
    }

    setTimeout(() => {
      this.isMounted = true;
    }, 50);
  },
  unmounted() {
    tg.offEvent('mainButtonClicked', this.mainButtonClickedEvent);
    tg.offEvent('backButtonClicked', this.backButtonClickedEvent);
  }
};
</script>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 16px;
  font-weight: 500;
  color: var(--app-text-color);
}

.wrapper {
  width: 100vw;
  height: 100vh;
  background-color: var(--app-background-color);
  transition: opacity 0.5s ease;
  .block {
    padding: 20px 5%;
    .span-block {
      display: flex;
      justify-content: space-between;
      h1 {
        font-size: 20px;
        font-weight: bold;
      }
      img {
        &:hover {
          opacity: 0.7;
        }
      }
    }
  }
}

.block-textarea {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  input {
    width: 48.5%;
    background-color: var(--app-hr-border-color);
    border-radius: 15px;
    height: 60px;
    resize: none;
    padding-left: 10px;
    font-size: 13px;
    color: var(--app-text-color);
    box-shadow: none;
    border: none;
    &::placeholder {
      color: var(--app-text-color);
    }
    &:focus {
      outline: 2px solid var(--app-text-color);
    }
  }
}


.based-filter {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(40vw, 1fr));
  grid-column: 1;
  grid-gap: 10px;
  .filterOnBased {
    font-size: 14px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 35px;
    border-radius: 30px;
    background-color: var(--app-hr-border-color);
  }
  .chosen {
    border: 3px solid #9EDCFF;
  }
}

.brand-filter {
  margin-top: 10px;
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(24%, 1fr));
  grid-column: 1;
  grid-gap: 15px;
  .brand {
    height: 30px;
    border-radius: 30px;
    display: flex;
    align-items: center;
    background-color: var(--app-hr-border-color);
    img {
      width: 13px;
      height: 13px;
      margin: 0 10px;
    }
  }
}
</style>
