const nav = document.getElementById("nav");
const urlActual = nav.getAttribute("data-path-actual");
const links = nav.querySelectorAll("a");

links.forEach((link) => {
  if (location.origin + urlActual.trim() === link.href)
    link.setAttribute("aria-current", "page");
});

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

menuSelector.addEventListener("change", aplicarTema);

const bg = document.getElementById("nav-bg");
const abierto = van.state(false);

function cerrarPorClickAfuera(e) {
  const padre = e.target.closest("#nav");

  if (padre === null) {
    // cerrar el nav si se hace click fuera de el y si no se trata del botón de abrir el nav
    if (!e.target.closest("#btn-nav")) abierto.val = false;
    window.removeEventListener("mousedown", cerrarPorClickAfuera);
  }
}

const btnNav = document.getElementById("btn-nav");
btnNav.onclick = () => (abierto.val = !abierto.oldVal);

van.derive(() => {
  btnNav.setAttribute("aria-expanded", abierto.val);
  nav.setAttribute("aria-hidden", !abierto.val);
  nav.toggleAttribute("inert", !abierto.val);
  bg.toggleAttribute("data-visible", abierto.val);

  if (abierto.val) window.addEventListener("mousedown", cerrarPorClickAfuera);
});
