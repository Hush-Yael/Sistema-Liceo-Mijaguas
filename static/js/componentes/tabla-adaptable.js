document.addEventListener("alpine:init", () => {
  Alpine.data("tablaAdaptable", (config) => ({
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

    init() {
      if (config.hayColumnasOcultables) {
        // si no hay filas, agregar un atributo para agregar ciertos estilos ya que no se pueden seleccionar
        if (!this.$el.$("[name=filas_id]"))
          this.$el.setAttribute("data-sin-filas-seleccionar", "");

        // ubicar el cambiador de columnas en el primer <th>
        Alpine.effect(() => {
          this.$el
            .$(`th[data-i='${this.indiceColActual}']>div`)
            .appendChild(this.$el.$("#selector-columna"));
        });
      }
    },
  }));
});
