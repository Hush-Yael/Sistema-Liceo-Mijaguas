import { Rule } from "unocss/index";

export default [
  ["aic", { "align-items": "center" }],
  ["jcc", { "justify-content": "center" }],
  ["jb", { "justify-content": "space-between" }],
  ["tac", { "text-align": "center" }],
  ["interpolate-keywords", { "interpolate-size": "allow-keywords" }],
  [
    /^h-(\d+)dvh$/,
    ([_, d]) => {
      return [
        ["height", `${d}vh`],
        ["height", `${d}dvh`],
      ];
    },
  ],
  [
    /^min-h-(\d+)dvh$/,
    ([_, d]) => {
      return [
        ["min-height", `${d}vh`],
        ["min-height", `${d}dvh`],
      ];
    },
  ],
] satisfies Rule[];
