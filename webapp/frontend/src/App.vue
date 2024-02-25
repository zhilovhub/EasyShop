<template>
  <RouterView />
  <RouterLink to="/shopping-cart" v-if="itemsAddToCartArray.length>0"><button class="addToCartBtn">В Корзину</button></RouterLink>
</template>

<script>
import { defineComponent } from 'vue'

const textarea = document.querySelectorAll('textarea');

textarea.forEach(textarea => {
  textarea.addEventListener('blur', function() {
    textarea.blur();
  });

  document.addEventListener('click', function(event) {
    // Проверяем, было ли событие клика вне области ввода текущего textarea и не было ли это событие клика именно на клавиатуре
    if (!textarea.contains(event.target) && !isKeyboardEvent(event)) {
      textarea.blur();
    }
  });
});

function isKeyboardEvent(event) {
  // Проверяем, является ли событие клика событием клавиатуры
  // Например, на мобильных устройствах, клавиатурные события имеют 0 координат для event.clientX и event.clientY
  return event.clientX === 0 && event.clientY === 0;
}

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