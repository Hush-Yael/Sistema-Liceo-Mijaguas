import {
  defineConfig,
  presetWind4,
  transformerVariantGroup,
  transformerDirectives,
} from "unocss";

class ColorDeTema {
  [n: number]: string;
  DEFAULT: string;
  texto: string;

  constructor(nombreColor: string) {
    Array.from({ length: 11 }).forEach((_, i) => {
      const numero = i === 0 ? 50 : i === 10 ? 950 : i * 100;
      this[numero] = `var(--color-${nombreColor}-${numero})`;
    });

    this.DEFAULT = this[500];
    this.texto = `var(--color-texto-${nombreColor})`;
  }
}

export default defineConfig({
  transformers: [transformerVariantGroup(), transformerDirectives()],
  presets: [
    presetWind4({
      preflights: {
        reset: false,
      },
      dark: {
        light: ".claro",
        dark: ".oscuro",
      },
    }),
  ],
  shortcuts: {
    col: "flex flex-col",
    fc: "flex items-center justify-center",
    aic: "items-center",
    jcc: "justify-center",
    tac: "text-center",
  },
  theme: {
    colors: {
      // @ts-expect-error
      primario: new ColorDeTema("primario"),
      // @ts-expect-error
      secundario: new ColorDeTema("secundario"),
      // @ts-expect-error
      acento: new ColorDeTema("acento"),
      // @ts-expect-error
      info: new ColorDeTema("info"),
      // @ts-expect-error
      exito: new ColorDeTema("exito"),
      // @ts-expect-error
      peligro: new ColorDeTema("peligro"),
      "texto-sutil": "var(--texto-sutil)",
    },
    radius: {
      campo: "4px",
      caja: "1rem",
    },
  },
  variants: [
    (matcher) => {
      if (!matcher.startsWith("pover:")) return matcher;

      return [
        {
          matcher: matcher.slice(6),
          handle: (input, next) => {
            const p = "@media (hover: hover) and (pointer: fine)";
            return next({
              ...input,
              parent: `${input.parent ? `${input.parent} $$ ` : ""}${p}`,
            });
          },
          selector: (s) => `${s}:hover`,
        },
        {
          matcher: matcher.slice(6),
          handle: (input, next) => {
            const p = "@media (hover: none) and (pointer: coarse)";
            return next({
              ...input,
              parent: `${input.parent ? `${input.parent} $$ ` : ""}${p}`,
            });
          },
          selector: (s) => `${s}:active`,
        },
      ];
    },
  ],
});
