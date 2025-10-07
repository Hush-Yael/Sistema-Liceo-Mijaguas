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
