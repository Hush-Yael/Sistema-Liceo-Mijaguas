"use strict";
{
  document.addEventListener("alpine:init", () => {
    Alpine.data("dropdown", (config) => ({
      /** @type { boolean } */
      abierto: config.abierto || false,
      /** @type { boolean } */
      abiertoPorTeclado: config.abiertoPorTeclado || false,
      /** @type { string } */
      menuStyle: config.menuStyle || "",

      init() {
        Alpine.bind(this.$el, {
          "@click.outside": this.cerrarMenu,
        });
      },

      cerrarMenu() {
        this.abierto = false;
        this.abiertoPorTeclado = false;
        this.menuStyle = "";
      },

      trigger: {
        "x-ref": "trigger",
        type: "button",
        "aria-haspopup": config.ariaHaspopup || "true",
        ":aria-expanded": "abierto || abiertoPorTeclado",
        "@click"() {
          this.abierto = !this.abierto;

          if (config.noAjustable) return;

          if (this.abierto) this.$nextTick(() => this.ajustarPosicion());
          else this.menuStyle = "";
        },
        "@keydown"() {
          /** @type { KeyboardEvent } */
          const e = this.$event;

          switch (e.key) {
            case " ":
            case "Enter":
            case "ArrowDown": {
              e.preventDefault();
              this.abiertoPorTeclado = true;

              if (config.noAjustable) return;
              this.$nextTick(() => this.ajustarPosicion());
            }
          }
        },
      },

      menu: {
        role: config.ariaHaspopup || "menu",
        "x-trap": "abierto || abiertoPorTeclado",
        "x-ref": "menu",
        "@keydown": manejarTeclas,
        "x-transition": true,
        "x-show"() {
          return this.abierto || this.abiertoPorTeclado;
        },
        ":style"() {
          return this.menuStyle;
        },
      },

      ajustarPosicion: config.noAjustable ? null : ajustarPosicion,

      ...config,
    }));
  });

  function ajustarPosicion() {
    const recta = this.$refs.menu.getBoundingClientRect();

    // si sobresale de la ventana, ajustarlo
    if (
      recta.top < 0 ||
      recta.bottom + 40 >
        (window.innerHeight || document.documentElement.clientHeight) ||
      recta.left < 0 ||
      recta.right + 40 >
        (window.innerWidth || document.documentElement.clientWidth)
    ) {
      /** @type { HTMLButtonElement } */
      const btn = this.$refs.trigger;
      const rectaBtn = btn.getBoundingClientRect();

      const menu = this.$refs.menu;
      const ventanaAncho = window.innerWidth;
      const ventanaAlto = window.innerHeight;

      let top = rectaBtn.bottom + window.scrollY;
      let left = rectaBtn.left + window.scrollX;

      // Ajustar verticalmente
      const espacioAbajo = ventanaAlto - rectaBtn.bottom;
      const alturaMenu = menu.offsetHeight || 300; // altura estimada

      // Mostrar arriba si hay más espacio
      if (espacioAbajo < alturaMenu && rectaBtn.top > alturaMenu)
        top = rectaBtn.top + window.scrollY - alturaMenu;

      // Ajustar horizontalmente
      const espacioRight = ventanaAncho - rectaBtn.left;
      const anchoMenu = menu.offsetWidth || 200; // ancho estimado

      // Alinear al lado derecho del botón
      if (espacioRight < anchoMenu && rectaBtn.left > anchoMenu)
        left = rectaBtn.right + window.scrollX - anchoMenu;

      // Asegurar que no se salga de la ventana
      top = Math.max(
        10,
        Math.min(top, window.scrollY + ventanaAlto - alturaMenu - 10),
      );
      left = Math.max(
        10,
        Math.min(left, window.scrollX + ventanaAncho - anchoMenu - 10),
      );

      this.menuStyle = `position: fixed; top: ${top}px; left: ${left}px;`;
    }
  }

  function manejarTeclas() {
    /** @type { KeyboardEvent } e */
    const e = this.$event;
    const $focus = this.$focus;

    switch (e.key) {
      case "Escape": {
        e.stopPropagation();
        this.abierto = false;
        this.abiertoPorTeclado = false;
        return this.$nextTick(() => this.$refs.trigger.focus());
      }
      case "ArrowDown": {
        e.preventDefault();
        return $focus.wrap().next();
      }
      case "ArrowUp": {
        e.preventDefault();
        return $focus.wrap().previous();
      }
      case "Home": {
        if (e.target.type !== "text") {
          e.preventDefault();
          return $focus.wrap().first();
        }
      }
      case "End": {
        if (e.target.type !== "text") {
          e.preventDefault();
          return $focus.wrap().last();
        }
      }
    }

    this.shiftPresionado = e.shiftKey;
  }
}
