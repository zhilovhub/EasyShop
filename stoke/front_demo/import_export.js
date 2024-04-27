// function sendCsv(form){
//   const form_data = new FormData(form)
//   const formDataObj = {};
//   form_data.forEach((value, key) => (formDataObj[key] = value));
//   console.log(formDataObj)
//     const reader = new FileReader();
//   reader.onload = function(evt) {
//     const metadata = `name: ${formDataObj.fileSelect.name}, type: ${formDataObj.fileSelect.type}, size: ${formDataObj.fileSelect.size}, contents:`;
//     const contents = evt.target.result;
//     formDataObj.file_result = contents
//     console.log(metadata, contents);
//     fetch("https://ezbots.ru:2024/api/products/send_product_csv_file", {
//     method: "POST",
//     headers: {
//       'Accept': 'multipart/form-data',
//       'Content-Type': 'multipart/form-data'
//     },
//
//     //make sure to serialize your JSON body
//     body: bot_id: 25, file: contents
//   })
//   .then( (response) => {
//     console.log(response)
//     if (response.ok) {
//       alert("Таблица отправлена")
//     } else {
//       alert("Ошибка при отправке таблицы.\n[" + response.status + "] " + response.statusText)
//     }
//      //do something awesome that makes the world a better place
//   });
//   };
//   reader.readAsDataURL(formDataObj.fileSelect);
//   // form.submit();
// }


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