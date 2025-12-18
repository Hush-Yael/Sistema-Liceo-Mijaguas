/** @type null | HTMLInputElement */
let ultimoSeleccionado = null;

/** @param {Event} e */
$id("filtros").addEventListener("change", function (e) {
  /** @type HTMLInputElement */
  const inputCambiado = e.target;
  const name = inputCambiado.name;

  // opción "todas" seleccionada, se deseleccionan las demás
  if (inputCambiado.type === "radio") {
    const inputs = $$(`[name=${name}]`);

    inputs.forEach(
      (input) => input !== inputCambiado && (input.checked = false),
    );
  }
  // opción que no es "todas" seleccionada, se deselecciona "todas"
  else {
    const inputNinguno = $(`[name=${inputCambiado.name}].ninguno`);
    const alMenosUno = $(`[name=${inputCambiado.name}]:checked`);

    inputNinguno.checked = !alMenosUno;
  }
});

// selección múltiple
/** @param {Event} e */
$id("filtros").addEventListener("click", function (e) {
  if (e.target.type !== "checkbox") return;
  /** @type HTMLInputElement */
  const opcionActual = e.target;

  // guardar la última opción seleccionada, para usarla como referencia en el siguiente click
  if (!ultimoSeleccionado) return (ultimoSeleccionado = opcionActual);

  // si se presiona shift, se seleccionan todas las opciones entre el última seleccionada y la actual
  if (e.shiftKey) {
    const opciones = Array.from($$('input[type="checkbox"]'));
    const inicio = opciones.indexOf(opcionActual);
    const fin = opciones.indexOf(ultimoSeleccionado);
    const indiceInicio = Math.min(inicio, fin);
    const indiceFin = Math.max(inicio, fin) + 1;

    opciones
      .slice(indiceInicio, indiceFin)
      .forEach((opcion) => (opcion.checked = ultimoSeleccionado.checked));
  }
  ultimoSeleccionado = opcionActual;
});
