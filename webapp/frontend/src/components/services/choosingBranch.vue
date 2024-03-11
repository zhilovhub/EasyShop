<script>
export default {
  name: 'choosingBranch',
  methods: {
    redirectToService(event) {
      const selectedBranch = event.target.value;
      this.$router.push(`/services/${selectedBranch}`);
    }
  }
}
</script>

<template>
  <div class="wrapper">
    <h1 style="margin: 25px auto">Онлайн Запись</h1>
    <div class="select-wrapper">
      <select @change="redirectToService($event)">
          <option>Выберите филиал</option>
          <option value="first-one">1-ый Филиал</option>
      </select>
    </div>
  </div>
</template>

<style scoped lang="scss">
*{
  box-sizing: border-box;
  font-family: 'Montserrat', sans-serif;
  font-size: 15px;
  line-height: 18.29px;
  color: #FFFFFF;
}

.wrapper {
  margin: 0 15px;
}

h1{
  color: #71CBFF;
  font-size: 24px;
  font-weight: 600;
  text-align: center;

}

.select-wrapper {
  position: relative;
  select {
    width: 100%;
    height: 50px;
    background-color: #293C47;
    border: 1px solid #20282C;
    border-radius: 8px;
    font-size: 20px;
    font-weight: 500;
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
    padding: 0 45px;
    margin: 10px auto;
    &:hover, :focus, :active {
      outline: none;
    }
  }
}

.select-wrapper::before, .select-wrapper::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 25px;
  height: 25px;
  background-repeat: no-repeat; /* Избегаем повторения фоновых изображений */
  background-size: contain; /* Подгоняем размер изображения под размеры контейнера */
}

.select-wrapper::before {
  left: 15px;
  transform: translateY(-50%);
  background-image: url("../../assets/geo.png");
}

.select-wrapper::after {
  right: 15px;
  background-image: url('../../assets/arrow-down.png');
  transform: translateY(-25%);
}


</style>