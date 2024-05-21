<template>
  <RouterView />
</template>

<script>

document.body.style.zoom = "100%";

const textarea = document.querySelectorAll('textarea');
textarea.forEach(textarea => {
  textarea.addEventListener('blur', function() {
    textarea.blur();
    document.activeElement.blur();
  });
  document.addEventListener('click', function(event) {
    // Проверяем, было ли событие клика вне области ввода текущего textarea и не было ли это событие клика именно на клавиатуре
    if (!textarea.contains(event.target) && !isKeyboardEvent(event)) {
      textarea.blur();
      document.activeElement.blur();
    }
  });
});
function isKeyboardEvent(event) {
  // Проверяем, является ли событие клика событием клавиатуры
  // Например, на мобильных устройствах, клавиатурные события имеют 0 координат для event.clientX и event.clientY
  return event.clientX === 0 && event.clientY === 0;
}
</script>

<style>
button {
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  -khtml-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
}
</style>