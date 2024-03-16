<script>
export default {
  data() {
    return {
      cards: [
        {
          name: "Мастер-класс \"Макияж для себя\"",
          price: 5000,
          id: 0,
          isActive: false
        },
        {
          name: "Мастер-класс \"Макияж для себя с подругой\"",
          price: 2010,
          id: 1,
          isActive: false
        },
        {
          name: "Выезд мастера",
          price: 500,
          id: 2,
          isActive: false
        },
        {
          name: "Макияж",
          price: 1000,
          id: 3,
          isActive: false
        },
        {
          name: "Макияж + прическа",
          price: 9600,
          id: 4,
          isActive: false
        },
        {
          name: "Пакет \"Выпускница\"",
          price: 4300,
          id: 4,
          isActive: false
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
    this.cards.map(card=>{card.price = card.price + " ₽"});
    let WebApp = window.Telegram.WebApp;
    const BackButton = WebApp.BackButton;
    BackButton.show();
    BackButton.onClick(function() {
      BackButton.hide();
    });
    WebApp.onEvent('backButtonClicked', function() {
      window.location.href = `/services/choose-employee?chosen_branch=${this.chosenBranch}&chosen_speciality=${this.chosenSpeciality}`;
    });
  },
  methods: {
    circleToggle(card) {
      card.isActive = !card.isActive;
      this.$store.services = this.cards.filter(card => card.isActive === true);
    }
  }
}
</script>

<template>
  <div class="wrapper">
    <h1 style="margin: 25px auto">Выбор услуг</h1>
    <h2><img src="@/assets/geo.png" alt="geo"> {{chosenBranch}}</h2>
    <ul class="cards">
      <li
        v-for="card in cards"
        :key="card.id"
        class="card-block"
        @click="circleToggle(card)"
      >
        <span class="card-name">{{card.name}}</span>
        <div style="display: flex; align-items: center;">
          <span class="card-price">{{card.price}}</span>
          <div v-if="card.isActive" class="circle-active"></div>
          <div v-else class="circle"></div>
        </div>
      </li>
    </ul>
  </div>
  <RouterLink :to="`/products-page/shopping-cart?bot_id=`" v-if="this.$store.services && this.$store.services.length>0"><button>Далее</button></RouterLink>
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
    line-height: 22px;
    aspect-ratio: 5/1;
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
    .card-name{
      font-size: 18px;
      font-weight: 500;
      white-space: normal;
      max-width: 250px;
    }
    .card-price{
      font-size: 14px;
      color: #71CBFF;
      font-weight: 400;
      line-height: 17px;
    }
    .circle{
      width: 28px;
      height: 28px;
      border: 1px solid #71CBFF;
      border-radius: 100%;
      margin-left: 10px;
    }
    .circle-active{
      width: 28px;
      height: 28px;
      border: 1px solid #71CBFF;
      background-color: #71CBFF;
      border-radius: 100%;
      margin-left: 10px;
    }
  }
}
button {
  width: 100%;
  height: 52px;
  color: #1E1E1E;
  background-color: #71CBFF;
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
    background-color: #71CBFF6E;
  }
}
</style>