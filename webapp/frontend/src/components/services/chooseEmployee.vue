<script>

export default {
  data() {
    return {
      cards: [
        {
          firstName: 'asd',
          id: 0
        },
        {
          firstName: "",
          lastName: "",
          position: "",
          img: null,
          id: 10
        },
        {
          firstName: "Имя",
          lastName: "Фамилия",
          position: "Должность",
          img: null,
          id: 1
        },
        {
          firstName: "Имя",
          lastName: "Фамилия",
          position: "Должность",
          img: null,
          id: 2
        },
        {
          firstName: "Имя",
          lastName: "Фамилия",
          position: "Должность",
          img: null,
          id: 3
        },
        {
          firstName: "Имя",
          lastName: "Фамилия",
          position: "Должность",
          img: null,
          id: 4
        },
        {
          firstName: "Имя",
          lastName: "Фамилия",
          position: "Должность",
          img: null,
          id: 5
        },
        {
          firstName: "Имя",
          lastName: "Фамилия",
          position: "Должность",
          img: null,
          id: 6
        },
        {
          firstName: "Имя",
          lastName: "Фамилия",
          position: "Должность",
          img: null,
          id: 7
        },
      ]
    }
  },
  computed: {
    chosenBranch() {
      const params = new URLSearchParams(window.location.search);
      return params.get('chosen_branch');
    },
    chosenSpeciality() {
      const params = new URLSearchParams(window.location.search);
      return params.get('chosen_speciality');
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
      window.location.href = `/services/choose-speciality?chosen_branch=${this.chosenBranch}`;
    });
  },
  methods: {
    redirectToService(firstName, lastName) {
      if (!firstName || !lastName || firstName.length <= 0 || lastName.length <= 0) {
        return
      }
      this.$router.push(`/services/choose-service?chosen_branch=${this.chosenBranch}&chosen_speciality=${this.chosenSpeciality}&chosen_employee=${firstName+' '+lastName}`);
    }
  }
}
</script>

<template>
  <div class="wrapper">
    <h1 style="margin: 25px auto">Выбор сотрудника</h1>
    <h2><img src="@/assets/geo.png" alt="geo"> {{chosenBranch}}</h2>
    <ul class="cards">
      <li
        v-for="card in cards"
        :key="card.id"
        class="card-block"
        @click="redirectToService(card.firstName, card.lastName)"
      >
        <div v-if="card && card.position && card.id && card.firstName && card.lastName" class="card-main">
          <img class="user-picture" v-if="card.img" :src="card.img">
          <img class="user-picture" v-else src="@/assets/ellipse.png">
          <div class="card-title">
            <span style="font-size: 20px; font-weight: 500">{{card.firstName + " " + card.lastName}}</span>
            <span style="font-size: 15px; font-weight: lighter; line-height: 18px">{{card.position}}</span>
          </div>
        </div>
        <div style="height: 56px; display: flex; align-items: center;" v-else>
          <span style="font-size: 20px; white-space: normal; max-width: 300px">Сотрудник не имеет значения</span>
        </div>
        <img class="arrow-right" src="@/assets/arrow-right.png">
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
    .card-main {
      display: flex;
      align-items: center;
      .card-title {
        display: flex;
        flex-direction: column;
        margin: 10px;
      }
    }
    .arrow-right{
      width: 12px;
      height: 25px;
    }
    .user-picture {
      width: 56px;
    }
  }
}
</style>