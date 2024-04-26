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
}