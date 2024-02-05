<template>
  <RouterView />
  <RouterLink to="/shopping-cart" v-if="itemsAddToCartArray.length>0"><custom-button /></RouterLink>
</template>

<script>
import { defineComponent } from 'vue'
import CustomButton from '@/components/customButton.vue'

export default defineComponent({
  components: { CustomButton },
  computed: {
    itemsAddToCartArray() {
      return this.$store.state.itemsAddToCartArray;
    }
  }
})
</script>

<style scoped lang="scss">
</style>