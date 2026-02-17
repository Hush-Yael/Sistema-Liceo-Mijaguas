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

  ["ui-loader"]:
    "inline-block aspect-square rounded-full size-4 border-3 animate-spin",

  ["ui-loader/primario"]:
    "border-[--transparente-3] border-r-[--color-primario-200] dark:border-r-[--color-primario-700]",

  ["ui-loader/blanco"]: "border-#fff3 border-r-#fff",

  ["ui-contenedor-icono"]: "inline-flex aic jcc rounded-full aspect-square",
} satisfies Config["shortcuts"];

const btn = {
  ["ui-btn"]:
    "fc gap-x-2 rounded-campo cursor-pointer active:scale-99 transition-[background-color,color,transform,border-color,outline-color] duration-200 ease-in-out select-none",

  ["ui-btn/primario"]:
    "bg-primario dark:bg-primario-600 text-primario-texto font-bold pover:bg-primario-400 dark:pover:bg-primario-700",

  ["ui-btn/secundario"]:
    "bg-secundario text-secundario-texto font-bold pover:bg-secundario-400 dark:pover:bg-secundario-600",

  ["ui-btn/borde"]:
    "outline-2 outline-[hsl(0,0%,60%)] -outline-offset-2 focus-visible:(ring-2 ring-primario) font-bold text-[hsl(0,0%,30%)] dark:(text-[hsl(0,0%,90%)] outline-[hsl(0,0%,80%)]) pover:outline-[hsl(0,0%,35%)] pover:text-[hsl(0,0%,25%)] dark:pover:text-[hsl(0,0%,75%)] dark:pover:outline-[hsl(0,0%,50%)]",

  ["ui-btn/peligro"]:
    "bg-peligro text-peligro-texto font-bold border-peligro-400 dark:border-peligro-600 pover:bg-peligro-600 dark:pover:bg-peligro-400",

  ["ui-btn/exito"]:
    "bg-exito text-exito-texto font-bold border-exito-400 dark:border-exito-600 pover:bg-exito-600 dark:pover:bg-exito-400",

  ["ui-btn/sm"]: "px-4 py-1 text-sm [&>svg]:size-4",

  ["ui-btn/md"]: "px-6 py-1.5 [&>svg]:size-4.5",
} satisfies Config["shortcuts"];

const input = {
  ["ui-input-error"]:
    "text-[.9rem] text-peligro-500 dark:text-peligro-300 hidden opacity-0 [.peer[aria-invalid=true]~&,.peer[data-invalido=true]~&]:(block! opacity-100!)",

  ["ui-opcion"]: `
    relative size-full appearance-none border border-[--transparente-2] bg-fondo-700 transition-[background-color,border-color]
    
    [&:checked,.peer:checked~&,.peer:checked~.group_&,.group[aria-selected=true]_&]:(bg-primario dark:bg-primario-700 border-primario dark:border-primario-700 dark:bg-primario-700! dark:border-primario-700!)

    before:(
      content-['']
      absolute top-2/4 left-2/4 block size-180% -translate-y-2/4 -translate-x-2/4 rounded-full bg-[--transparente-1] opacity-0 transition-opacity pointer-events-none focus-visible:opacity-50 pover:opacity-50
    )

    group-hover/label:before:opacity-50
  `,

  ["ui-opcion/checkbox"]: "rounded",

  ["ui-opcion/radio"]:
    "rounded-full after:(content-[''] absolute top-0 left-0 right-0 bottom-0 size-50% ma block rounded-full bg-primario-texto opacity-0) checked:after:(opacity-100)",
} satisfies Config["shortcuts"];

const msg = {
  ["ui-msg"]: `
      flex jb aic gap-3 p-3 px-4 rounded-t not-last:rounded-b animate-forwards! animate-ease-out
      bg-exito text-exito-texto [&>button]:bg-#0002

      before:(content-[''] absolute top-0 left-0 size-full bg-#0002 pointer-events-none)

      data-[estado=abriendo]:(animate-slide-in-up animate-duration-400)

      data-[estado=cerrando]:(animate-fade-out-down animate-duration-500 animate-delay-[var(--retraso,5000ms)] hover:(animate-paused before:animate-paused))

      data-[estado=cerrando]:before:animate-[encoger_var(--retraso,5000ms)_linear_forwards]
    `,

  ["ui-msg/exito"]: "bg-exito text-exito-texto [&>button]:bg-#0002",

  ["ui-msg/peligro"]: "bg-peligro text-peligro-texto [&>button]:bg-#0004",

  ["ui-msg/advertencia"]:
    "bg-advertencia text-advertencia-texto [&>button]:bg-#0002",

  ["ui-msg/info"]: "bg-info text-info-texto [&>button]:bg-#0002",
} satisfies Config["shortcuts"];

const pestañas = {
  ["ui-lista-pestañas"]: "flex flex-wrap text-sm -mb-px font-500 text-center",

  ["ui-pestaña"]:
    "inline-flex items-center justify-center p-2 px-4 border-b border-#0000 text-texto-semi-sutil transition-colors cursor-pointer select-none",
};

export default {
  ...util,
  ...elems,
  ...btn,
  ...input,
  ...msg,
  ...pestañas,
} satisfies UserShortcuts<ConfigThemePreset>;
