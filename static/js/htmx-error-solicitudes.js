const $listaMensajes = $id("lista-mensajes");

/** @param {string} mensaje **/
function notificarError(texto) {
  /** @type {HTMLTemplateElement} */
  const msgTemplate = $id("msg-template");
  const nuevoMensaje = document.importNode(msgTemplate.content, true);

  /** @type {HTMLLIElement} */
  const $mensaje = nuevoMensaje.firstElementChild;

  $mensaje.id = "htmx-error";
  $mensaje.prepend(document.createTextNode(texto));

  $mensaje.setAttribute("data-eterno", "");
  $mensaje.classList.add("ui-msg/peligro");

  /** @type {HTMLLIElement} */
  const $errorExistente = $listaMensajes.$("#htmx-error");

  if ($errorExistente) $listaMensajes.replaceChild($mensaje, $errorExistente);
  else $listaMensajes.appendChild($mensaje);
}

htmx.on("htmx:responseError", function (evt) {
  /** @type {XMLHttpRequest} xhr */
  const xhr = evt.detail.xhr;

  notificarError(
    xhr.status < 500
      ? `Error en la solicitud: [${xhr.status}: ${xhr.statusText}] ${xhr.responseText.slice(
          0,
          256,
        )}`
      : `Error interno del servidor al procesar la solicitud: [${xhr.status}: ${xhr.statusText}]`,
  );
});

htmx.on("htmx:sendError", function (evt) {
  const requestConfig = evt.detail.requestConfig;
  notificarError(
    `Error de conexión: ${requestConfig.verb} ${requestConfig.path}`,
  );
});

htmx.on("htmx:beforeSend", function () {
  const $errorExistente = $listaMensajes.$("#htmx-error");
  if ($errorExistente) $errorExistente.remove();
});
