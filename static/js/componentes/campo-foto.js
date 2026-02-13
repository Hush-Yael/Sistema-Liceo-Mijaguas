// oxlint-disable-next-line no-unused-vars
function campoFoto(config) {
  return {
    /** @type { string } */
    urlFotoPerfil: config.urlFotoPerfil || "",
    /** @type { string } */
    url: config.url || "",
    /** @type { boolean } */
    modalFotoAbierto: config.modalFotoAbierto || false,
    actualizarFoto() {
      /** @type { HTMLInputElement } */
      const input = this.$el;
      const archivo = input.files[0];

      if (archivo) {
        inputLimpiar = this.$refs.limpiar;
        if (inputLimpiar) inputLimpiar.checked = false;

        const tamañoMaximo = config.tamañoMaximo || 5242880;
        if (archivo.size > tamañoMaximo) {
          alert(
            `El archivo no puede superar los ${(tamañoMaximo / (1024 * 1024)).toFixed(2)} MB.`,
          );
          return (input.value = "");
        }

        this.url = URL.createObjectURL(archivo);

        if (input.getAttribute("aria-invalid")) {
          input.removeAttribute("aria-invalid");
          input.removeAttribute("aria-errormessage");
        }
      }
    },
    borrarFoto() {
      this.url = "";
      /** @type { HTMLInputElement } */
      const input = this.$refs.input;

      input.value = "";
      input.removeAttribute("aria-invalid");
      input.removeAttribute("aria-errormessage");

      inputLimpiar = this.$refs.limpiar;
      if (inputLimpiar) inputLimpiar.checked = true;

      this.modalFotoAbierto = false;

      this.$el.dispatchEvent(new Event("change", { bubbles: true }));
    },
  };
}
