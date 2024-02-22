<template>
  <RouterView />
  <RouterLink to="/shopping-cart" v-if="itemsAddToCartArray.length>0"><button class="addToCartBtn">В Корзину</button></RouterLink>
</template>

<script>
import { defineComponent } from 'vue'

const buttons = document.querySelectorAll('button');
buttons.forEach(button => {
  button.addEventListener('click', function(event) {
    if (event.detail === 2) {
      event.preventDefault();
    }
  });
});
export default defineComponent({
  computed: {
    itemsAddToCartArray() {
      return this.$store.state.itemsAddToCartArray;
    }
  },
})
</script>

<style scoped lang="scss">
.addToCartBtn {
  width: 100%;
  height: 52px;
  color: #293C47;
  background-color: #59FFAF;
  position: fixed;
  bottom: 0;
  left: 0;
  cursor: pointer;
  box-shadow: none;
  border: none;
  font-size: 24px;
  font-weight: 600;
  font-family: 'Montserrat', sans-serif;
  z-index: 10;
  &:hover{
    background-color: #55A27D;
  }
}
@media (min-width: 1400px) {
  .addToCartBtn{
    height: 100px;
  }
}
</style>