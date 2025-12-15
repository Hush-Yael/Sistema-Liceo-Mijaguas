# ============================================================================
# EJEMPLOS DE USO
# ============================================================================

from .core import analizar_grupo_variantes, transformador_grupo_variantes


if __name__ == "__main__":
    # Ejemplos de uso directo en Python
    test_cases = [
        "min-md:(bg-red text-blue)",
        "hover:(bg-blue-500 text-white)",
        "dark:(bg-gray-800 text-white) focus:(ring-2 ring-blue-500)",
        "lg:(flex grid) md:(p-4 m-2)",
        "foo-(bar baz)",
        "before:(content-[''] block)",
    ]

    print("=== Pruebas de transformación de grupos de variantes ===\n")

    for test in test_cases:
        result = analizar_grupo_variantes(test)
        print(f"Entrada:  {test}")
        print(f"Salida:   {result['expanded']}")
        print(f"Prefijos: {result['prefixes']}")
        print(f"Cambios:  {result['has_changed']}")
        print("-" * 50)

    # Ejemplo de uso del transformador
    print("\n=== Ejemplo usando el transformador ===\n")
    transformer = transformador_grupo_variantes()
    test_string = "hover:(bg-blue-500 text-white) focus:(outline-none ring-2)"
    transformed = transformer["transform"](test_string)

    print(f"Entrada: {test_string}")
    print("Anotaciones de resaltado:")
    for ann in transformed["highlight_annotations"]:
        print(f"  - {ann}")
