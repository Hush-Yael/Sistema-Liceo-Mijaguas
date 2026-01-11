"use strict";

// oxlint-disable-next-line no-unused-vars
const TablaConFilaSticky = class {
  /** @param {string} contenedorId */
  constructor(contenedorId) {
    this.contenedorId = contenedorId;

    /** @type {IntersectionObserver | null} */
    this.observador = null;

    window.addEventListener("beforeunload", () => this.destruir());

    window.addEventListener("htmx:afterRequest", (e) => {
      // Si se reemplazó el contenedor
      if (e.detail.successful && e.detail.target.id === this.contenedorId) {
        // ya no hay que observar sus filas
        this.destruir();

        const contenedorNuevo = $id(this.contenedorId);
        // Se cambió por la misma tabla, hay que volver a inicializar
        if (contenedorNuevo) {
          // a veces se reemplaza la tabla por otro elemento, como un mensaje de vacío, por lo que se asegura que haya una tabla para ini
          if (contenedorNuevo.$("table")) this.init();
        }
      }
    });

    // Configurar Intersection Observer
    this.montarObservador();

    this.init();
  }

  init() {
    /** @type {HTMLDivElement}  */
    this.contenedor = $id(this.contenedorId);

    /** @type {HTMLTableRowElement[]} */
    this.filas = Array.from(this.contenedor.$$("tbody tr"));

    this.establecerFilasObservadas();

    /** @type {number} */
    this.indiceStickyActual = -1;

    this.montarRangosYColores();

    // Configurar eventos de scroll
    this.contenedor.addEventListener("scroll", this.manejarScroll.bind(this));

    // Aplicar sticky a la primera fila inicialmente
    requestAnimationFrame(() => this.establecerFilaSticky(0));
  }

  // Asignar colores a los datos de has filas de acuerdo a donde empiezan y terminan los repetidos
  montarRangosYColores() {
    const cantidadColumnas = this.filas[0].children.length;
    const coloresColumnas = Array.from({ length: cantidadColumnas }, () => 0);

    /** @type { number | null } */
    let ultimaFilaRepetidos = null;

    for (let i = 0; i < this.filas.length; i++) {
      const fila = this.filas[i];
      let repetidos = 0;

      for (let j = 0; j < fila.children.length; j++) {
        const td = fila.children[j];
        const seRepite = td.hasAttribute("data-se-repite");
        const datoRepetido = td.hasAttribute("data-repetido");

        if (seRepite) {
          if (ultimaFilaRepetidos !== null)
            coloresColumnas[j] = (coloresColumnas[j] + 15) % 360;

          repetidos++;
        }

        if (seRepite || datoRepetido)
          td.style.setProperty("--hue", coloresColumnas[j]);
      }

      if (repetidos > 0) ultimaFilaRepetidos = i;
    }
  }

  montarObservador() {
    const options = {
      root: this.contenedor,
      rootMargin: "-1px 0px 0px 0px",
      threshold: [0, 1],
    };

    this.observador = new IntersectionObserver((entradas) => {
      // Usar requestAnimationFrame para agrupar actualizaciones
      requestAnimationFrame(() => {
        let nuevoIndiceSticky = this.indiceStickyActual;

        entradas.forEach((entrada) => {
          const indice = parseInt(entrada.target.dataset.indice);

          if (!entrada.isIntersecting && entrada.boundingClientRect.top < 0)
            nuevoIndiceSticky = Math.max(nuevoIndiceSticky, indice + 1);
          else if (
            entrada.isIntersecting &&
            entrada.boundingClientRect.top <= 0
          )
            nuevoIndiceSticky = Math.max(nuevoIndiceSticky, indice);
        });

        // Actualizar solo si cambió
        if (nuevoIndiceSticky !== this.indiceStickyActual)
          this.establecerFilaSticky(nuevoIndiceSticky);
      });
    }, options);
  }

  establecerFilasObservadas() {
    // Observar todas las filas
    this.filas.forEach((fila) => this.observador.observe(fila));
  }

  /** @param {number} indice */
  establecerFilaSticky(indice) {
    if (
      indice < 0 ||
      indice >= this.filas.length ||
      indice === this.indiceStickyActual
    )
      return;

    // Remover clase sticky de todas las filas
    const sticky = this.contenedor.$(".fila-sticky");
    if (sticky) sticky.classList.remove("fila-sticky");

    // Añadir clase sticky a la fila actual
    this.filas[indice].classList.add("fila-sticky");

    this.indiceStickyActual = indice;
  }

  manejarScroll() {
    // Backup: Si Intersection Observer falla, usar cálculo manual
    const scrollTop = this.contenedor.scrollTop;
    const filaAltura = this.filas[0]?.offsetHeight || 50;
    const indiceCalculado = Math.floor(scrollTop / filaAltura);

    if (indiceCalculado >= 0 && indiceCalculado < this.filas.length) {
      this.establecerFilaSticky(indiceCalculado);
    }
  }

  destruir() {
    if (this.observador) this.observador.disconnect();

    this.contenedor.removeEventListener("scroll", this.manejarScroll);
  }
};
