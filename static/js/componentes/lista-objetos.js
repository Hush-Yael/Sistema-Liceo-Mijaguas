"use strict";

document.addEventListener("alpine:init", () => {
  Alpine.data("listaObjetos", (config) => {
    // Estados de selección
    const seleccion = {
      /** @type { Set<number> } */
      filasSeleccionadas: new Set(),
      /** @type { Set<number> } */
      ids: new Set(),
      shiftKey: false,
      /** @type { null | string } */
      ultimaSeleccionadaIndice: null,
      /** @param { KeyboardEvent & { target: HTMLElement } } e */
      cambiarTabIndex(e) {
        e.target.tabIndex = -1;
        setTimeout(() => (this.$focus.focused().tabIndex = 0));
      },
    };

    /** @type { boolean } */
    const tablaConColumnasOcultas =
      config.tabla && config.hayColumnasOcultables;

    const datos = {
      ...seleccion,
      init() {
        if (tablaConColumnasOcultas) {
          // obtener los ids de las filas
          this.$el
            .$$("[name=filas_id]")
            .forEach((el) => this.ids.add(el.value));

          // si no hay filas, agregar un atributo para agregar ciertos estilos ya que no se pueden seleccionar
          if (!this.$el.$("[name=filas_id]"))
            this.$el.setAttribute("data-sin-filas-seleccionar", "");

          // ubicar el cambiador de columnas en el primer <th>
          Alpine.effect(() => {
            this.$el
              .$(`th[data-i='${this.indiceColActual}']>div`)
              .appendChild(this.$el.$("#columna-cambiador"));
          });
        }

        Alpine.bind(this.$el, {
          // desactivar la variable shiftKey al soltar la tecla Shift
          "x-on:keyup"() {
            if (!this.$event.shiftKey) this.shiftKey = false;
          },
          // Abrir el modal de eliminar al presionar la tecla Delete en un input para seleccionar filas
          "x-on:keydown.delete"() {
            if (
              this.$event.target.matches("input") &&
              this.filasSeleccionadas.size
            )
              this.modalAbierto = "eliminar";
          },
          // Selección de filas individual y múltiple
          "x-on:change"() {
            const el = this.$event.target;

            if (el.id === "seleccionar-todos") {
              this.ultimaSeleccionadaIndice = null;
              this.filasSeleccionadas.size === this.ids.size
                ? this.filasSeleccionadas.clear()
                : (this.filasSeleccionadas = new Set(this.ids));
            } else if (el.name === "filas_id") {
              if (this.shiftKey && this.ultimaSeleccionadaIndice !== null) {
                const start = Math.min(
                  this.ultimaSeleccionadaIndice,
                  el.dataset.i,
                );
                const end = Math.max(
                  this.ultimaSeleccionadaIndice,
                  el.dataset.i,
                );

                let i = 0;
                this.ids.forEach((id) => {
                  if (i >= start && i <= end) this.filasSeleccionadas.add(id);
                  i++;
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

        Alpine.bind(config.contenedorManejoTeclas || this.$el, {
          // Navegar entre elementos enfocables de la tabla, para no tener que usar Tab
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
      },
    };

    // si la tabla tiene columnas ocultas, agregar las funciones necesarias para controlar el cambio de columnas
    if (tablaConColumnasOcultas) {
      const tabla = {
        /** @type { number } */
        indiceColActual: config.indiceColActual || 0,
        /** @type { string } */
        tituloColActual: config.tituloColActual || "",
        anteriorCol() {
          if (this.indiceColActual > 0) this.indiceColActual--;
        },
        siguienteCol() {
          if (this.indiceColActual < this.columnasOcultables.length - 1)
            this.indiceColActual++;
        },
        columnasOcultables: config.columnasOcultables || [],
      };

      return { ...tabla, ...datos };
    }

    return datos;
  });
});
