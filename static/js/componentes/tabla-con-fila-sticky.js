"use strict";

// oxlint-disable-next-line no-unused-vars
const TablaConFilaSticky = class {
  constructor(contenedorId) {
    /** @type {HTMLDivElement} */
    this.contenedor = $id(contenedorId);

    /** @type {HTMLTableRowElement[]} */
    this.filas = Array.from(this.contenedor.$$("tbody tr"));

    /** @type {HTMLTableRowElement | null} */
    this.stickyActual = null;

    /** @type {number | null} */
    this.scrollTimeout = null;

    /** @type {number} */
    this.tiempoScrollAnterior = 0;

    /** @type {number} */
    this.retraso = 16; // ~60fps

    this.init();
  }

  init() {
    // Escuchar scroll con throttle
    this.contenedor.onscroll = this.handleScroll.bind(this);

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

    // Inicializar
    this.actualizarFilas();
  }

  handleScroll() {
    const now = Date.now();
    const timeSinceLastScroll = now - this.tiempoScrollAnterior;

    // Si ya pasó el tiempo del throttle, ejecutar inmediatamente
    if (timeSinceLastScroll >= this.retraso) {
      this.tiempoScrollAnterior = now;
      this.actualizarFilas();
    } else {
      // Programar para ejecutar después del tiempo restante
      clearTimeout(this.scrollTimeout);
      this.scrollTimeout = setTimeout(() => {
        this.tiempoScrollAnterior = Date.now();
        this.actualizarFilas();
      }, this.retraso - timeSinceLastScroll);
    }
  }

  actualizarFilas() {
    const scrollTop = this.contenedor.scrollTop;

    // Encontrar la fila que debería ser sticky
    let indiceFilaObjetivo = 0;
    let alturaAcumulada = 0;

    for (let i = 0; i < this.filas.length; i++) {
      const alturaFila = this.filas[i].offsetHeight;
      alturaAcumulada += alturaFila;

      if (alturaAcumulada > scrollTop) {
        indiceFilaObjetivo = i;
        break;
      }
    }

    this.aplicarSticky(indiceFilaObjetivo);
  }

  /** @param {number} indice */
  aplicarSticky(indice) {
    // Remover sticky anterior
    if (this.stickyActual) this.stickyActual.classList.remove("sticky-row");

    // Aplicar nuevo sticky
    const filaObjetivo = this.filas[indice];
    filaObjetivo.classList.add("sticky-row");

    this.stickyActual = filaObjetivo;
  }

  // Limpiar timeout al destruir
  destruir() {
    clearTimeout(this.scrollTimeout);
    this.contenedor.onscroll = null;
  }
};
