<script>
export default {
  data() {
    return {
      cards: [
        {
          name: "Архитектура бровей",
          id: 1
        },
        {
          name: "Броу Бар",
          id: 2
        },
        {
          name: "Визаж",
          id: 3
        },
        {
          name: "Врач косметолог",
          id: 4
        },
        {
          name: "Косметолог",
          id: 5
        },
        {
          name: "Маникюр",
          id: 6
        },
        {
          name: "Наращивание ресниц",
          id: 7
        },
      ]
    }
  },
  computed: {
    chosenBranch() {
      const params = new URLSearchParams(window.location.search);
      return params.get('chosen_branch');
    }
  },
  mounted() {
    let WebApp = window.Telegram.WebApp;
    const BackButton = WebApp.BackButton;
    BackButton.show();
    BackButton.onClick(function() {
      BackButton.hide();
    });
    WebApp.onEvent('backButtonClicked', function() {
      window.location.href = "/services/choose-branch";
    });
  },
  methods: {
    redirectToService(selectedSpeciality) {
      this.$router.push(`/services/choose-employee?chosen_branch=${this.chosenBranch}&chosen_speciality=${selectedSpeciality}`);
    }
  }
}

</script>

<template>
  <div class="wrapper">
    <h1 style="margin: 25px auto">Выбор специальности</h1>
    <h2><img src="@/assets/geo.png" alt="geo"> {{chosenBranch}}</h2>
    <ul class="cards">
      <li
        v-for="card in cards"
        :key="card.id"
        class="card-block"
        @click="redirectToService(card.name)"
      >
      {{card.name}}
        <img src="@/assets/arrow-right.png">
      </li>
    </ul>
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

.wrapper img{
  width: 16px;
  margin-right: 5px;
  position: relative;
  top: 2.5px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
  grid-column: 1;
  grid-gap: 15px;
  padding: 0;
  margin: 20px auto 50px;
  .card-block{
    cursor: pointer;
    font-size: 20px;
    font-weight: 500;
    line-height: 24.38px;
    aspect-ratio: 8/1;
    white-space: nowrap;
    background-color: #293C47;
    list-style-type: none;
    display: flex;
    justify-content: space-between;
    border-radius: 10px;
    padding: 12px;
    align-items: center;
    img{
      width: 12px;
      height: 25px;
    }
  }
}
</style>