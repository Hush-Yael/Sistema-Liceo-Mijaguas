import type { ThemeExtender } from "unocss/index";
import type { Config, ConfigThemePreset } from "../uno.config";

type Color = Config["theme"]["colors"];

class ColorDeTema implements Color {
  [n: string]: string;
  DEFAULT: string;
  texto: string;

  constructor(nombreColor: string) {
    Array.from({ length: 11 }).forEach((_, i) => {
      const numero = i === 0 ? 50 : i === 10 ? 950 : i * 100;
      this[numero.toString()] = `var(--color-${nombreColor}-${numero})`;
    });

    this.DEFAULT = this["500"];
    this.texto = `var(--color-texto-${nombreColor})`;
  }
}

const tema: ThemeExtender<ConfigThemePreset> = (theme) => ({
  ...theme,
  colors: {
    ...theme.colors,
    fondo: new ColorDeTema("fondo"),
    primario: new ColorDeTema("primario"),
    secundario: new ColorDeTema("secundario"),
    acento: new ColorDeTema("acento"),
    info: new ColorDeTema("info"),
    exito: new ColorDeTema("exito"),
    advertencia: new ColorDeTema("advertencia"),
    peligro: new ColorDeTema("peligro"),
    "texto-sutil": "var(--texto-sutil)",
  },
  radius: {
    ...theme.radius,
    campo: "4px",
    caja: "1rem",
  },
  breakpoint: {
    ...theme.breakpoint,
    sidebar: "800px",
    sidebar_full: "1000px",
  },
});

export default tema;
