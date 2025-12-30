// sin cambios: se deshabilita el botón
$id("submit").setAttribute("disabled", "");

// al cambiar algo, se habilita el botón
document.querySelector("form").addEventListener(
  "change",
  function () {
    $id("submit").removeAttribute("disabled");
  },
  { once: true },
);
