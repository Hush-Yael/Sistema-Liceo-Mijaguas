"use strict";
/** @typedef {{ id: number, label: string }} Opcion */
/** @typedef {{ label: string, opciones: Opcion[] }} GrupoOpciones */
/** @typedef { "disponibles" | "seleccionadas" } CualLista */

/**
 * @typedef {{
 *   opciones: Opcion[],
 *   seleccionadasPorDefecto: Set<number>,
 *   opcionesDisponibles: Opcion[],
 *   opcionesSeleccionadas: Opcion[],
 *   seleccionesVisualesEn: Set<number>,
 *   ultimaSeleccionadaIndice: number | null,
 *   opcionesAgrupadas: boolean,
 * }} Contexto
 **/

// Componente reutilizable de selección bidireccional
document.addEventListener("alpine:init", () => {
  Alpine.data("selectorListaDual", (config) => ({
    // Estado inicial
    /** @type {Contexto['opciones']} */
    opciones: config.opciones || [],
    /** @type {Contexto['seleccionadas']} */
    seleccionadas: config.seleccionadas || new Set(),
    /** @type {Contexto['seleccionesVisualesEn']} */
    seleccionesVisualesEnIzquierda: new Set(),
    /** @type {Contexto['seleccionesVisualesEn']} */
    seleccionesVisualesEnDerecha: new Set(),
    /** @type {Contexto['ultimaSeleccionadaIndice']} */
    ultimaSeleccionadaIndice: null,
    busquedaDisponibles: "",
    busquedaSeleccionadas: "",
    /** @type { Contexto['opcionesDisponibles'] } */
    opcionesDisponibles: null,
    /** @type { Contexto['opcionesSeleccionadas'] } */
    opcionesSeleccionadas: null,
    /** @type { Contexto['opcionesAgrupadas'] } */
    opcionesAgrupadas: config.opcionesAgrupadas || false,
    esTactil: window.matchMedia("(hover: none) and (pointer: coarse)").matches,
    /** @type { Contexto['opciones'] } */
    _flatOpcionesDisponibles: null,
    /** @type { Contexto['opciones'] } */
    _flatOpcionesSeleccionadas: null,

    // establecer las opciones disponibles y seleccionadas con un efecto en vez de usar getters, de modo que se actualicen cuando cambien y no se tenga que filtrar cada vez que se acceden a ellas
    init() {
      const tactilMedia = window.matchMedia(
        "(hover: none) and (pointer: coarse)",
      );
      tactilMedia.addEventListener(
        "change",
        (e) => (this.esTactil = e.matches),
      );
      this.esTactil = tactilMedia.matches;

      Alpine.effect(() => {
        if (this.opcionesAgrupadas) {
          this.opcionesDisponibles = this.opciones.map(
            /** @param { GrupoOpciones } grupo */
            (grupo) => ({
              label: grupo.label,
              opciones: grupo.opciones.filter(
                (opcion) => !this.seleccionadas.has(opcion.id),
              ),
            }),
          );

          this._flatOpcionesDisponibles = this.opcionesDisponibles.flatMap(
            (grupo) => grupo.opciones,
          );

          this.opcionesSeleccionadas = this.opciones.map(
            /** @param { GrupoOpciones } grupo */
            (grupo) => ({
              label: grupo.label,
              opciones: grupo.opciones.filter((opcion) =>
                this.seleccionadas.has(opcion.id),
              ),
            }),
          );

          this._flatOpcionesSeleccionadas = this.opcionesSeleccionadas.flatMap(
            (grupo) => grupo.opciones,
          );
        } else {
          this.opcionesDisponibles = this.opciones.filter(
            (opcion) => !this.seleccionadas.has(opcion.id),
          );

          this.opcionesSeleccionadas = this.opciones.filter((opcion) =>
            this.seleccionadas.has(opcion.id),
          );
        }
      });
    },

    /**
     * @param { Contexto['cualLista'] } cualLista
     * @param { number }  id
     **/
    visualmenteSeleccionada(cualLista, id) {
      const seleccionesVisuales =
        cualLista === "disponibles"
          ? this.seleccionesVisualesEnIzquierda
          : this.seleccionesVisualesEnDerecha;

      return seleccionesVisuales.has(id);
    },

    /**
     * @param { Contexto['cualLista'] } cualLista
     * @param { number | null}  objetivoId
     **/
    alternarSeleccionVisual(cualLista, objetivoId) {
      /** @type { Contexto['opciones'] } */
      let opciones;

      if (this.opcionesAgrupadas)
        opciones =
          cualLista === "disponibles"
            ? this._flatOpcionesDisponibles
            : this._flatOpcionesSeleccionadas;
      else
        opciones =
          cualLista === "disponibles"
            ? this.opcionesDisponibles
            : this.opcionesSeleccionadas;

      const seleccionesVisuales =
        cualLista === "disponibles"
          ? this.seleccionesVisualesEnIzquierda
          : this.seleccionesVisualesEnDerecha;

      // Encontrar el índice de la opción
      const indiceActual = opciones.findIndex((opt) => opt.id === objetivoId);

      // Ctrl+Click: selección múltiple
      if (this.$event.ctrlKey || this.$event.metaKey) {
        if (seleccionesVisuales.has(objetivoId))
          seleccionesVisuales.delete(objetivoId);
        else seleccionesVisuales.add(objetivoId);

        this.ultimaSeleccionadaIndice = indiceActual;
      }
      // Shift+Click: seleccionar rango
      else if (this.$event.shiftKey && this.ultimaSeleccionadaIndice !== null) {
        const inicio = Math.min(this.ultimaSeleccionadaIndice, indiceActual);
        const fin = Math.max(this.ultimaSeleccionadaIndice, indiceActual);

        for (let i = inicio; i <= fin; i++)
          seleccionesVisuales.add(opciones[i].id);
      } else {
        if (seleccionesVisuales.has(objetivoId))
          seleccionesVisuales.delete(objetivoId);
        else {
          // Si no es por táctil y se hace click normal: seleccionar solo esta opción
          if (!this.esTactil) seleccionesVisuales.clear();
          seleccionesVisuales.add(objetivoId);
        }

        this.ultimaSeleccionadaIndice = indiceActual;
      }
    },

    /** @param { CualLista } cualLista */
    seleccionarVisualmenteTodo(cualLista) {
      /** @type { Contexto['opciones'] } */
      let opciones;

      if (this.opcionesAgrupadas)
        opciones =
          cualLista === "disponibles"
            ? this._flatOpcionesDisponibles
            : this._flatOpcionesSeleccionadas;
      else
        opciones =
          cualLista === "disponibles"
            ? this.opcionesDisponibles
            : this.opcionesSeleccionadas;

      const seleccionesVisuales =
        cualLista === "disponibles"
          ? this.seleccionesVisualesEnIzquierda
          : this.seleccionesVisualesEnDerecha;

      opciones.forEach((opcion) => seleccionesVisuales.add(opcion.id));

      this.ultimaSeleccionadaIndice = null;
    },

    /** @param { CualLista } cualLista */
    limpiarVisualmenteTodo(cualLista) {
      const seleccionesVisuales =
        cualLista === "disponibles"
          ? this.seleccionesVisualesEnIzquierda
          : this.seleccionesVisualesEnDerecha;

      seleccionesVisuales.clear();

      this.ultimaSeleccionadaIndice = null;
    },

    moverMarcadasASeleccionadas() {
      // Mover las selecciones visuales de disponibles a seleccionadas
      this.seleccionesVisualesEnIzquierda.forEach((id) => {
        this.seleccionadas.add(id);
        this.seleccionesVisualesEnIzquierda.delete(id);
      });
    },

    /** @param {number} id */
    moverASeleccionadas(id) {
      this.seleccionadas.add(id);
      this.seleccionesVisualesEnIzquierda.delete(id);
    },

    moverMarcadasADisponibles() {
      // Mover las selecciones visuales de seleccionadas a disponibles
      this.seleccionesVisualesEnDerecha.forEach((id) => {
        this.seleccionadas.delete(id);
        this.seleccionesVisualesEnDerecha.delete(id);
      });
    },

    /** @param {number} id */
    moverADisponibles(id) {
      this.seleccionadas.delete(id);
      this.seleccionesVisualesEnDerecha.delete(id);
    },

    moverTodasASeleccionadas() {
      // Mover todas las opciones disponibles a seleccionadas

      if (this.opcionesAgrupadas)
        this.opcionesDisponibles.forEach(
          /** @param { GrupoOpciones } grupo */
          (grupo) =>
            grupo.opciones.forEach((opcion) =>
              this.seleccionadas.add(opcion.id),
            ),
        );
      else
        this.opcionesDisponibles.forEach((opcion) =>
          this.seleccionadas.add(opcion.id),
        );
      this.limpiarVisualmenteTodo("disponibles");
    },

    moverTodasADisponibles() {
      // Mover todas las opciones seleccionadas a disponibles
      this.seleccionadas.clear();
      this.limpiarVisualmenteTodo("seleccionadas");
    },

    /**
     * @param {KeyboardEvent} e
     * @param { Contexto['cualLista'] } cualLista
     **/
    manejoTeclas(e, cualLista) {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          return this.$focus.wrap().next();

        case "ArrowUp":
          e.preventDefault();
          return this.$focus.wrap().previous();

        case "Home":
          e.preventDefault();
          return this.$focus.wrap().first();

        case "End":
          e.preventDefault();
          return this.$focus.wrap().last();

        case " ":
          e.preventDefault();
          return this.alternarSeleccionVisual(
            cualLista,
            parseInt(this.$focus.focused().getAttribute("data-id")),
          );

        case "Enter":
          e.preventDefault();
          if (cualLista === "disponibles")
            return this.moverMarcadasASeleccionadas();
          return this.moverMarcadasADisponibles();
      }
    },

    /**
     * @param { Opcion } opcion
     * @param { string } busqueda
     */
    _filtrarOpcion: (opcion, busqueda) =>
      opcion.label
        .toLowerCase()
        .normalize("NFD")
        .replace(/\p{Diacritic}/gu, "")
        .includes(busqueda),

    /**
     *  @param { CualLista } cualLista
     *  @param {string} refSinResultadosMsj
     */
    filtrarOpciones(cualLista, refSinResultadosMsj) {
      const opciones =
        cualLista === "disponibles"
          ? this.opcionesDisponibles
          : this.opcionesSeleccionadas;

      const q =
        cualLista === "disponibles"
          ? this.busquedaDisponibles
          : this.busquedaSeleccionadas;

      let busqueda = q.trim();

      if (busqueda && opciones.length) {
        busqueda = busqueda
          .toLowerCase()
          .normalize("NFD")
          .replace(/\p{Diacritic}/gu, "");

        const filtradas = this.opcionesAgrupadas
          ? opciones.map(
              /** @param { GrupoOpciones } grupo */
              (grupo) => ({
                label: grupo.label,
                opciones: grupo.opciones.filter((o) =>
                  this._filtrarOpcion(o, busqueda),
                ),
              }),
            )
          : opciones.filter((o) => this._filtrarOpcion(o, busqueda));

        const noHayResultados = this.opcionesAgrupadas
          ? !filtradas.find((g) => g.opciones.length)
          : filtradas.length === 0;

        if (noHayResultados)
          this.$refs[refSinResultadosMsj].classList.remove("hidden");
        else this.$refs[refSinResultadosMsj].classList.add("hidden");

        if (this.mostrarCantidad) this.cantidadFiltradas = filtradas.length;
        return filtradas;
      }

      this.$refs[refSinResultadosMsj].classList.add("hidden");

      if (this.mostrarCantidad) this.cantidadFiltradas = opciones.length;
      return opciones;
    },
  }));
});
