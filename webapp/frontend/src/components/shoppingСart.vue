<script>
  export default {
    name: 'ShoppingCart',
    computed: {
      itemsAddToCartArray() {
        return this.$store.state.itemsAddToCartArray;
      }
    }
  }
</script>

<template>
  <div class="wrapper">
    <ul class="items-styles">
      <li
        v-for="item in itemsAddToCartArray"
        :key="item.id"
        class="item-block"
      >
      </li>
    </ul>
  </div>
</template>

<style scoped lang="scss">
.items-styles{
  width: 100%;
  display: grid;
  grid-column: 1;
  grid-template-rows: repeat(auto-fill, minmax(166.68px, 1fr)) ;
  grid-gap: 15px;
  padding: 0;
  margin-bottom: 50px;

  .item-block{
    aspect-ratio: 1/1;
    background-color: #293C47;
    list-style-type: none;
    display: flex;
    flex-direction: column;
    justify-content: end;
    border-radius: 10px;
    padding: 12px;
  }
}
.order-wrapper{
  background-color: #20282C;
}

@media (min-width: 700px) {
  .items-styles {
    grid-template-columns: repeat(auto-fill, minmax(40%, 1fr));
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