"use strict";

const filtros = document.getElementById("filtros");

document.getElementById("ver-filtros").addEventListener("click", function (e) {
  filtros.classList.toggle("abierto");

  if (filtros.classList.contains("abierto")) cerrarPorClickAfuera();
});

function cerrarPorClickAfuera() {
  document.addEventListener("mousedown", function (e) {
    if (!filtros.contains(e.target)) {
      filtros.classList.remove("abierto");
      document.removeEventListener("mousedown", cerrarPorClickAfuera);
    }
  });
}
