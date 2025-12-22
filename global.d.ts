import type { Alpine } from "alpinejs";
declare global {
  const Alpine: Alpine;
  const log: typeof console.log;
  const $: typeof document.querySelector;
  const $$: typeof document.querySelectorAll;
  const $id: typeof document.getElementById;
  interface HTMLElement {
    $: typeof document.querySelector;
    $$: typeof document.querySelectorAll;
  }
}
