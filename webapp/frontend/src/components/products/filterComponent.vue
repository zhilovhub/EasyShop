<template>
  <div class="wrapper">
    <div class="block">
      <div class="span-block">
        <h1>Фильтры</h1>
        <img @click="closeFilterComponent" src="@/assets/close.svg" alt="close" >
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
      <div>По популярности</div>
      <div>По популярности</div>
      <div>По популярности</div>
    </div>
    <hr style="border: 1px solid var(--app-hr-border-color); width: 90%; margin: 2.5% auto;">
    <div class="block">
      <span>Бренд</span>
      <div class="brand-filter">
        <div class="brand" v-for="brand in brands" @click="toggleImage($event, brand)">
          <img :src="brand.isActive ? '/src/assets/checkmarkcircle.svg' : '/src/assets/circle.svg'" alt="brand image">
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
    }
  },
  computed: {
    brands() {
      return this.$store.state.brands;
    }
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
