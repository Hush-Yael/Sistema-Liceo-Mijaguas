/** @import { Tema } from  '../aplicar-tema' */
/** @import { State } from  '../van-1.6.0' */

const $nav = $id("nav");
const $selectorTema = $id("tema-selector");
const temaAutoMedia = window.matchMedia("(prefers-color-scheme: dark)");

/** @type {State<Tema>} */
const tema = van.state(localStorage.getItem("tema"));

/** @param {boolean} esOscuro */
const cambiarTemaClase = (esOscuro) =>
  document.documentElement.classList.toggle("oscuro", esOscuro);

// validar el tema seleccionado y aplicarlo al documento
van.derive(() => {
  let t = tema.val;

  if (!TEMA_VALORES.includes(t)) {
    t = TEMA_POR_DEFECTO;
    tema.val = t;
  }

  try {
    $selectorTema.$("input[value='" + t + "']").checked = true;
  } catch (e) {
    if (!(e instanceof TypeError)) throw e;
  }

  localStorage.setItem("tema", t);

  const esOscuro = t === "oscuro" || (t === "auto" && temaAutoMedia.matches);
  if (!document.startViewTransition) cambiarTemaClase(esOscuro);
  else document.startViewTransition(() => cambiarTemaClase(esOscuro));

  // cambio automático si se selecciona 'auto'
  if (tema === "auto")
    temaAutoMedia.addEventListener
      ? temaAutoMedia.addEventListener("change", cambioAutoTema)
      : temaAutoMedia.addListener(cambioAutoTema);
  // se elimina el cambio automático con otro valor
  else
    temaAutoMedia.removeEventListener
      ? temaAutoMedia.removeEventListener("change", cambioAutoTema)
      : temaAutoMedia.removeListener(cambioAutoTema);
});

$selectorTema.addEventListener("change", function () {
  /** @type Tema */
  let val;

  try {
    // valor seleccionado
    val = $selectorTema.$("input:checked").value;
  } catch (e) {
    // no se encontró el <input>, se usa el valor por defecto
    if (e instanceof TypeError) val = TEMA_POR_DEFECTO;
    else throw e;
  }

  tema.val = val;
});

/** @param {MediaQueryList} e */
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
