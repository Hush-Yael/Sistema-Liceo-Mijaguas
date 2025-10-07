const nav = document.getElementById("nav");
const urlActual = nav.getAttribute("data-path-actual");
const links = nav.querySelectorAll("a");

links.forEach((link) => {
  if (location.origin + urlActual.trim() === link.href)
    link.setAttribute("aria-current", "page");
});

const btnNav = document.getElementById("btn-nav");

btnNav.addEventListener("click", function () {
  nav.classList.toggle("abierto");

  const abierto = nav.classList.contains("abierto");

  if (abierto) window.addEventListener("mousedown", cerrarPorClickAfuera);

  this.setAttribute("aria-expanded", abierto);
});

function cerrarPorClickAfuera(e) {
  const padre = e.target.closest("#nav");

  if (padre === null) {
    // cerrar el nav si se hace click fuera de el y si no se trata del botón de abrir el nav
    if (!e.target.closest("#btn-nav")) {
      btnNav.setAttribute("aria-expanded", "false");
      nav.classList.remove("abierto");
    }

    window.removeEventListener("mousedown", cerrarPorClickAfuera);
  }
}
