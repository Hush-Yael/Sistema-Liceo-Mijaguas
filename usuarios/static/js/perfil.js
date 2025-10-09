const modal = document.getElementById("img-dialog");
const vetAvatar = document.getElementById("ver-avatar");

modal.addEventListener("click", function (e) {
  if (e.target === modal) modal.close();
});

vetAvatar.addEventListener("click", function () {
  const avatar = document.getElementById("avatar");

  if (avatar.tagName !== "svg") modal.showModal();
});

document.querySelector("form").addEventListener("change", function (e) {
  if (e.target.id === "id_foto_perfil") {
    const archivo = e.target.files[0];

    if (archivo) {
      if (archivo.size > 5242880) {
        alert("El archivo no puede superar los 5MB.");
        return (e.target.value = "");
      }

      const avatar = document.getElementById("avatar");
      const url = URL.createObjectURL(e.target.files[0]);

      if (avatar.tagName === "svg") {
        const nuevoAvatar = document.createElement("IMG");

        nuevoAvatar.classList.add("avatar");
        nuevoAvatar.setAttribute("src", url);
        nuevoAvatar.setAttribute("id", "avatar");
        nuevoAvatar.setAttribute("alt", "avatar");

        avatar.parentElement.replaceChild(nuevoAvatar, avatar);
      } else avatar.setAttribute("src", url);

      modal.querySelector("img").src = url;
    }
  }
});

// sin foto
const icono = `
  <svg
    class="cabecera-avatar"
    role="img"
    viewBox="0 0 512 512"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M256 0C114.6 0 0 114.6 0 256s114.6 256 256 256s256-114.6 256-256S397.4 0 256 0zM256 128c39.77 0 72 32.24 72 72S295.8 272 256 272c-39.76 0-72-32.24-72-72S216.2 128 256 128zM256 448c-52.93 0-100.9-21.53-135.7-56.29C136.5 349.9 176.5 320 224 320h64c47.54 0 87.54 29.88 103.7 71.71C356.9 426.5 308.9 448 256 448z"
    />
  </svg>
`;

document.addEventListener("htmx:afterRequest", function (e) {
  // foto eliminada, reemplazar por el ícono
  if (e.detail.xhr.status === 200) {
    document.getElementById("avatar").outerHTML = icono;

    // actualizar fotos en el menú de navegación
    fotosEnCabecera = document
      .querySelectorAll(".cabecera-avatar")
      .forEach(
        (foto) =>
          (foto.outerHTML = icono.replace(
            'id="avatar"',
            "id='cabecera-avatar'",
          )),
      );
  }
});
