import {
  defineConfig,
  presetWind4,
  transformerVariantGroup,
  transformerDirectives,
} from "unocss";

import tema from "./tema";
import variantes from "./variantes";
import shortcuts from "./shortcuts";

export default defineConfig({
  transformers: [transformerVariantGroup(), transformerDirectives()],
  presets: [
    // @ts-expect-error: no import el tipo de los colores
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
  shortcuts,
  theme: tema,
  variants: variantes,
});
