import re
from django.template import base as template_base

# Soporte para etiquetas de plantilla multilínea
template_base.tag_re = re.compile(template_base.tag_re.pattern, re.DOTALL)
