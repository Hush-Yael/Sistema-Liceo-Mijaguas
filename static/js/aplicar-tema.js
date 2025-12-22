/** @typedef {"claro" |"oscuro" | "auto"} Tema */

/** @type {Tema[]} */
const TEMA_VALORES = ["claro", "oscuro", "auto"];

/** @type Tema */
const TEMA_POR_DEFECTO = "auto";

// oxlint-disable-next-line no-unused-vars
const temaAutoMedia = window.matchMedia("(prefers-color-scheme: dark)");

/** @param {Tema} t */
const cambiarTemaClase = (t) =>
  document.documentElement.classList.toggle(
    "oscuro",
    t === "oscuro" || (t === "auto" && temaAutoMedia.matches),
  );

/**
 * @param {Tema} t
 * @param {boolean} conTransicion
 * @description conTransicion se usa para evitar que se ejecute la transición la primera vez que se aplica el tema, ya que la página estaría cargando por la primera vez
 * */
function aplicarTema(t, conTransicion = false) {
  if (!conTransicion || !document.startViewTransition) cambiarTemaClase(t);
  else document.startViewTransition(() => cambiarTemaClase(t));

  localStorage.setItem("tema", t);
}

/** @param {Tema} valor */
// oxlint-disable-next-line no-unused-vars
function verificarTema(valor) {
  return !TEMA_VALORES.includes(valor) ? TEMA_POR_DEFECTO : valor;
}

aplicarTema(verificarTema(localStorage.getItem("tema")));
