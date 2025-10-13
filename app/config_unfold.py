from django.templatetags.static import static

CONFIG = {
    "SITE_TITLE": "Panel de administración - Liceo Mijaguas",
    "SITE_HEADER": "Panel de administración",
    "SITE_LOGO": lambda _: static("img/logo-sin-letras.png"),
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda _: static("favicon.ico"),
        },
    ],
    "SIDEBAR": {
        "show_search": True,
    },
}
