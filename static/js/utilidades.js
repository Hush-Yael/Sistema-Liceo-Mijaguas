Object.defineProperties(window, {
  log: { value: (...params) => console.log(...params) },
  $: { value: (query) => document.querySelector(query) },
  $$: { value: (query) => document.querySelectorAll(query) },
  $id: { value: (id) => document.getElementById(id) },
});

Object.defineProperties(HTMLElement.prototype, {
  $: {
    value: function (query) {
      return this.querySelector(query);
    },
  },
  $$: {
    value: function (query) {
      return this.querySelectorAll(query);
    },
  },
});
