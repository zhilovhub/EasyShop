function sendForm(form){
  const form_data = new FormData(form)
  const formDataObj = {};
  form_data.forEach((value, key) => (formDataObj[key] = value));
  console.log(formDataObj)
  fetch("https://ezbots.ru:2024/api/products/add_product", {
    method: "POST",
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },

    //make sure to serialize your JSON body
    body: JSON.stringify({
      bot_id: 25,
      name: formDataObj.product_name,
      category: formDataObj.category,
      description: formDataObj.description,
      article: formDataObj.article,
      price: formDataObj.price,
      count: formDataObj.stock,
      picture: formDataObj.picture,
      extra_options: {}
    })
  })
  .then( (response) => {
    console.log(response)
    if (response.ok) {
      alert("Товар добавлен")
    } else {
      alert("Ошибка при добавлении товара.\n[" + response.status + "] " + response.statusText)
    }
     //do something awesome that makes the world a better place
  });
  // form.submit();
}

