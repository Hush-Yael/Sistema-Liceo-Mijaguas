// se llama directamente desde el HTML, por lo que no hay que añadirlo al botón
// oxlint-disable-next-line no-unused-vars
function mostrarModal() {
  const modal = document.getElementById("form-modal");

  if (modal) {
    // al cambiar de pestaña, se crea un nuevo modal, por lo que si habría que añadir otra vez el evento
    if (modal.onclick === null) modal.onclick = cerrarModal;

    modal.showModal();
  }
}

function cerrarModal(e) {
  if (e.target === e.currentTarget) e.currentTarget.close();
}
