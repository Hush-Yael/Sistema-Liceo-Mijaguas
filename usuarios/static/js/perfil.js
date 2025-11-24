"use strict";

const modal = document.getElementById("img-dialog");
const verFotoPerfil = document.getElementById("ver-foto");

modal.addEventListener("click", function (e) {
  if (e.target === modal) modal.close();
});

verFotoPerfil.addEventListener("click", function () {
  const foto = document.getElementById("foto");

  if (foto.tagName !== "svg") modal.showModal();
});

const form = document.querySelector("form");

// al cambiar la foto, se actualiza la vista previa
form.addEventListener("change", function (e) {
  if (e.target.id === "id_foto_perfil") {
    const archivo = e.target.files[0];

    if (archivo) {
      if (archivo.size > 5242880) {
        alert("El archivo no puede superar los 5MB.");
        return (e.target.value = "");
      }

      const foto = document.getElementById("foto");
      const url = URL.createObjectURL(e.target.files[0]);

      if (foto.tagName === "svg") {
        const nuevaFoto = document.createElement("IMG");

        nuevaFoto.classList.add("foto");
        nuevaFoto.setAttribute("src", url);
        nuevaFoto.setAttribute("id", "foto");
        nuevaFoto.setAttribute("alt", "foto");

        foto.parentElement.replaceChild(nuevaFoto, foto);
      } else foto.setAttribute("src", url);

      modal.querySelector("img").src = url;
    }
  }
});
