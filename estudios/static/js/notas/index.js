// para evitar que se ejecute la request de "/notas_tabla" al cambiar los filtros específicos de búsqueda cuando el campo de búsqueda está vacío, ya que no tendría sentido, pues los resultados serías los mismos
function verificarBusquedaNoVacia() {
  return document.getElementById("q").value.trim() !== "";
}

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
