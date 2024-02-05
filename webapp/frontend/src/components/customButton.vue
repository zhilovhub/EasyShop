<script>
  export default {
    name: "customButton",
    props: {
      amount: Number,
      // eslint-disable-next-line vue/require-prop-type-constructor
      default: 0
    }

  }
</script>

<template>
  <div v-if="this.$props.amount">
    <button>
      {{this.$props.amount}}
    </button>
  </div>
  
  <div v-else>
    <button>
      В Корзину
    </button>
  </div>
</template>

<style scoped lang="scss">
button {
  width: 100%;
  aspect-ratio: 8/1;
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
  padding: 20px;
  font-family: 'Montserrat', sans-serif;
  z-index: 999;
  &:hover{
    background-color: #55A27D;
  }
}
@media (min-width: 1400px) {
  button{
    height: 100px;
  }
}
</style>