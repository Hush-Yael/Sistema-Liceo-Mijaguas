// al cambiar algo, se habilita el botón
document.querySelector("form").addEventListener(
  "change",
  function () {
    document.getElementById("submit").removeAttribute("disabled");
  },
  { once: true },
);
