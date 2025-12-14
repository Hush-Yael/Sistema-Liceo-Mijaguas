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

function cambiarTemaClase(oscuro) {
  document.documentElement.classList.toggle("oscuro", oscuro);
}

menuTema.dataset.tema = localStorage.getItem("tema", tema) || "auto";
menuTema.querySelector("input[value='" + menuTema.dataset.tema + "']").checked =
  true;

function aplicarTema() {
  try {
    // valor seleccionado
    const tema = menuTema.querySelector("input:checked").value;
    localStorage.setItem("tema", tema);

    // cambio automático si se selecciona 'auto'
    if (tema === "auto")
      auto.addEventListener
        ? auto.addEventListener("change", cambioAutoTema)
        : auto.addListener(cambioAutoTema);
    else
      auto.removeEventListener
        ? auto.removeEventListener("change", cambioAutoTema)
        : auto.removeListener(cambioAutoTema);

    const esOscuro = tema === "oscuro" || (tema === "auto" && auto.matches);

    if (!document.startViewTransition) cambiarTemaClase(esOscuro);
    else document.startViewTransition(() => cambiarTemaClase(esOscuro));

    menuTema.dataset.tema = tema;
  } catch (error) {
    // no se ha seleccionado ninguno, se selecciona 'auto' por defecto
    if (error instanceof TypeError) {
      document.getElementById("tema-auto").checked = true;
      aplicarTema();
    }
  }
}

function cambioAutoTema(e) {
  if (!document.startViewTransition) cambiarTemaClase(e.matches);
  else document.startViewTransition(() => cambiarTemaClase(e.matches));
}

menuTema.addEventListener("change", aplicarTema);
