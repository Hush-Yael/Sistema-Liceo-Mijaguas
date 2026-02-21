"use strict";

// oxlint-disable-next-line no-unused-vars
function notasApp() {
  return {
    marcarCambio() {
      /** @type { HTMLInputElement } */
      const input = this.$event.target;

      input.setAttribute("data-estado", "C");
    },

    $listaMensajes: $id("lista-mensajes"),

    /**
     *  @param {string} texto
     *  @param {boolean} exito
     **/
    notificar(texto, exito) {
      /** @type {HTMLTemplateElement} */
      const msgTemplate = $id("msg-template");
      const nuevoMensaje = document.importNode(msgTemplate.content, true);

      /** @type {HTMLLIElement} */
      const $mensaje = nuevoMensaje.firstElementChild;

      const id = `htmx-error-${exito ? "exito" : "error"}`;
      $mensaje.id = id;

      $mensaje.prepend(document.createTextNode(texto));

      $mensaje.classList.add(exito ? "ui-msg/exito" : "ui-msg/peligro");

      /** @type {HTMLLIElement} */
      const $errorExistente = this.$listaMensajes.$(`#${id}`);

      if ($errorExistente)
        this.$listaMensajes.replaceChild($mensaje, $errorExistente);
      else this.$listaMensajes.appendChild($mensaje);
    },
  };
}
