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

const menuTema = document.getElementById("tema-menu");
const auto = window.matchMedia("(prefers-color-scheme: dark)");

aplicarTema();

function aplicarTema() {
  try {
    // valor seleccionado
    const tema = menuTema.querySelector("input:checked").value;

    document.documentElement.classList.toggle(
      "oscuro",
      tema === "oscuro" || (tema === "auto" && auto.matches),
    );

    // cambio automático si se selecciona 'auto'
    if (tema === "auto")
      auto.addEventListener
        ? auto.addEventListener("change", aplicarTemaAuto)
        : auto.addListener(aplicarTemaAuto);
    else
      auto.removeEventListener
        ? auto.removeEventListener("change", aplicarTemaAuto)
        : auto.removeListener(aplicarTemaAuto);

    menuTema.dataset.tema = tema;
  } catch (error) {
    // no se ha seleccionado ninguno, se selecciona 'auto' por defecto
    if (error instanceof TypeError) {
      document.getElementById("tema-auto").checked = true;
      aplicarTema();
    }
  }
}

function aplicarTemaAuto(e) {
  document.documentElement.classList.toggle("oscuro", e.matches);
}

menuTema.addEventListener("change", aplicarTema);
