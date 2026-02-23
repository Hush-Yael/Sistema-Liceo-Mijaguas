"use strict";

// oxlint-disable-next-line no-unused-vars
const Dropdown = class {
  constructor(config) {
    Object.assign(this, config);

    /** @type { boolean } */
    this.abierto = config.abierto || false;

    /** @type { boolean } */
    this.abiertoPorTeclado = config.abiertoPorTeclado || false;

    /** @type { string } */
    this.posPorDefecto =
      (config.pos_x || "") + (config.pos_y || "") ||
      "top: 100%; margin-top: 8px; left: 0;";

    this.menuStyle = this.posPorDefecto;

    /** @type { string | undefined } */
    this.pos_x = config.pos_x;

    /** @type { string | undefined } */
    this.pos_y = config.pos_y;

    this.trigger = {
      "x-ref": "trigger",
      type: "button",
      "aria-haspopup": config.ariaHaspopup || "true",
      ":aria-expanded": "abierto || abiertoPorTeclado",
      "@click"() {
        this.abierto = !this.abierto;
        this.$nextTick(() => this.ajustarPosicion());
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
            this.$nextTick(() => this.ajustarPosicion());
          }
        }
      },
    };

    this.menu = {
      role: config.ariaHaspopup || "menu",
      "x-trap": "abierto || abiertoPorTeclado",
      "x-ref": "menu",
      "@keydown"() {
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
      },
      ...(config.transicionPersonalizada
        ? undefined
        : { "x-transition": true }),
      "x-show"() {
        return this.abierto || this.abiertoPorTeclado;
      },
      ":style"() {
        return this.menuStyle;
      },
    };
  }

  init() {
    Alpine.bind(this.$el, {
      "@click.outside": this.cerrarMenu,
    });
  }

  cerrarMenu() {
    this.abierto = false;
    this.abiertoPorTeclado = false;
  }

  ajustarPosicion() {
    clearTimeout(this.posTimeout);

    if (this.abierto) {
      /** @type { HTMLButtonElement } */
      const button = this.$refs.trigger;
      /** @type { HTMLDivElement } */
      const dropdown = this.$refs.menu;

      if (!button || !dropdown) return;

      // Obtener dimensiones y posiciones
      const buttonRect = button.getBoundingClientRect();
      const dropdownRect = dropdown.getBoundingClientRect();

      // Determinar posición vertical
      let style = "";
      let verticalFlip = ""; // Por defecto abajo
      const spaceBelow = window.innerHeight - buttonRect.bottom - 15;
      const spaceAbove = buttonRect.top - 15;

      // Si no hay espacio abajo pero sí arriba, mostrar arriba
      if (
        spaceBelow < dropdownRect.height &&
        spaceAbove >= dropdownRect.height
      ) {
        verticalFlip = "top";
      }
      // Si no hay espacio en ninguna dirección, mostrar donde haya más espacio
      else if (
        spaceBelow < dropdownRect.height &&
        spaceAbove < dropdownRect.height
      ) {
        verticalFlip = spaceBelow >= spaceAbove ? "bottom" : "top";
      }

      // Determinar posición horizontal
      let horizontalFlip = ""; // Por defecto a la izquierda
      const spaceRight = window.innerWidth - buttonRect.left;
      const spaceLeft = buttonRect.right;

      // Si el dropdown es más ancho que el espacio a la izquierda, mostrar a la derecha
      if (dropdownRect.width > spaceLeft && spaceRight >= dropdownRect.width) {
        horizontalFlip = "right";
      }
      // Si no cabe en ninguna dirección, mostrar donde haya más espacio
      else if (
        dropdownRect.width > spaceLeft &&
        dropdownRect.width > spaceRight
      ) {
        horizontalFlip = spaceRight >= spaceLeft ? "right" : "left";
      }

      if (verticalFlip) {
        if (verticalFlip === "top")
          style += "bottom: 100%; margin-bottom: 8px;";
        else if (verticalFlip === "bottom")
          style += "top: 100%; margin-top: 8px;";
      } else if (this.pos_x) style += this.pos_x;

      if (horizontalFlip) {
        if (horizontalFlip === "left") style += "right: 0;";
        else if (horizontalFlip === "right") style += "left: 0;";
      } else if (this.pos_y) style += this.pos_y;

      if (style) log(style);

      if (style) this.menuStyle = style;
    }

    // luego de la animación
    else
      this.posTimeout = setTimeout(
        () => (this.menuStyle = "display: none; " + (this.posPorDefecto || "")),
        200,
      );
  }
};
