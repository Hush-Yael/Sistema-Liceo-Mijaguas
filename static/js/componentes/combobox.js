/** @typedef {{ id: number, label: string }} ComboboxOpcion */

/**
 * @typedef {{
 *   opciones: ComboboxOpcion[],
 *   opcionesSeleccionadas: Set<number>,
 *   seleccionada: ComboboxOpcion['id'] | null,
 *   ultimaSeleccionada: HTMLInputElement | null,
 *   shiftPresionado: boolean,
 *   multiple: boolean,
 *   reiniciar: () => void,
 *   $el: HTMLDivElement
 * }} ComboboxContext
 **/

/** @this {ComboboxContext} **/
// oxlint-disable-next-line no-unused-vars
function establecerTextoLabel() {
  if (this.multiple) {
    if (!this.opcionesSeleccionadas.size) return;

    // hay al menos una opción seleccionada, mostrarlas separadas por comas
    return this.opciones
      .filter((item) => this.opcionesSeleccionadas.has(item.id))
      .map((item) => item.label)
      .join(", ");
  } else
    return this.seleccionada
      ? this.opciones.find((item) => item.id === this.seleccionada).label
      : "";
}

/**
 *  @this {ComboboxContext}
 *  @param {KeyboardEvent['key']} teclaPresionada
 * **/
// oxlint-disable-next-line no-unused-vars
function destacarPrimeraCoincidencia(teclaPresionada) {
  // no destacar nada si se presiona enter
  if (teclaPresionada === "Enter") return;

  // encontrar la opción que comienza con la tecla presionada para enfocarla
  const opcion = this.opciones.find((item) =>
    item.label.toLowerCase().startsWith(teclaPresionada.toLowerCase()),
  );

  if (opcion) {
    const indice = this.opciones.indexOf(opcion);
    /** @type {NodeListOf<HTMLInputElement>} */
    const $todasLasOpciones = this.$el.$$(".combobox-opcion");

    if ($todasLasOpciones[indice]) $todasLasOpciones[indice].focus();
  }
}

/**
 * @this {ComboboxContext}
 * @param {HTMLInputElement} opcion
 * **/
// oxlint-disable-next-line no-unused-vars
function seleccionarOpcion(opcion) {
  // se pueden seleccionar más de una sola opción
  if (this.multiple) {
    /**
     * @this {ComboboxContext}
     * @param {HTMLInputElement} opcionActual
     * **/
    const variasOpciones = (opcionActual) => {
      // se acaba de seleccionar una opción
      const debeAñadir = opcionActual.checked;

      const inputs = Array.from(this.$el.$$(".combobox-opcion"));
      const inicio = inputs.indexOf(opcion);
      const fin = inputs.indexOf(this.ultimaSeleccionada);
      const indiceInicio = Math.min(inicio, fin);
      const indiceFin = Math.max(inicio, fin) + 1;

      console.log({ indiceInicio, indiceFin });

      for (let i = indiceInicio; i < indiceFin; i++)
        this.opcionesSeleccionadas[debeAñadir ? "add" : "delete"](
          inputs[i].value,
        );

      this.shiftPresionado = false;
      return (this.ultimaSeleccionada = null);
    };

    if (
      opcion.type === "checkbox" &&
      this.shiftPresionado &&
      this.ultimaSeleccionada
    )
      variasOpciones(opcion);
    else {
      // añadir la opción marcada al Set de opciones seleccionadas
      if (opcion.checked) this.opcionesSeleccionadas.add(opcion.value);
      // remover la opción desmarcada del Set de opciones seleccionadas
      else this.opcionesSeleccionadas.delete(opcion.value);

      // guardar la última opción seleccionada, para usarla como referencia en el siguiente cambio, si se presiona shift
      this.ultimaSeleccionada = opcion;
    }
  }
  // marcar una única opción como el valor seleccionado
  else this.seleccionada = opcion.value;
}

/** @this {ComboboxContext} **/
// oxlint-disable-next-line no-unused-vars
function reiniciar() {
  if (this.multiple) this.opcionesSeleccionadas.clear();
  else this.seleccionada = null;
}
