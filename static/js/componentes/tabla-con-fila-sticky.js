"use strict";

// oxlint-disable-next-line no-unused-vars
const TablaConFilaSticky = class {
  /** @param {string} contenedorId */
  constructor(contenedorId) {
    this.contenedorId = contenedorId;

    /** @type {HTMLDivElement}  */
    this.contenedor = $id(contenedorId);

    /** @type {HTMLTableRowElement[]} */
    this.filas = Array.from(this.contenedor.$$("tbody tr"));

    /** @type {number} */
    this.indiceStickyActual = -1;

    /** @type {IntersectionObserver | null} */
    this.observador = null;

    this.init();
  }

  init() {
    // Configurar Intersection Observer
    this.montarObservador();

    let seRepetiraEncontrado = false,
      /** @type {number | null} */
      ultimoRepetiraIndice = null,
      hue = 0;

    for (let i = 0; i < this.filas.length; i++) {
      const fila = this.filas[i];
      const seRepetira = fila.$("[data-me-voy-a-repetir]") !== null;
      const tieneRepetidos = fila.$("[data-igual-anterior]") !== null;

      if (seRepetira) {
        seRepetiraEncontrado = true;
        hue = ultimoRepetiraIndice === null ? 0 : (hue + 20) % 360;
        ultimoRepetiraIndice = i;
        fila.setAttribute("data-empiezan-los-repetidos", "");
        fila.style.setProperty("--hue", hue);
      } else if (tieneRepetidos && seRepetiraEncontrado !== false) {
        fila.style.setProperty("--hue", hue);
        fila.setAttribute("data-contiene-repetidos", "");
      } else if (!seRepetira && !tieneRepetidos) seRepetiraEncontrado = false;
    }

    // Configurar eventos de scroll
    this.contenedor.addEventListener("scroll", this.manejarScroll.bind(this));

    // Aplicar sticky a la primera fila inicialmente
    requestAnimationFrame(() => this.establecerFilaSticky(0));

    window.addEventListener("beforeunload", () => this.destruir());
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
