<template>
  <div class="wrapper">
    <div class="block">
      <div class="span-block">
        <h1>Фильтры</h1>
        <svg @click="closeFilterComponent" width="13" height="13" viewBox="0 0 13 13" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
          <path d="M7.6493 6.50023L12.7624 1.38765C13.0798 1.07026 13.0798 0.55566 12.7624 0.238291C12.445 -0.0791046 11.9304 -0.0791046 11.6131 0.238291L6.50047 5.3514L1.3879 0.238291C1.0705 -0.0791046 0.555904 -0.0791046 0.238535 0.238291C-0.0788351 0.555686 -0.0788605 1.07028 0.238535 1.38765L5.35164 6.50023L0.238535 11.6128C-0.0788605 11.9302 -0.0788605 12.4448 0.238535 12.7622C0.55593 13.0796 1.07053 13.0796 1.3879 12.7622L6.50047 7.64905L11.613 12.7622C11.9304 13.0796 12.445 13.0796 12.7624 12.7622C13.0798 12.4448 13.0798 11.9302 12.7624 11.6128L7.6493 6.50023Z" fill="currentColor"/>
        </svg>
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
      <div @click="chooseOption($event.target)" class="filterOnBased">По популярности</div>
      <div @click="chooseOption($event.target)" class="filterOnBased">По популярности</div>
      <div @click="chooseOption($event.target)" class="filterOnBased">По популярности</div>
    </div>
    <hr style="border: 1px solid var(--app-hr-border-color); width: 90%; margin: 2.5% auto;">
    <div class="block">
      <span>Бренд</span>
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
export default {
  data() {
    return {
      imageCircle: '',
      imageMarkedCircle: '',
      fromPrice: null,
      toPrice: null
    }
  },
  name: "filterComponent",
  methods: {
    closeFilterComponent() {
      this.groupFilters();
      this.$emit("close");
    },
    toggleImage(event, brand) {
      brand.isActive = !brand.isActive;
    },
    groupFilters() {
      this.$emit("group", {fromPrice: this.fromPrice, toPrice: this.toPrice})
    },
    chooseOption(target) {
      const allSizes = document.querySelectorAll('.filterOnBased');
      allSizes.forEach(size => {
        size.classList.remove('chosen');
      });
      target.classList.add('chosen');
    }
  },
  computed: {
    brands() {
      return this.$store.state.brands;
    }
  },
  mounted() {
    let tg = window.Telegram.WebApp;
    tg.MainButton.show();
    tg.MainButton.text = "Применить";
    tg.onEvent('mainButtonClicked', function(){
      this.closeFilterComponent();
      tg.MainButton.hide();
    });
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
  grid-gap: 15px;
  div {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 30px;
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
