"use strict";

/**
 * @typedef {{
 *  filasSeleccionadas: Set<number>
 *  ids: number[]
 *  shiftKey: false,
 *  ultimaSeleccionadaIndice: null | string
 *  modalAbierto: string | null
 * }} Contexto
 **/

// oxlint-disable-next-line no-unused-vars
const ListaObjetos = class {
  /** @param { Contexto } config */
  constructor(config) {
    Object.assign(this, config);

    /** @type { Set<number> } */
    this.filasSeleccionadas = new Set();
    /** @type { number[] } */
    this.ids = [];
    this.shiftKey = false;
    /** @type { null | string } */
    this.ultimaSeleccionadaIndice = null;
    /** @type { string | null } */
    this.modalAbierto = config.modalAbierto || null;

    this.eventos = {
      // desactivar la variable shiftKey al soltar la tecla Shift
      "x-on:keyup"() {
        if (!this.$event.shiftKey) this.shiftKey = false;
      },

      // Abrir el modal de eliminar al presionar la tecla Delete en un input para seleccionar filas
      "x-on:keydown.delete"() {
        if (
          this.$event.target.matches("[name=filas_id]") &&
          this.filasSeleccionadas.size
        )
          this.modalAbierto = "eliminar";
      },

      // Selección de filas individual y múltiple
      "x-on:change"() {
        const el = this.$event.target;

        if (el.name === "filas_id") {
          // seleccion en rango
          if (this.shiftKey && this.ultimaSeleccionadaIndice !== null) {
            const start = Math.min(this.ultimaSeleccionadaIndice, el.dataset.i);
            const end = Math.max(this.ultimaSeleccionadaIndice, el.dataset.i);

            if (start === end)
              return this.filasSeleccionadas.has(el.value)
                ? this.filasSeleccionadas.delete(el.value)
                : this.filasSeleccionadas.add(el.value);

            if (Number.isInteger(start) && Number.isInteger(end))
              this.ids.forEach((id, i) => {
                if (i >= start && i <= end) this.filasSeleccionadas.add(id);
              });
          } else {
            this.ultimaSeleccionadaIndice = el.dataset.i;
            el.checked
              ? this.filasSeleccionadas.add(el.value)
              : this.filasSeleccionadas.delete(el.value);
          }
        }
      },
    };

    this.eventosLista = {
      // Navegar entre elementos enfocables de la lista, para no tener que usar Tab
      "x-on:keydown"() {
        /** @type { KeyboardEvent } */
        const e = this.$event;
        // activar la variable shiftKey al presionar la tecla Shift
        if (e.shiftKey) this.shiftKey = true;

        switch (e.key) {
          case "ArrowDown": {
            e.preventDefault();
            this.$focus.wrap().next();
            return this.cambiarTabIndex(e);
          }
          case "ArrowUp": {
            e.preventDefault();
            this.$focus.wrap().previous();
            return this.cambiarTabIndex(e);
          }
          case "Home": {
            e.preventDefault();
            this.$focus.first();
            return this.cambiarTabIndex(e);
          }
          case "End": {
            e.preventDefault();
            this.$focus.last();
            return this.cambiarTabIndex(e);
          }
        }
      },
    };
  }

  /** @param { KeyboardEvent & { target: HTMLElement } } e */
  cambiarTabIndex(e) {
    e.target.tabIndex = -1;
    setTimeout(() => (this.$focus.focused().tabIndex = 0));
  }

  limpiarSeleccion() {
    this.ultimaSeleccionadaIndice = null;
    this.filasSeleccionadas.clear();
  }

  limpiarSeleccionTodo() {
    this.ultimaSeleccionadaIndice = null;
    this.ids.forEach((id) => this.filasSeleccionadas.delete(id));
  }

  seleccionarTodo() {
    this.ultimaSeleccionadaIndice = null;
    this.filasSeleccionadas = new Set([
      ...this.filasSeleccionadas,
      ...this.ids,
    ]);
  }

  alternarSeleccionTodo() {
    this.ids.every((id) => this.filasSeleccionadas.has(id))
      ? this.limpiarSeleccionTodo()
      : this.seleccionarTodo();
  }

  cargarIds() {
    // Establecer los ids disponibles de la lista al esta cargarse
    this.ids = Array.from(this.$el.$$("[name=filas_id]"), (el) => el.value);
  }
};
