let valorErrorActual = "";

/** @type {{input: HTMLInputElement, error: string}[]} */
const inputsLimpiados = [];

$$("form").forEach((form) => {
  form.addEventListener("focus", rastrearErrorInputActual, true);

  form.onchange = limpiarAlCambiar;
});

// guarda el valor erróneo del input al momento de enfocarlo, para verificar cuando se vuelva a introducir o desenfocar
/** @param {Event} e */
function rastrearErrorInputActual(e) {
  const elemento = e.target;
  const input = elemento.matches("input");

  // guardar el valor erróneo del input al momento de corregirlo, para volver a mostrar el error si se vuelve a introducir
  if (input && elemento.hasAttribute("aria-invalid"))
    valorErrorActual = elemento.value;
  else valorErrorActual = "";
}

// si se vuelve a introducir el valor erróneo en el mismo campo, volver a mostrar el error
/** @param {Event} e */
function limpiarAlCambiar(e) {
  /** @type {HTMLElement} */
  const elemento = e.target;
  const input = elemento.matches("input");

  if (input) {
    // guardar el valor erróneo del input
    if (elemento.hasAttribute("aria-invalid")) {
      elemento.removeAttribute("aria-invalid");
      inputsLimpiados.push({ input, valorError: valorErrorActual });
    } else {
      const limpiado = inputsLimpiados.find((l) => l.input === input);

      // si se vuelve a introducir el valor erróneo en el mismo campo, volver a mostrar el error
      if (limpiado && limpiado.valorError === elemento.value) {
        elemento.setAttribute("aria-invalid", "true");
        elemento.setAttribute("aria-errormessage", "error");
        inputsLimpiados.splice(inputsLimpiados.indexOf(limpiado), 1);
      }
    }
  }
}
