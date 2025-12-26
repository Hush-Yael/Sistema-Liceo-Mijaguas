import {
  defineConfig,
  presetWind4,
  transformerVariantGroup,
  transformerDirectives,
  ConfigBase,
  PresetWind4Theme,
} from "unocss";
import tema from "./unocss/tema";
import variantes from "./unocss/variantes";
import shortcuts from "./unocss/shortcuts";
import rules from "./unocss/rules";

const config = defineConfig({
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
  extendTheme: tema,
  rules,
  variants: variantes,
  shortcuts,
});

export default config;

export type ConfigThemePreset = PresetWind4Theme;
export type Config = ConfigBase<ConfigThemePreset>;
