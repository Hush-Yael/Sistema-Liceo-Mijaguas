$id("lista-mensajes").addEventListener("animationend", (e) => {
  /** @type {HTMLLIElement} */
  const $el = e.target;

  if ($el.classList.contains("ui-msg")) {
    switch ($el.getAttribute("data-estado")) {
      case "abriendo": {
        // no se debe iniciar la animación para cerrar si es un mensaje eterno
        if ($el.hasAttribute("data-eterno")) return;

        const retraso = parseInt($el.getAttribute("data-retraso"));

        if (Number.isInteger(retraso) && retraso > 0)
          $el.style.setProperty("--retraso", `${retraso}ms`);

        // conteo hasta cerrar (se usa el delay de la animación)
        return $el.setAttribute("data-estado", "cerrando");
      }
      case "cerrando":
        return ($el.onanimationend = () => $el.remove());
    }
  }
});
