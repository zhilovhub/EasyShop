<template>
  <FilterComponent @group="receivedData" @close="filterComponentIs = false" v-if="filterComponentIs"/>
  <div v-else>
  <div class="input-block" v-if="inputIsActive">
    <input autofocus @focusout="toggleInput" v-model="inputValue" placeholder="Введите название продукта">
  </div>
  <div v-else class="header">
    <span>Каталог</span>
    <div class="images">
      <svg @click="toggleFilterComponent()" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_1019_10893)">
          <path d="M0.833333 3.95806H3.11333C3.2922 4.61617 3.68264 5.19714 4.22444 5.61134C4.76623 6.02553 5.42927 6.24994 6.11125 6.24994C6.79323 6.24994 7.45627 6.02553 7.99806 5.61134C8.53986 5.19714 8.9303 4.61617 9.10917 3.95806H19.1667C19.3877 3.95806 19.5996 3.87026 19.7559 3.71398C19.9122 3.5577 20 3.34574 20 3.12473C20 2.90371 19.9122 2.69175 19.7559 2.53547C19.5996 2.37919 19.3877 2.29139 19.1667 2.29139H9.10917C8.9303 1.63328 8.53986 1.05232 7.99806 0.638118C7.45627 0.223921 6.79323 -0.000488281 6.11125 -0.000488281C5.42927 -0.000488281 4.76623 0.223921 4.22444 0.638118C3.68264 1.05232 3.2922 1.63328 3.11333 2.29139H0.833333C0.61232 2.29139 0.400358 2.37919 0.244078 2.53547C0.0877974 2.69175 0 2.90371 0 3.12473C0 3.34574 0.0877974 3.5577 0.244078 3.71398C0.400358 3.87026 0.61232 3.95806 0.833333 3.95806ZM6.11083 1.66639C6.39926 1.66639 6.68122 1.75192 6.92104 1.91217C7.16086 2.07241 7.34778 2.30017 7.45816 2.56665C7.56854 2.83312 7.59742 3.12635 7.54115 3.40923C7.48488 3.69212 7.34598 3.95197 7.14203 4.15592C6.93808 4.35988 6.67823 4.49877 6.39534 4.55504C6.11245 4.61131 5.81923 4.58243 5.55275 4.47205C5.28628 4.36167 5.05852 4.17476 4.89827 3.93493C4.73803 3.69511 4.6525 3.41316 4.6525 3.12473C4.65294 2.73809 4.80673 2.36741 5.08012 2.09402C5.35352 1.82062 5.72419 1.66684 6.11083 1.66639Z" fill="currentColor"/>
          <path d="M19.1667 9.16672H16.8867C16.7081 8.50846 16.3178 7.92728 15.7761 7.51291C15.2343 7.09854 14.5712 6.87402 13.8892 6.87402C13.2071 6.87402 12.544 7.09854 12.0023 7.51291C11.4605 7.92728 11.0702 8.50846 10.8917 9.16672H0.833333C0.61232 9.16672 0.400358 9.25452 0.244078 9.4108C0.0877974 9.56708 0 9.77904 0 10.0001C0 10.2211 0.0877974 10.433 0.244078 10.5893C0.400358 10.7456 0.61232 10.8334 0.833333 10.8334H10.8917C11.0702 11.4916 11.4605 12.0728 12.0023 12.4872C12.544 12.9016 13.2071 13.1261 13.8892 13.1261C14.5712 13.1261 15.2343 12.9016 15.7761 12.4872C16.3178 12.0728 16.7081 11.4916 16.8867 10.8334H19.1667C19.3877 10.8334 19.5996 10.7456 19.7559 10.5893C19.9122 10.433 20 10.2211 20 10.0001C20 9.77904 19.9122 9.56708 19.7559 9.4108C19.5996 9.25452 19.3877 9.16672 19.1667 9.16672ZM13.8892 11.4584C13.6007 11.4584 13.3188 11.3729 13.079 11.2126C12.8391 11.0524 12.6522 10.8246 12.5418 10.5581C12.4315 10.2917 12.4026 9.99843 12.4589 9.71555C12.5151 9.43266 12.654 9.17281 12.858 8.96885C13.0619 8.7649 13.3218 8.62601 13.6047 8.56974C13.8875 8.51347 14.1808 8.54235 14.4472 8.65273C14.7137 8.76311 14.9415 8.95002 15.1017 9.18985C15.262 9.42967 15.3475 9.71162 15.3475 10.0001C15.3471 10.3867 15.1933 10.7574 14.9199 11.0308C14.6465 11.3042 14.2758 11.4579 13.8892 11.4584Z" fill="currentColor"/>
          <path d="M19.1667 16.0416H9.10917C8.9303 15.3835 8.53986 14.8026 7.99806 14.3884C7.45627 13.9742 6.79323 13.7498 6.11125 13.7498C5.42927 13.7498 4.76623 13.9742 4.22444 14.3884C3.68264 14.8026 3.2922 15.3835 3.11333 16.0416H0.833333C0.61232 16.0416 0.400358 16.1294 0.244078 16.2857C0.0877974 16.442 0 16.654 0 16.875C0 17.096 0.0877974 17.3079 0.244078 17.4642C0.400358 17.6205 0.61232 17.7083 0.833333 17.7083H3.11333C3.2922 18.3664 3.68264 18.9474 4.22444 19.3616C4.76623 19.7758 5.42927 20.0002 6.11125 20.0002C6.79323 20.0002 7.45627 19.7758 7.99806 19.3616C8.53986 18.9474 8.9303 18.3664 9.10917 17.7083H19.1667C19.3877 17.7083 19.5996 17.6205 19.7559 17.4642C19.9122 17.3079 20 17.096 20 16.875C20 16.654 19.9122 16.442 19.7559 16.2857C19.5996 16.1294 19.3877 16.0416 19.1667 16.0416ZM6.11083 18.3333C5.8224 18.3333 5.54045 18.2478 5.30063 18.0875C5.0608 17.9273 4.87389 17.6995 4.76351 17.4331C4.65313 17.1666 4.62425 16.8734 4.68052 16.5905C4.73679 16.3076 4.87568 16.0477 5.07964 15.8438C5.28359 15.6398 5.54344 15.5009 5.82633 15.4447C6.10922 15.3884 6.40244 15.4173 6.66891 15.5276C6.93539 15.638 7.16315 15.8249 7.32339 16.0648C7.48364 16.3046 7.56917 16.5865 7.56917 16.875C7.56851 17.2615 7.41465 17.6321 7.1413 17.9054C6.86795 18.1788 6.4974 18.3326 6.11083 18.3333Z" fill="currentColor"/>
        </g>
        <defs>
          <clipPath id="clip0_1019_10893">
            <rect width="20" height="20" fill="white"/>
          </clipPath>
        </defs>
      </svg>
      <svg @click="toggleInput()" width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_1019_10954)">
          <path d="M19.9998 18.8217L14.7815 13.6034C16.137 11.9456 16.8035 9.83014 16.643 7.6947C16.4826 5.55925 15.5075 3.56717 13.9195 2.1305C12.3314 0.693821 10.252 -0.0775273 8.11119 -0.0240008C5.97039 0.0295257 3.93207 0.903832 2.41783 2.41807C0.903588 3.93231 0.0292815 5.97064 -0.024245 8.11143C-0.0777715 10.2522 0.693577 12.3317 2.13025 13.9197C3.56693 15.5077 5.55901 16.4828 7.69445 16.6433C9.82989 16.8037 11.9453 16.1372 13.6032 14.7817L18.8215 20.0001L19.9998 18.8217ZM8.33315 15.0001C7.01461 15.0001 5.72568 14.6091 4.62935 13.8765C3.53302 13.144 2.67854 12.1028 2.17395 10.8846C1.66937 9.66644 1.53735 8.326 1.79458 7.03279C2.05182 5.73959 2.68676 4.5517 3.61911 3.61935C4.55146 2.687 5.73934 2.05206 7.03255 1.79483C8.32576 1.53759 9.6662 1.66961 10.8844 2.1742C12.1025 2.67878 13.1437 3.53327 13.8763 4.62959C14.6088 5.72592 14.9998 7.01485 14.9998 8.3334C14.9978 10.1009 14.2948 11.7954 13.045 13.0452C11.7952 14.2951 10.1007 14.9981 8.33315 15.0001Z" fill="currentColor"/>
        </g>
        <defs>
          <clipPath id="clip0_1019_10954">
            <rect width="20" height="20" fill="currentColor"/>
          </clipPath>
        </defs>
      </svg>
    </div>
  </div>
  <div class="wrapper">
<!--    <div v-if="isLoading" class="loading-message">-->
<!--      Загрузка...-->
<!--    </div>-->
    <div v-if="items.length === 0"
         style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -75%); text-align: center; width: 350px"
    >
      <div style="font-size: 24px; color: #FFFFFF; font-weight: 600; word-wrap: break-word; margin-bottom: 20px">Товары в магазине отсутствуют</div>
      <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
        <g clip-path="url(#clip0_349_452)">
          <path d="M36 72C28.8799 72 21.9197 69.8887 15.9995 65.9329C10.0793 61.9772 5.46511 56.3548 2.74035 49.7766C0.0155983 43.1985 -0.697322 35.9601 0.691746 28.9768C2.08081 21.9935 5.50948 15.5789 10.5442 10.5442C15.5789 5.50948 21.9935 2.08081 28.9768 0.691746C35.9601 -0.697322 43.1985 0.0155983 49.7766 2.74035C56.3548 5.46511 61.9772 10.0793 65.9329 15.9995C69.8887 21.9197 72 28.8799 72 36C71.9897 45.5446 68.1935 54.6954 61.4445 61.4445C54.6954 68.1935 45.5446 71.9897 36 72ZM36 6.00002C30.0666 6.00002 24.2664 7.75949 19.3329 11.0559C14.3994 14.3524 10.5543 19.0377 8.28363 24.5195C6.013 30.0013 5.4189 36.0333 6.57646 41.8527C7.73402 47.6722 10.5912 53.0177 14.7868 57.2132C18.9824 61.4088 24.3279 64.266 30.1473 65.4236C35.9667 66.5811 41.9987 65.987 47.4805 63.7164C52.9623 61.4458 57.6477 57.6006 60.9441 52.6671C64.2405 47.7337 66 41.9335 66 36C65.9913 28.0462 62.8278 20.4207 57.2036 14.7965C51.5794 9.17226 43.9538 6.00875 36 6.00002ZM53.238 53.001C53.5009 52.7071 53.7032 52.3642 53.8334 51.9919C53.9636 51.6197 54.0192 51.2255 53.9969 50.8318C53.9746 50.4381 53.8749 50.0526 53.7035 49.6975C53.5321 49.3423 53.2924 49.0244 52.998 48.762C48.2344 44.6924 42.2574 42.3147 36 42C29.7427 42.3147 23.7656 44.6924 19.002 48.762C18.4077 49.2911 18.0478 50.0347 18.0017 50.8291C17.9556 51.6235 18.2269 52.4037 18.756 52.998C19.2851 53.5924 20.0287 53.9522 20.8231 53.9983C21.6175 54.0445 22.3977 53.7731 22.992 53.244C26.6594 50.1562 31.2164 48.3191 36 48C40.7835 48.3195 45.3404 50.1566 49.008 53.244C49.6016 53.7717 50.3803 54.0425 51.1733 53.9969C51.9662 53.9514 52.7087 53.5932 53.238 53.001ZM18 30C18 33 20.685 33 24 33C27.315 33 30 33 30 30C30 28.4087 29.3679 26.8826 28.2427 25.7574C27.1174 24.6322 25.5913 24 24 24C22.4087 24 20.8826 24.6322 19.7574 25.7574C18.6322 26.8826 18 28.4087 18 30ZM42 30C42 33 44.685 33 48 33C51.315 33 54 33 54 30C54 28.4087 53.3679 26.8826 52.2427 25.7574C51.1174 24.6322 49.5913 24 48 24C46.4087 24 44.8826 24.6322 43.7574 25.7574C42.6322 26.8826 42 28.4087 42 30Z" fill="#71CBFF"/>
        </g>
        <defs>
          <clipPath id="clip0_349_452">
            <rect width="72" height="72" fill="white"/>
          </clipPath>
        </defs>
      </svg>
    </div>

    <ul v-else class="items-styles">
      <li
          v-for="item in this.filteredItems"
          :key="item.id"
          class="item-block"
          style="position: relative;"
      >
        <img @click="redirectToProductCard(item.id)" v-if="item.picture" :src="item.picture" alt="img">
        <div style="margin: 10px 0;">
          <span style="font-size: 20px; font-weight: 600">
          {{priceComma(item.price)}}
        </span>
          <br>
        <span style="font-size: 15px;">
          {{ shortenName(item.name) }}
        </span>
        </div>
        <button
            type="button"
            v-if="item.count === 0"
            @click="incrementCount(item) "
            id="buy-button"
        >
          Купить
        </button>
        <div
            v-else
            style="display: flex; justify-content: space-between;"
        >
          <button
              class="increment-and-decrement-buttons"
              style="background-color: var(--app-button-bgcolor);"
              @click="decrementCount(item)"
          >
            <svg width="22" height="4" viewBox="0 0 22 4" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20.625 3.875H1.375C0.615613 3.875 0 3.03553 0 2C0 0.964473 0.615613 0.125 1.375 0.125H20.625C21.3844 0.125 22 0.964473 22 2C22 3.03553 21.3844 3.875 20.625 3.875Z" fill="white"/>
            </svg>
          </button>
          <button
              class="increment-and-decrement-buttons"
              style="background-color:#71CBFF;"
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
  </div>
</template>

<script>

import { apiUrl, bot_id } from '@/store/store.js'
import * as https from 'https'
import router from '@/router/router.js'
import FilterComponent from '/src/components/products/filterComponent.vue'
let tg = window.Telegram.WebApp;

Telegram.WebApp.onEvent('mainButtonClicked', async function(){
  await this.itemsAddToCart().then(e => {
    this.$store.commit("addToSessionStorage");
  });
});

window.Telegram.WebApp.onEvent('backButtonClicked', () => {
  this.fromPrice = null;
  this.toPrice = null;
  this.inputValue = ''
  this.inputIsActive = !this.inputIsActive;
  tg.BackButton.hide();
});

export default {
  name: 'productsPage',
  components: { FilterComponent },
  data() {
    return {
      isLoading: true,
      inputIsActive: false,
      inputValue: '',
      filterComponentIs: false,
      fromPrice: null,
      toPrice: null,
    }
  },
  methods: {
    apiUrl() {
      return apiUrl
    },
    bot_id() {
      return bot_id
    },
    priceComma(price) {
      const parts = price.toString().split(/(?=(?:\d{3})+$)/);
      return parts.join(' ') + ' ₽';
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
        this.itemsAddToCart();
      } else {
        console.error('Ошибка: объект item или count не определены.');
      }
    },
    itemsAddToCart() {
      this.$store.state.itemsAddToCartArray = this.$store.state.items.filter(item => item.count > 0);
      if (this.itemsAddToCartArray.length> 0) {
        tg.MainButton.show();
      } else {
        tg.MainButton.hide();
      }
    },
    shortenName(name) {
      if (!name) return '';
      return name.length > 18 ? name.substring(0, 15) + '...' : name;
    },
    redirectToProductCard(itemId) {
      router.push('products-page/' + itemId)
    },
    toggleInput() {
      this.fromPrice = null;
      this.toPrice = null;
      this.inputValue = ''
      this.inputIsActive = !this.inputIsActive;
    },
    toggleFilterComponent() {
      this.filterComponentIs = !this.filterComponentIs;
    },
    receivedData(data) {
      this.fromPrice = data.fromPrice;
      this.toPrice = data.toPrice;
    },
    // animationButton(item, $event) {
    //   $event.target.classList.add('animation-button');
    //   setTimeout(() => {
    //     $event.target.classList.remove('animation-button');
    //     if (item && typeof item.count === 'number') {
    //       item.count += 1;
    //       this.itemsAddToCart();
    //     } else {
    //       console.error('Ошибка: объект item или count не определены.');
    //     }}, 100)
    // }
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
    filteredItems() {
      if (!this.items) return [];

      return this.items.filter(el => {
        const matchesPrice = (!this.fromPrice || el.price >= this.fromPrice) && (!this.toPrice || el.price < this.toPrice);
        const matchesName = !this.inputValue || (el.name && el.name.toLowerCase().includes(this.inputValue.toLowerCase()));
        return matchesPrice && matchesName;
      });
    },
  },
  watch: {
    inputIsActive(value) {
      const BackButton = window.Telegram.WebApp.BackButton;
      if (value) {
        BackButton.show();
        BackButton.onClick(() => {
          this.fromPrice = null;
          this.toPrice = null;
          this.inputValue = ''
          this.inputIsActive = !this.inputIsActive;
          BackButton.hide();
        });
      }
    }
  },
  mounted() {
    this.itemsAddToCart();
  //   this.$store.dispatch('itemsInit').then(() => {
  //     this.isLoading = false;
  //     let tempCheckItems = sessionStorage.getItem('itemsAddToCartArray');
  //     tempCheckItems = JSON.parse(tempCheckItems);
  //     if (tempCheckItems && tempCheckItems.length > 0 && tempCheckItems.length !== this.items.length) {
  //       //Проверка совпадает ли длина из хранилища сессии с длиной из сервера, если не совпадает, то заменяется только совпадающий элемент(т.е его поле count).
  //       let resultArray = [];
  //       for (let i = 0; i < this.$store.state.items.length; i++) {
  //         let matchingItem = tempCheckItems.find(item => item.id === this.$store.state.items[i].id);
  //         resultArray.push(matchingItem || this.$store.state.items[i]);
  //       }
  //       this.$store.state.items = resultArray;
  //       this.itemsAddToCart();
  //     }
  //     else if(tempCheckItems && tempCheckItems.length > 0) {
  //       //Если все элементы из локального хранилища совпадают с теми, что на сервере, то приоритет отдаётся тем, что в хранилище сессии.
  //       let itemsMatch = true;
  //       for (let i = 0; i < this.items.length; i++) {
  //         if (this.items[i].id !== tempCheckItems[i].id) {
  //           itemsMatch = false;
  //           break;
  //         }
  //       }
  //       if (itemsMatch) {
  //         this.$store.state.items = tempCheckItems;
  //         this.itemsAddToCart();
  //       }
  //     }
  //   });
  //    this.$store.commit("fetchOrderId");
  //    this.$store.commit("checkOrderId");
  },
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

.header {
  max-width: 100%;
  margin: 0 5%;
  padding-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  .images {
    display: flex;
    svg {
      margin: 0 5px;
      width: 20px;
      height: 20px;
    }
  }
  span {
    font-size: 20px;
    font-weight: bold;
  }
}

.input-block {
  margin: 20px 5%;
  input {
    width: 100%;
    padding: 10px 20px;
    border-radius: 15px;
    background-color: var(--app-card-background-color);
    color: var(--app-text-color);

    &:focus {
      outline: 2px solid var(--app-text-color);
      &::placeholder {
        opacity: 0;
      }
    }
  }
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
    aspect-ratio: 1/0.75;
    white-space: nowrap;
    background-color: var(--app-card-background-color);
    list-style-type: none;
    display: flex;
    flex-direction: column;
    justify-content: end;
    border-radius: 15px;
    padding: 5px;
    img {
      position: relative;
      top: -5px;
      left: -5px;
      border-radius: 15px;
      object-fit: cover;
      width: calc(100% + 10px);
      height: calc(100% + 10px);
    }
    button {
      width: 100%;
      height: 40px;
      background-color: var(--app-button-bgcolor);
      box-shadow: 0 1px 2px 0 rgb(0, 0, 0, 25%);
      font-weight: 550;
      border-radius: 15px;
      cursor: pointer;
      border: none;
      &:hover {
        opacity: 0.7;
      }
    }
    .increment-and-decrement-buttons {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 47.5%;
    }
  }
}

.loading-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #FFFFFF;
  font-size: 24px;
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

//.animation-button {
//  animation: buttonAnimate 0.1s linear;
//}
//
//@keyframes buttonAnimate {
//  0% {
//    width: 100%;
//  }
//  100% {
//    width: 75%;
//  }
//}

@media (min-width: 1400px) {
  .addToCartBtn{
    height: 100px;
  }
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
