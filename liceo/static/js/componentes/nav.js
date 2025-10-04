const menu = document.getElementById("menu");
const urlActual = menu.getAttribute("data-path-actual");
const links = menu.querySelectorAll("a");

links.forEach((link) => {
  if (location.origin + urlActual.trim() === link.href)
    link.setAttribute("aria-current", "page");
});

const btnMenu = document.getElementById("btn-menu");

btnMenu.addEventListener("click", () => {
  const aside = document.getElementById("aside");
  aside.classList.toggle("mostrar");

  if (aside.classList.contains("mostrar"))
    window.addEventListener("mousedown", cerrarPorClickAfuera);
});

function cerrarPorClickAfuera(e) {
  const padre = e.target.closest("#aside");

  if (padre === null) {
    // cerrar el menu si se hace click fuera de el y si no se trata del botón de abrir el menu
    if (!e.target.closest("#btn-menu")) aside.classList.remove("mostrar");

    window.removeEventListener("mousedown", cerrarPorClickAfuera);
  }
}
