let valorErrorActual = "";

document.querySelector("form").addEventListener(
  "focus",
  (e) => {
    const elemento = e.target;
    const input = elemento.matches("input");

    // guardar el valor erróneo del input al momento de corregirlo, para volver a mostrar el error si se vuelve a introducir
    if (input && elemento.hasAttribute("aria-invalid"))
      valorErrorActual = elemento.value;
    else valorErrorActual = "";
  },
  true
);

const limpiados = [];

document.querySelector("form").onchange = (e) => {
  const elemento = e.target;
  const input = elemento.matches("input");

  if (input) {
    // guardar el valor erróneo del input
    if (elemento.hasAttribute("aria-invalid")) {
      elemento.removeAttribute("aria-invalid");
      limpiados.push({ input, valorError: valorErrorActual });
    } else {
      const limpiado = limpiados.find((l) => l.input === input);

      // si se vuelve a introducir el valor erróneo en el mismo campo, volver a mostrar el error
      if (limpiado && limpiado.valorError === elemento.value) {
        elemento.setAttribute("aria-invalid", "true");
        elemento.setAttribute("aria-errormessage", "error");
        limpiados.splice(limpiados.indexOf(limpiado), 1);
      }
    }
  }
};
