import re
from django.template import base as template_base
from django.http import HttpResponseRedirect

# Soporte para etiquetas de plantilla multilínea
template_base.tag_re = re.compile(template_base.tag_re.pattern, re.DOTALL)


# Soporte para redirecciones con HTMX
class HTTPResponseHXRedirect(HttpResponseRedirect):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["HX-Redirect"] = self["Location"]

    status_code = 200
