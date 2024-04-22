fetch("https://ezbots.ru:2024/api/products/get_all_products/25",
    {
    method: "GET",
    headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*"
    }
    })
  .then((response) => {
    if (response.ok) {
      return response.json();
    } else {
      throw new Error("NETWORK RESPONSE ERROR");
    }
  })
  .then(data => {
    console.log(data);
    displayProducts(data)
  })
  .catch((error) => console.error("FETCH ERROR:", error));


function displayProducts(data) {
  const productsSection = document.getElementById("products_list");
  for (let i in data){
      let product = data[i]
      console.log(product)
      const product_card = document.createElement("div");
      product_card.innerHTML = "<h3>" + product.name + "</h3><p>" + product.description + "</p>";
      productsSection.appendChild(product_card);
  }

  // // cocktail image
  // const cocktailImg = document.createElement("img");
  // cocktailImg.src = cocktail.strDrinkThumb;
  // cocktailDiv.appendChild(cocktailImg);
  // document.body.style.backgroundImage = "url('" + cocktail.strDrinkThumb + "')";
  // // cocktail ingredients
  // const cocktailIngredients = document.createElement("ul");
  // cocktailDiv.appendChild(cocktailIngredients);
  // const getIngredients = Object.keys(cocktail)
  //   .filter(function (ingredient) {
  //     return ingredient.indexOf("strIngredient") == 0;
  //   })
  //   .reduce(function (ingredients, ingredient) {
  //     if (cocktail[ingredient] != null) {
  //       ingredients[ingredient] = cocktail[ingredient];
  //     }
  //     return ingredients;
  //   }, {});
  // for (let key in getIngredients) {
  //   let value = getIngredients[key];
  //   listItem = document.createElement("li");
  //   listItem.innerHTML = value;
  //   cocktailIngredients.appendChild(listItem);
  // }
}