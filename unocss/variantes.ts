import type { Variant } from "unocss";

export default [
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
] satisfies Variant[];
