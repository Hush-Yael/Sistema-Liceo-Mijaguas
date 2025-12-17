import type { Van } from "./static/js/van-1.6.0";

declare global {
  const van: Van;
  const $: typeof document.querySelector;
  const $$: typeof document.querySelectorAll;
  const $id: typeof document.getElementById;
  interface HTMLElement {
    $: typeof document.querySelector;
    $$: typeof document.querySelectorAll;
  }
}
