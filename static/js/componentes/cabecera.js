const nav = document.getElementById("nav");

const menuSelector = document.getElementById("tema-selector");
const auto = window.matchMedia("(prefers-color-scheme: dark)");

function cambiarTemaClase(oscuro) {
  document.documentElement.classList.toggle("oscuro", oscuro);
}

const temaValores = ["claro", "oscuro", "auto"];
let temaGuardado = localStorage.getItem("tema");
if (!temaValores.includes(temaGuardado)) temaGuardado = "auto";

menuSelector.querySelector("input[value='" + temaGuardado + "']").checked =
  true;

function aplicarTema() {
  try {
    // valor seleccionado
    let tema = menuSelector.querySelector("input:checked").value;

    if (!temaValores.includes(tema)) {
      tema = "auto";
      try {
        menuSelector.querySelector("input[value='auto']").checked = true;
      } catch (error) {
        console.error(error);
      }
    }

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

    menuSelector.dataset.tema = tema;
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

const $btnNav = $id("btn-nav");
const $navBg = $id("nav-bg");
const anchoMedia = window.matchMedia("(min-width: 800px)");
const abierto = van.state(anchoMedia.matches);

function cerrarPorClickAfuera(e) {
  /** @type { Element | null } */
  const padre = e.target.closest("#nav");

  if (padre === null) {
    // cerrar el nav si se hace click fuera de el y si no se trata del botón de abrir el nav
    if (!e.target.closest("#btn-nav")) abierto.val = false;
    window.removeEventListener("mousedown", cerrarPorClickAfuera);
  }
}

$btnNav.onclick = () => (abierto.val = !abierto.oldVal);

/** @param {boolean} abierto */
function cambiarEstadoMenu(abierto) {
  $btnNav.setAttribute("aria-expanded", abierto);
  $nav.setAttribute("aria-hidden", !abierto);
  $nav.toggleAttribute("inert", !abierto);
  $navBg.toggleAttribute("data-visible", abierto);
}

// hacer cambios al abrir o cerrar el menú
van.derive(() => {
  cambiarEstadoMenu(abierto.val);
  if (abierto.val) window.addEventListener("mousedown", cerrarPorClickAfuera);
});

anchoMedia.addEventListener
  ? anchoMedia.addEventListener("change", (e) => cambiarEstadoMenu(e.matches))
  : anchoMedia.addListener((e) => cambiarEstadoMenu(e.matches));
