function sendCsv(form){
  const form_data = new FormData(form)
  const formDataObj = {};
  form_data.forEach((value, key) => (formDataObj[key] = value));
  console.log(formDataObj)
  fetch("https://ezbots.ru:2024/api/products/send_product_csv_file", {
    method: "POST",
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },

    //make sure to serialize your JSON body
    body: JSON.stringify({
        bot_id: 25,
        file: formDataObj.file
    })
  })
  .then( (response) => {
    console.log(response)
    if (response.ok) {
      alert("Таблица отправлена")
    } else {
      alert("Ошибка при отправке таблицы.\n[" + response.status + "] " + response.statusText)
    }
     //do something awesome that makes the world a better place
  });
  // form.submit();
}


function exportCsv(){
  fetch("https://ezbots.ru:2024/api/products/get_products_csv_file/25", {
    method: "GET",
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  })
  .then( (response) => {
    console.log(response)
    if (response.ok) {
      alert("Таблица получена")
    } else {
      alert("Ошибка при получении таблицы.\n[" + response.status + "] " + response.statusText)
    }
     //do something awesome that makes the world a better place
  });
  // form.submit();
}