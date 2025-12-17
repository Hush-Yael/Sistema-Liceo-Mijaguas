"use strict";

/** @type {HTMLElement} */
const fotoInput = $id("id_foto_perfil");

// al cambiar la foto, se actualiza la vista previa
fotoInput.addEventListener(
  "change",
  /** @param {Event} e */
  function (e) {
    const archivo = e.target.files[0];

    if (archivo) {
      if (archivo.size > 5242880) {
        alert("El archivo no puede superar los 5MB.");
        return (e.target.value = "");
      }

      const fotoActual = $id("foto-actual");

      if (!fotoActual)
        console.error("No se encontró el elemento con la foto actual");

      const url = URL.createObjectURL(e.target.files[0]);

      if (fotoActual.tagName === "svg") {
        /** @type {HTMLElement} */
        const nuevaFotoActual = Object.assign(document.createElement("IMG"), {
          src: url,
          alt: "foto",
          id: "foto-actual",
        });

        fotoActual.replaceWith(nuevaFotoActual);
      } else fotoActual.setAttribute("src", url);

      $id("modal-img").$("img").src = url;
    }
  },
);
