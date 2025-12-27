import type { UserShortcuts } from "unocss/index";
import type { Config, ConfigThemePreset } from "../uno.config";

const util = {
  col: "flex flex-col",
  fc: "flex items-center justify-center",
};

const elems = {
  ["ui-elevado"]:
    "border-1 border-[--borde-caja] shadow-[--sombra-caja] bg-fondo-500",

  ["ui-elevado-2"]:
    "border-1 border-[--transparente-1] shadow-[--sombra-caja] bg-fondo-700",

  ["ui-caja"]:
    "border-1 border-[--borde-caja] rounded-caja shadow-[--sombra-caja] bg-fondo-500",
} satisfies Config["shortcuts"];

const btn = {
  ["ui-btn"]:
    "fc gap-x-2 rounded-campo cursor-pointer active:scale-99 transition-[background-color,color,transform,border-color,outline-color] duration-200 ease-in-out select-none",

  ["ui-btn/primario"]: "bg-primario text-primario-texto pover:bg-primario-600",

  ["ui-btn/secundario"]: "bg-secundario text-secundario-texto",

  ["ui-btn/borde"]:
    "outline-2 outline-[hsl(0,0%,60%)] -outline-offset-2 focus-visible:(ring-2 ring-primario) text-[hsl(0,0%,30%)] dark:(text-[hsl(0,0%,90%)] outline-[hsl(0,0%,80%)]) pover:outline-[hsl(0,0%,35%)] pover:text-[hsl(0,0%,25%)] dark:pover:text-[hsl(0,0%,75%)] dark:pover:outline-[hsl(0,0%,50%)]",

  ["ui-btn/peligro"]:
    "bg-peligro text-peligro-texto border-peligro-400 dark:border-peligro-600 pover:bg-peligro-600 dark:pover:bg-peligro-400",

  ["ui-btn/exito"]:
    "bg-exito text-exito-texto border-exito-400 dark:border-exito-600 pover:bg-exito-600 dark:pover:bg-exito-400",

  ["ui-btn/redondeado"]: "rounded-full",

  ["ui-btn/sm"]: "px-4 py-1 text-sm [&>svg]:size-4",

  ["ui-btn/md"]: "px-6 py-1.5 [&>svg]:size-4.5",
} satisfies Config["shortcuts"];

const input = {
  ["ui-input-error"]:
    "text-[.9rem] text-peligro-500 dark:text-peligro-300 starting:(block opacity-100) peer-not-[[aria-invalid=true]]:(hidden opacity-0)",
  ["ui-opcion"]: `
    relative size-full appearance-none border border-[--transparente-2] bg-fondo-700 transition-[background-color,border-color]
    
    [&:checked,.peer:checked~&,.group[aria-selected=true]_&]:(bg-primario dark:bg-primario-700 border-primario dark:border-primario-700)
    

    before:(
      content-['']
      absolute -z-1 top-2/4 left-2/4 block size-180% -translate-y-2/4 -translate-x-2/4 rounded-full bg-[--transparente-1] opacity-0 transition-opacity focus-visible:opacity-50 pover:opacity-50
    )
  `,
  ["ui-opcion/checkbox"]: "rounded",
  ["ui-opcion/radio"]:
    "rounded-full after:(content-[''] absolute top-0 left-0 right-0 bottom-0 size-50% ma block rounded-full bg-primario-texto opacity-0) checked:after:(opacity-100)",
} satisfies Config["shortcuts"];

export default {
  ...util,
  ...elems,
  ...btn,
  ...input,
} satisfies UserShortcuts<ConfigThemePreset>;
