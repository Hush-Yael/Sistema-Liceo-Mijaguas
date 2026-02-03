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

document.addEventListener("alpine:init", () => {
  Alpine.data("listaObjetos", (config) => ({
    /** @type { Set<number> } */
    filasSeleccionadas: new Set(),
    /** @type { number[] } */
    ids: [],
    shiftKey: false,
    /** @type { null | string } */
    ultimaSeleccionadaIndice: null,
    /** @type { string | null } */
    modalAbierto: config.modalAbierto || null,

    /**
     * @param { KeyboardEvent & { target: HTMLElement } } e
     * @this Contexto
     **/
    cambiarTabIndex(e) {
      e.target.tabIndex = -1;
      setTimeout(() => (this.$focus.focused().tabIndex = 0));
    },

    /** @this Contexto */
    limpiarSeleccion() {
      this.ultimaSeleccionadaIndice = null;
      this.filasSeleccionadas.clear();
    },

    /** @this Contexto */
    limpiarSeleccionTodo() {
      this.ultimaSeleccionadaIndice = null;
      this.ids.forEach((id) => this.filasSeleccionadas.delete(id));
    },

    /** @this Contexto */
    seleccionarTodo() {
      this.ultimaSeleccionadaIndice = null;
      this.filasSeleccionadas = new Set([
        ...this.filasSeleccionadas,
        ...this.ids,
      ]);
    },

    /** @this Contexto */
    alternarSeleccionTodo() {
      this.ids.every((id) => this.filasSeleccionadas.has(id))
        ? this.limpiarSeleccionTodo()
        : this.seleccionarTodo();
    },

    /** @this Contexto */
    cargarIds() {
      // Establecer los ids disponibles de la lista al esta cargarse
      this.ids = Array.from(this.$el.$$("[name=filas_id]"), (el) => el.value);
    },

    /** @this Contexto */
    init() {
      Alpine.bind(this.$el, {
        /** @this Contexto */
        // desactivar la variable shiftKey al soltar la tecla Shift
        "x-on:keyup"() {
          if (!this.$event.shiftKey) this.shiftKey = false;
        },

        /** @this Contexto */
        // Abrir el modal de eliminar al presionar la tecla Delete en un input para seleccionar filas
        "x-on:keydown.delete"() {
          if (
            this.$event.target.matches("[name=filas_id]") &&
            this.filasSeleccionadas.size
          )
            this.modalAbierto = "eliminar";
        },

        /** @this Contexto */
        // Selección de filas individual y múltiple
        "x-on:change"() {
          const el = this.$event.target;

          if (el.name === "filas_id") {
            // seleccion en rango
            if (this.shiftKey && this.ultimaSeleccionadaIndice !== null) {
              const start = Math.min(
                this.ultimaSeleccionadaIndice,
                el.dataset.i,
              );
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
      });

      if (config.contenedorManejoTeclas)
        Alpine.bind(config.contenedorManejoTeclas, {
          /** @this Contexto */
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
        });
      else console.warn("No se indicó el contenedor que maneja las teclas");
    },

    ...config,
  }));
});
