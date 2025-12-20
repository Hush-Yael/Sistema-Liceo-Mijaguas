"use strict";

// oxlint-disable-next-line no-unused-vars
const TablaConFilaSticky = class {
  constructor(contenedorId) {
    this.contenedor = $id(contenedorId);
    this.filas = Array.from(this.contenedor.$$("tbody tr"));
    this.stickyActual = null;
    this.scrollTimeout = null;
    this.tiempoScrollAnterior = 0;
    this.retraso = 16; // ~60fps

    this.init();
  }

  init() {
    // Escuchar scroll con throttle
    this.contenedor.onscroll = this.handleScroll.bind(this);

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
