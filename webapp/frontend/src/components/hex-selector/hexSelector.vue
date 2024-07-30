<script>
  import { createVuetify } from 'vuetify'
  import { tg } from '@/main.js'
  import {th} from "vuetify/locale";

  export default {
    computed: {
      th() {
        return th
      }
    },
    data: () => ({
      selected_color: '#fff',
    }),
    mounted() {
      tg.MainButton.show();
      tg.MainButton.text = "Выбрать цвет";
      tg.MainButton.textColor = "#0C0C0C";
      tg.onEvent('mainButtonClicked', this.sendSelectedColor);
    },
    methods: {
      // handleChangedColor(color) {
      //   console.log("color", color, this.selected_color)
      // },
      sendSelectedColor() {
        console.log(this.selected_color)
        this.$store.dispatch("postColorData", {color: this.selected_color}).then((response) => {console.log(response)})
      }
    }
  }
</script>

<template>
  <div class="color-picker-container">
    <v-color-picker
        class="v-color-picker"
        v-model="selected_color"
        color="#fff"
        mode="rgba"
        rounded="true"> <!--@update:modelValue="handleChangedColor" -->
    </v-color-picker>
  </div>
</template>

<style scoped lang="scss">
.v-color-picker {
  margin: 10px;
}

.color-picker-container {
  margin: 0 auto;
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
}
</style>