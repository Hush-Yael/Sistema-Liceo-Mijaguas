from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView,
)
from django.http import HttpRequest, HttpResponse

from liceo.forms import FormularioPerfil, FormularioRegistro


@login_required
def inicio(request: HttpRequest):
    return render(request, "inicio.html")


def login(request: HttpRequest):
    if not request.user.is_authenticated:
        return LoginView.as_view(
            template_name="auth/login.html",
        )(request)
    else:
        return redirect("/")


def registro(request: HttpRequest):
    if request.method == "POST":
        user_form = FormularioRegistro(request.POST)

        if user_form.is_valid():
            nuevo_usuario = user_form.save(commit=False)
            nuevo_usuario.set_password(user_form.cleaned_data["password"])
            nuevo_usuario.save()

            return render(request, "auth/registrado.html", {"new_user": nuevo_usuario})
    else:
        user_form = FormularioRegistro()
    return render(request, "auth/registro.html", {"form": user_form})


def cerrar_sesion(request: HttpRequest):
    return LogoutView.as_view(
        next_page="/",
    )(request)


@login_required
def cambiar_contraseña(request: HttpRequest):
    return PasswordChangeView.as_view(
        template_name="auth/cambiar-contraseña.html",
    )(request)


@login_required
def contraseña_cambiada(request: HttpRequest):
    return PasswordChangeDoneView.as_view(
        template_name="auth/contraseña-cambiada.html",
    )(request)


@login_required
def perfil(request: HttpRequest):
    if request.method == "DELETE":
        try:
            request.user.foto_perfil.delete()  # type: ignore
            return HttpResponse(
                """
                <span class='eliminado'>
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M17 3.34a10 10 0 1 1 -14.995 8.984l-.005 -.324l.005 -.324a10 10 0 0 1 14.995 -8.336zm-1.293 5.953a1 1 0 0 0 -1.32 -.083l-.094 .083l-3.293 3.292l-1.293 -1.292l-.094 -.083a1 1 0 0 0 -1.403 1.403l.083 .094l2 2l.094 .083a1 1 0 0 0 1.226 0l.094 -.083l4 -4l.083 -.094a1 1 0 0 0 -.083 -1.32z" /></svg>

                  Foto eliminada
                </span>
              """,
                status=200,
            )
        except Exception as e:
            print("Error al eliminar la foto", e)
            return HttpResponse("Error al eliminar la foto", status=204)

    elif request.method == "POST":
        form = FormularioPerfil(request.POST, request.FILES, instance=request.user)  # type: ignore

        if form.is_valid():
            form.save()
    else:
        form = FormularioPerfil(instance=request.user)  # type: ignore

    return render(
        request,
        "perfil.html",
        {"form": form},
    )
