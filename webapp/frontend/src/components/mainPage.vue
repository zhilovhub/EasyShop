<template>
  <div class="wrapper">
    <ul class="items-styles">
      <li
          v-for="item in items"
          :key="item.id"
          class="item-block"
          style="position: relative;"
      >
        <img style="border-radius: 10px; width: 100%; height: 100%; object-fit: cover; margin: 5px auto;" v-if="item.picture" :src="'https://ezbots.ru:8080/files/' + item.picture" alt="img">
        <div style="margin-bottom: 10px">
        <span style="color: #71CBFF; font-size: 15px;">
          {{ shortenName(item.name) }}
        </span>
          <br>
          <span style="font-weight: 600; color: #FFFFFF; font-size: 15px;">
          {{priceComma(item.price)}}
        </span>
        </div>
        <button
            type="button"
            v-if="item.count === 0"
            @click="incrementCount(item)"
            style="height: 17.5%;"
        >
          Добавить
        </button>
        <div
            v-else
            style="display: flex; justify-content: space-between; height: 17.5%"
        >
          <button
              style="background-color: #FF7171; display: flex; align-items: center; justify-content: center; width: 45%;"
              @click="decrementCount(item)"
          >
            <svg width="22" height="4" viewBox="0 0 22 4" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20.625 3.875H1.375C0.615613 3.875 0 3.03553 0 2C0 0.964473 0.615613 0.125 1.375 0.125H20.625C21.3844 0.125 22 0.964473 22 2C22 3.03553 21.3844 3.875 20.625 3.875Z" fill="white"/>
            </svg>
          </button>
          <button
              style="background-color:#71CBFF; display: flex; align-items: center; justify-content: center; width: 45%;"
              @click="incrementCount(item)"
          >
            <svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19.6875 9.1875H11.8125V1.3125C11.8125 0.587631 11.2249 0 10.5 0C9.77513 0 9.1875 0.587631 9.1875 1.3125V9.1875H1.3125C0.587631 9.1875 0 9.77513 0 10.5C0 11.2249 0.587631 11.8125 1.3125 11.8125H9.1875V19.6875C9.1875 20.4124 9.77513 21 10.5 21C11.2249 21 11.8125 20.4124 11.8125 19.6875V11.8125H19.6875C20.4124 11.8125 21 11.2249 21 10.5C21 9.77513 20.4124 9.1875 19.6875 9.1875Z" fill="white"/>
            </svg>
          </button>
        </div>
        <div v-if="item.count > 0" class="circle">
          {{item.count}}
        </div>
      </li>
    </ul>
  </div>

</template>

<script>

export default {
  name: 'mainPage',
  methods: {
    priceComma(price) {
      return price + ' ₽'
    },
    incrementCount(item) {
      if (item && typeof item.count === 'number') {
        item.count += 1;
        this.itemsAddToCart();
      } else {
        console.error('Ошибка: объект item или count не определены.');
      }
    },
    decrementCount(item) {
      if (item && typeof item.count === 'number') {
        item.count -= 1;
        this.itemsAddToCart()
      } else {
        console.error('Ошибка: объект item или count не определены.');
      }
    },
    itemsAddToCart() {
      this.$store.state.itemsAddToCartArray = this.$store.state.items.filter(item => item.count > 0);
    },
    shortenName(name) {
      if (!name) return '';
      return name.length > 15 ? name.substring(0, 15) + '...' : name;;
    }
  },
  computed: {
    https() {
      return https
    },
    items() {
      return this.$store.state.items;
    },
    itemsAddToCartArray() {
      return this.$store.state.itemsAddToCartArray;
    },
  },
  mounted() {
    this.$store.commit('itemsInit');
  }
};
</script>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 15px;
  line-height: 18.29px;
}

.items-styles{
  width: 90%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(40vw, 1fr));
  grid-column: 1;
  grid-gap: 15px;
  padding: 0;
  margin: 20px auto 50px;

  .item-block{
    aspect-ratio: 1/1;
    white-space: nowrap;
    background-color: #293C47;
    list-style-type: none;
    display: flex;
    flex-direction: column;
    justify-content: end;
    border-radius: 10px;
    padding: 12px;
  }
}

button {
  width: 100%;
  aspect-ratio: 5/1;
  background-color: #71CBFF;
  border-radius: 5px;
  cursor: pointer;
  box-shadow: none;
  border: none;
  &:hover {
    background-color: #3F5C6D;
    color:  #293C47;
  }
}

.circle {
  border-radius: 100%;
  background-color: #71CBFF;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  right: 10px;
  top: 10px;
}
@media (max-width: 300px) {
  .items-styles {
    grid-template-columns: repeat(auto-fill, minmax(95vw, 1fr));
    margin: 10px auto 40px;
    justify-content: center;
  }
}
@media (min-width: 700px) {
  .items-styles {
    grid-template-columns: repeat(auto-fill, minmax(35vw, 1fr));
    margin: 30px auto 40px;
    justify-content: center;
    width: 95%
  }
}
@media (min-width: 950px) and (max-width: 1400px) {
  .items-styles {
    grid-template-columns: repeat(2, minmax(20vw, 1fr));
    margin: 30px auto 50px;
  }
  .wrapper {
    margin: 0 auto;
  }
}
@media (min-width: 1400px) {
  .items-styles {
    grid-template-columns: repeat(auto-fill, minmax(20vw, 1fr));
    margin: 30px auto 120px;
    width: 1200px;
  }
}
</style>
