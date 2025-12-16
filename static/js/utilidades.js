Object.defineProperties(window, {
  $: { value: (query) => document.querySelector(query) },
  $id: { value: (id) => document.getElementById(id) },
});

Object.defineProperty(HTMLElement.prototype, "$", {
  value: function (query) {
    return this.querySelector(query);
  },
});
