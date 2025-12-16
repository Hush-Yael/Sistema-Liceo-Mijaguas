import type { ConfigBase, PresetWind4Theme } from "unocss/index";

type ThemePreset = PresetWind4Theme;
type Color = ConfigBase<ThemePreset>["theme"]["colors"];

class ColorDeTema implements Color {
  [n: string]: string;
  DEFAULT: string;
  texto: string;

  constructor(nombreColor: string) {
    Array.from({ length: 11 }).forEach((_, i) => {
      const numero = i === 0 ? 50 : i === 10 ? 950 : i * 100;
      this[numero.toString()] = `var(--color-${nombreColor}-${numero})`;
    });

    this.DEFAULT = this[500];
    this.texto = `var(--color-texto-${nombreColor})`;
  }
}

export default {
  colors: {
    primario: new ColorDeTema("primario"),
    secundario: new ColorDeTema("secundario"),
    acento: new ColorDeTema("acento"),
    info: new ColorDeTema("info"),
    exito: new ColorDeTema("exito"),
    peligro: new ColorDeTema("peligro"),
    "texto-sutil": "var(--texto-sutil)",
  },
  radius: {
    campo: "4px",
    caja: "1rem",
  },
} satisfies ConfigBase<ThemePreset>["theme"];
