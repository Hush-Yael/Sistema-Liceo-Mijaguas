let valorErrorActual = "";

/** @type { Map<string, { input: HTMLInputElement, valorError: string | unknown }> } */
const inputsLimpiados = new Map();

$$("form").forEach((form) => {
  form.addEventListener("focus", rastrearErrorInputActual, true);
  form.onchange = limpiarAlCambiar;
  form.onreset = limpiarAlReiniciar;
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

// verificar si se vuelve a introducir un valor erróneo o si se introduce uno diferente
/** @param {Event} e */
function limpiarAlCambiar(e) {
  if (e.target !== e.currentTarget) {
    /** @type {HTMLInputElement} */
    const campo = e.target;

    // eliminar los atributos y guardar el valor erróneo anterior del input
    if (campo.hasAttribute("aria-invalid")) {
      const wrapper = campo.closest("[data-invalido]");
      if (wrapper) wrapper.setAttribute("data-invalido", "false");

      campo.removeAttribute("aria-invalid");
      inputsLimpiados.set(campo.id || campo.name, {
        campo,
        valorError: valorErrorActual,
      });
    } else {
      const limpiado = inputsLimpiados.get(campo.id);

      // si se vuelve a introducir el valor erróneo en el mismo campo, volver a mostrar el error
      if (limpiado && limpiado.valorError === campo.value) {
        const wrapper = campo.closest("[data-invalido]");
        if (wrapper) wrapper.setAttribute("data-invalido", "true");

        campo.setAttribute("aria-invalid", "true");
        campo.setAttribute("aria-errormessage", "error");
        inputsLimpiados.delete(campo.id);
      }
    }
  }
}

// elimina los errores al reiniciar el formulario
/** @param {Event} e */
function limpiarAlReiniciar(e) {
  /** @type {HTMLFormElement} */
  const form = e.target;

  /** @type {HTMLElement[]} */
  const camposConErrores = Array.from(form.$$("input[aria-invalid='true']"));
  const mensajesErrores = Array.from(form.$$(".input-error"));

  if (form.id) {
    const camposConErroresFuera = $$(
      "input[aria-invalid='true'][form='" + form.id + "']",
    );
    camposConErroresFuera.length &&
      camposConErrores.push(...camposConErroresFuera);

    const mensajesErroresFuera = $$(`.input-error[data-form="${form.id}"]`);
    mensajesErroresFuera.length &&
      mensajesErrores.push(...mensajesErroresFuera);
  }

  camposConErrores.forEach((input) => {
    input.removeAttribute("aria-invalid");
    input.removeAttribute("aria-errormessage");
    inputsLimpiados.delete(input.id);
  });

  mensajesErrores.forEach((mensaje) => mensaje.remove());
}
