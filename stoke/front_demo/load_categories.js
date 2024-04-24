fetch("https://ezbots.ru:2024/api/products/get_all_categories/25",
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
    showCats(data)
  })
  .catch((error) => console.error("FETCH ERROR:", error));


function showCats(data) {
  const catsList = document.getElementById("category");
  for (let i in data){
      let cat = data[i]
      console.log(cat)
      const cat_option = document.createElement("option");
      cat_option.value = cat.id;
      cat_option.label = cat.name;
      cat_option.innerHTML = cat.name;
      catsList.appendChild(cat_option);
  }
}