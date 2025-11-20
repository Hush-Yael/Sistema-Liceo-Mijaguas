from typing import Tuple
from django import forms
from django.shortcuts import render
import json


# Guarda cookies a la vez que renderiza la plantilla deseada
def render_con_cookies(request, nombre_archivo, context, cookies_a_guardar):
    respuesta = render(
        request,
        nombre_archivo,
        context,
    )

    for clave, valor in cookies_a_guardar:
        respuesta.set_cookie(clave, valor)

    return respuesta


# Para determinar los valores iniciales de un formulario de filtros a partir de las cookies y corregir las que no tengan un valor válido
def obtener_y_corregir_valores_iniciales(cookies: dict, form: forms.Form):
    # print(f"Cookies recibidas: {cookies}")
    cookies_a_corregir: list[Tuple] = []

    # cambiar los valores iniciales del form al cargar la página
    for id, campo in form.fields.items():
        if (cookie := cookies.get(id)) is not None:
            try:
                if isinstance(campo, forms.ModelMultipleChoiceField):
                    cookie = json.loads(cookie)
                    campo.initial = cookie

                # validar que el valor de la cookie sea correcto para indicarlo como valor inicial al campo
                else:
                    valor_valido = campo.clean(cookie)
                    campo.initial = valor_valido
            # si no lo es, se deja como está y se manda a corregir la cookie con el valor por defecto
            except (ValueError, forms.ValidationError):
                # print(f'La cookie "{id}" no tenía un valor válido --> {cookie}')
                cookies_a_corregir.append((id, campo.initial))

            # print(f"Campo <{id}>: initial = {campo.initial}, cookie = {cookie}")
        """ else:
          print(f"Campo <{id}>: initial = {campo.initial}") """

    # print(f"Cookies a corregir: {cookies_a_corregir}")
    return cookies_a_corregir


# Para verificar que un formulario de filtros creado a partir de los datos (POST) sea válido, y guardar los valores de los campos en cookies, para luego poder cargarlos al abrir la página por primera vez con la función anterior
def verificar_y_aplicar_filtros(form_poblado: forms.Form):
    cookies_para_guardar = []

    # validar el form para que los campos cuyos valores no sean válidos tengan su valor por defecto
    form_poblado.is_valid()

    for id, campo in form_poblado.fields.items():
        # filtros de selección múltiple
        if isinstance(campo, forms.ModelMultipleChoiceField):
            queryset = form_poblado.cleaned_data.get(id)

            if not queryset:
                cookies_para_guardar.append((id, None))
            elif hasattr(queryset, "values_list"):
                cookies_para_guardar.append(
                    (id, json.dumps(list(queryset.values_list("pk", flat=True))))
                )
        # filtros de campos individuales
        else:
            valor = form_poblado.cleaned_data.get(id)

            cookies_para_guardar.append((id, str(valor)))

        # print(f"Campo <{id}>, con valor <{form_poblado.cleaned_data.get(id)}>")

    # print("Datos del form:", form_poblado.data)

    return cookies_para_guardar
