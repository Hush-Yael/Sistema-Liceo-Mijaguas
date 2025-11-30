document.querySelectorAll(".lista-pestañas").forEach(function (lista_pestañas) {
  lista_pestañas.addEventListener("click", seleccionarPestaña);

  lista_pestañas.addEventListener("keydown", navegar);
});

function seleccionarPestaña(e) {
  const lista = e.currentTarget;
  const pestañaActual = e.target;

  // solo al dar click en una pestaña y no en otra parte de la lista
  if (lista !== pestañaActual) {
    // ya está seleccionada, no hacer nada
    if (pestañaActual.getAttribute("aria-selected") === "true")
      return e.preventDefault();

    const url = new URL(window.location.href);
    const busqueda = location.search;
    const parametros = new URLSearchParams(busqueda);
    const pestañas = Array.from(lista.children);

    // Deseleccionar las otras pestañas y establecer esta pestaña como seleccionada
    pestañas.forEach(function (pestaña) {
      if (pestaña === pestañaActual) return;

      pestaña.setAttribute("aria-selected", false);
      pestaña.tabIndex = -1;
    });

    pestañaActual.setAttribute("aria-selected", true);
    pestañaActual.tabIndex = 0;

    parametros.set(
      lista.getAttribute("data-nombre_parametro") || "pestaña",
      pestañaActual.getAttribute("data-pestaña-nombre"),
    );
    url.search = parametros.toString();
    window.history.replaceState({}, "", url);
  }
}

function navegar(e) {
  const lista = e.currentTarget;
  const pestañaActual = e.target;

  if (pestañaActual !== lista) {
    const pestañas = Array.from(lista.children);
    const indiceActual = pestañas.indexOf(pestañaActual);

    if (indiceActual === -1) return; // El elemento enfocado no es una pestaña

    let nuevoIndice = 0;

    switch (e.key) {
      case "ArrowRight":
        nuevoIndice = (indiceActual + 1) % pestañas.length;
        break;
      case "ArrowLeft":
        nuevoIndice = (indiceActual - 1 + pestañas.length) % pestañas.length;
        break;
      case "Home":
        nuevoIndice = 0;
        break;
      case "End":
        nuevoIndice = pestañas.length - 1;
        break;
      default:
        return; // Salir si no se reconoce la tecla
    }

    e.preventDefault();
    e.stopPropagation();

    pestañas[nuevoIndice].focus();
  }
}
