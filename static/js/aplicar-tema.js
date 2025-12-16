/** @typedef {"claro" |"oscuro" | "auto"} Tema */

/** @type {Tema[]} */
const TEMA_VALORES = ["claro", "oscuro", "auto"];

/** @type Tema */
const TEMA_POR_DEFECTO = "auto";

let temaGuardado = localStorage.getItem("tema");

if (!TEMA_VALORES.includes(temaGuardado)) {
  temaGuardado = TEMA_POR_DEFECTO;
  localStorage.setItem("tema", TEMA_POR_DEFECTO);
}

if (temaGuardado !== "claro") {
  const auto = window.matchMedia("(prefers-color-scheme: dark)");
  document.documentElement.classList.toggle(
    "oscuro",
    temaGuardado === "oscuro" || (temaGuardado === "auto" && auto.matches),
  );
}
