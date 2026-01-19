"use strict";
/** @typedef {{ id: string, label: string }} ComboboxOpcion */

document.addEventListener("alpine:init", () => {
  Alpine.data("combobox", (config) => ({
    /** @type { boolean } */
    abierto: config.abierto || false,
    /** @type { boolean } */
    abiertoPorTeclado: config.abierto || false,
    /** @type { boolean } */
    multiple: config.multiple || false,
    /** @type { ComboboxOpcion[] } **/
    opciones: config.opciones || [],
    /** @type { Set<number> } **/
    opcionesSeleccionadas: config.opcionesSeleccionadas || new Set(),
    /** @type { ComboboxOpcion['id'] | null } **/
    seleccionada: config.seleccionada || null,
    /** @type { HTMLInputElement | null } **/
    ultimaSeleccionada: null,
    /** @type { boolean } */
    shiftPresionado: false,
    q: "",
    /** @type { boolean } */
    mostrarCantidad: config.mostrarCantidad || false,
    /** @type { number } */
    cantidadFiltradas: config.opciones?.length || 0,
    establecerTextoLabel,
    destacarPrimeraCoincidencia,
    seleccionarOpcion,
    reiniciar,
    manejarTeclas,
    filtrarOpciones,
  }));
});

/**
 * @typedef {{
 *   opciones: ComboboxOpcion[],
 *   opcionesSeleccionadas: Set<number>,
 *   seleccionada: ComboboxOpcion['id'] | null,
 *   ultimaSeleccionada: HTMLInputElement | null,
 *   shiftPresionado: boolean,
 *   multiple: boolean,
 *   reiniciar: () => void,
 *   q: string,
 *   mostrarCantidad: boolean,
 *   cantidadFiltradas: number,
 *   $el: HTMLDivElement
 * }} ComboboxContext
 **/

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
  }
  // marcar una única opción como el valor seleccionado
  else this.seleccionada = opcion.value;
}

/** @this { ComboboxContext } **/
function reiniciar() {
  if (this.multiple) this.opcionesSeleccionadas.clear();
  else this.seleccionada = null;
}

/**
 * @this { ComboboxContext }
 * @param { KeyboardEvent } e
 * **/
function manejarTeclas(e, $focus) {
  switch (e.key) {
    case "ArrowDown": {
      e.preventDefault();
      return $focus.wrap().next();
    }
    case "ArrowUp": {
      e.preventDefault();
      return $focus.wrap().previous();
    }
    case "Home": {
      if (e.target.type !== "text") {
        e.preventDefault();
        return $focus.wrap().first();
      }
    }
    case "End": {
      if (e.target.type !== "text") {
        e.preventDefault();
        return $focus.wrap().last();
      }
    }
    case "Enter": {
      if (e.target !== e.currentTarget && e.target.type !== "text") {
        e.preventDefault();
        e.target.checked = !e.target.checked;
        seleccionarOpcion(e.target);
      }
    }
  }

  this.shiftPresionado = e.shiftKey;
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
