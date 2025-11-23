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

// al cambiar algo, se habilita el botón
form.addEventListener(
  "change",
  function () {
    document.getElementById("submit").removeAttribute("disabled");
  },
  { once: true },
);

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
        const nuevoFotor = document.createElement("IMG");

        nuevoFotor.classList.add("foto");
        nuevoFotor.setAttribute("src", url);
        nuevoFotor.setAttribute("id", "foto");
        nuevoFotor.setAttribute("alt", "foto");

        foto.parentElement.replaceChild(nuevoFotor, foto);
      } else foto.setAttribute("src", url);

      modal.querySelector("img").src = url;
    }
  }
});

// ícono cuando no hay foto
const icono = `
  <svg
    id="foto"
    viewBox="0 0 512 512"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M256 0C114.6 0 0 114.6 0 256s114.6 256 256 256s256-114.6 256-256S397.4 0 256 0zM256 128c39.77 0 72 32.24 72 72S295.8 272 256 272c-39.76 0-72-32.24-72-72S216.2 128 256 128zM256 448c-52.93 0-100.9-21.53-135.7-56.29C136.5 349.9 176.5 320 224 320h64c47.54 0 87.54 29.88 103.7 71.71C356.9 426.5 308.9 448 256 448z"
    />
  </svg>
`;

// al eliminar la foto, se reemplaza por el ícono
document.addEventListener("htmx:afterRequest", function (e) {
  // foto eliminada, reemplazar por el ícono
  if (e.detail.xhr.status === 200) {
    document.getElementById("foto").outerHTML = icono;

    // actualizar fotos en el menú de navegación
    document
      .querySelectorAll(".cabecera-foto-perfil")
      .forEach(
        (foto) =>
          (foto.outerHTML = icono.replace(
            'id="foto"',
            "id='cabecera-foto-perfil' class='cabecera-foto-perfil'",
          )),
      );
  }
});
