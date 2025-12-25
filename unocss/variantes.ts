import { type Variant } from "unocss";

export default [
  (matcher) => {
    if (!matcher.startsWith("pover:")) return matcher;

    return [
      {
        matcher: matcher.slice(6),
        order: 999,
        handle: (input, next) => {
          const p = "@media (hover: hover) and (pointer: fine)";
          return next({
            ...input,
            parent: `${input.parent ? `${input.parent} $$ ` : ""}${p}`,
          });
        },
        selector: (s) => `${s}:not(:disabled):hover`,
      },
      {
        matcher: matcher.slice(6),
        order: 999,
        handle: (input, next) => {
          const p = "@media (hover: none) and (pointer: coarse)";
          return next({
            ...input,
            parent: `${input.parent ? `${input.parent} $$ ` : ""}${p}`,
          });
        },
        selector: (s) => `${s}:not(:disabled):active`,
      },
    ];
  },
] satisfies Variant[];
