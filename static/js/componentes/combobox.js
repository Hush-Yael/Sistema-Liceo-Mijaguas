"use strict";
/** @typedef {{ id: string, label: string }} ComboboxOpcion */

/**
 * @typedef {{
 *   opciones: ComboboxOpcion[],
 *   opcionesSeleccionadas: Set<number>,
 *   seleccionada: ComboboxOpcion['id'] | null,
 *   ultimaSeleccionada: HTMLInputElement | null,
 *   name: string | null,
 *   ultimoValorIncorrecto: number | null,
 *   valorErroneoIntroducido: boolean,
 *   shiftPresionado: boolean,
 *   multiple: boolean,
 *   reiniciar: () => void,
 *   q: string,
 *   mostrarCantidad: boolean,
 *   cantidadFiltradas: number,
 *   $el: HTMLDivElement,
 *   $refs: Record<string, HTMLElement>
 * }} ComboboxContext
 **/

/** @param { ComboboxContext } config */
// oxlint-disable-next-line no-unused-vars
function combobox(config) {
  return {
    ...config,
    multiple: config.multiple || false,
    opciones: config.opciones || [],
    opcionesSeleccionadas: config.opcionesSeleccionadas || new Set(),
    seleccionada: config.seleccionada || null,
    name: config.name,
    valorErroneoIntroducido: config.valorErroneoIntroducido || false,
    /** @type { number | null } */
    ultimoValorIncorrecto: null,
    /** @type { HTMLInputElement | null } **/
    ultimaSeleccionada: null,
    /** @type { boolean } */
    shiftPresionado: false,
    q: "",
    mostrarCantidad: config.mostrarCantidad || false,
    cantidadFiltradas: config.opciones?.length || 0,
    establecerTextoLabel,
    destacarPrimeraCoincidencia,
    seleccionarOpcion,
    reiniciar,
    filtrarOpciones,
    verificarEstadoError,
    reintroducirError,
    limpiarError,

    ...config,
  };
}

/**
 * @this { ComboboxContext }
 * @returns { string }
 **/
function establecerTextoLabel() {
  if (this.multiple) {
    if (!this.opcionesSeleccionadas.size) return;

    // hay al menos una opción seleccionada, mostrarlas separadas por comas
    return this.opciones
      .filter((item) => this.opcionesSeleccionadas.has(item.id))
      .map((item) => item.label)
      .join(", ");
  } else {
    if (this.seleccionada) {
      const seleccionada = this.opciones.find(
        (item) => item.id === this.seleccionada,
      );
      if (seleccionada) return seleccionada.label;
    }

    return "";
  }
}

/**
 *  @this { ComboboxContext }
 *  @param { KeyboardEvent['key'] } teclaPresionada
 * **/
function destacarPrimeraCoincidencia(teclaPresionada) {
  // no destacar nada si se presiona enter
  if (teclaPresionada === "Enter") return;

  // encontrar la opción que comienza con la tecla presionada para enfocarla
  const opcion = this.opciones.find((item) =>
    item.label.toLowerCase().startsWith(teclaPresionada.toLowerCase()),
  );

  if (opcion) {
    const indice = this.opciones.indexOf(opcion);
    /** @type { NodeListOf<HTMLInputElement> } */
    const $todasLasOpciones = this.$el.$$(".combobox-opcion");

    if ($todasLasOpciones[indice]) $todasLasOpciones[indice].focus();
  }
}

/**
 * @this { ComboboxContext }
 * @param { HTMLInputElement } opcion
 * **/
function seleccionarOpcion(opcion) {
  // se pueden seleccionar más de una sola opción
  if (this.multiple) {
    /** @param { HTMLInputElement } opcionActual **/
    const variasOpciones = (opcionActual) => {
      // se acaba de seleccionar una opción
      const debeAñadir = opcionActual.checked;

      const inputs = Array.from(this.$el.$$(".combobox-opcion"));
      const inicio = inputs.indexOf(opcion);
      const fin = inputs.indexOf(this.ultimaSeleccionada);
      const indiceInicio = Math.min(inicio, fin);
      const indiceFin = Math.max(inicio, fin) + 1;

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

    limpiarError(this.$refs);
  }

  // marcar una única opción como el valor seleccionado
  else {
    this.seleccionada = opcion.value;
    this.verificarEstadoError(this.refs);
  }
}

/** @this { ComboboxContext } ***/
function verificarEstadoError() {
  if (this.valorErroneoIntroducido) {
    if (this.ultimoValorIncorrecto === this.seleccionada)
      this.reintroducirError();
    else this.limpiarError();
  }
}

/** @this { ComboboxContext } ***/
function reintroducirError() {
  const refs = this.$refs;

  if (this.name) {
    refs.contenedor.setAttribute("data-invalido", "true");
    refs.trigger.setAttribute("aria-invalid", "true");
    refs.trigger.setAttribute("aria-errormessage", this.name + "-error");
  }
}

/** @this { ComboboxContext } ***/
function limpiarError() {
  /** @type { Record<string, HTMLElement> } */
  const refs = this.$refs;

  if (refs.trigger.hasAttribute("aria-invalid")) {
    refs.contenedor.setAttribute("data-invalido", "false");
    refs.trigger.setAttribute("aria-invalid", "false");
    refs.trigger.removeAttribute("aria-errormessage");
  }
}

/** @this { ComboboxContext } **/
function reiniciar() {
  if (this.multiple) {
    this.opcionesSeleccionadas.clear();
    this.limpiarError();
  } else {
    this.seleccionada = null;
    this.verificarEstadoError();
  }

  this.$el.dispatchEvent(new Event("change", { bubbles: true }));
}

/** @this { ComboboxContext } **/
function filtrarOpciones() {
  let busqueda = this.q.trim();

  if (busqueda) {
    busqueda = busqueda
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "");

    const filtradas = this.opciones.filter((opcion) =>
      opcion.label
        .toLowerCase()
        .normalize("NFD")
        .normalize("NFD")
        .replace(/\p{Diacritic}/gu, "")
        .includes(busqueda),
    );

    if (filtradas.length === 0)
      this.$refs.sinResultadosMsj.removeAttribute("style");
    else this.$refs.sinResultadosMsj.style.display = "none";

    if (this.mostrarCantidad) this.cantidadFiltradas = filtradas.length;
    return filtradas;
  }

  this.$refs.sinResultadosMsj.style.display = "none";

  if (this.mostrarCantidad) this.cantidadFiltradas = this.opciones.length;
  return this.opciones;
}
