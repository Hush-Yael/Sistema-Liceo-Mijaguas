# Solo profesores (10 por defecto)
python manage.py poblar_datos_ejemplo --profesores

# Solo estudiantes (30 estudiantes)
python manage.py poblar_datos_ejemplo --estudiantes --cantidad-estudiantes=30

# Solo lapsos para 2do año
python manage.py poblar_datos_ejemplo --lapsos --año=2

# Solo asignaciones de materias
python manage.py poblar_datos_ejemplo --asignaciones

# Solo matrículas
python manage.py poblar_datos_ejemplo --matriculas

# Solo notas
python manage.py poblar_datos_ejemplo --notas

# Crear solo secciones (4 secciones por año)
python manage.py poblar_datos_ejemplo --secciones --secciones-por-año=4

# Datos completos con secciones específicas
python manage.py poblar_datos_ejemplo --año=2 --todo --secciones-por-año=4 --cantidad-estudiantes=80

# Solo asignar tutores a secciones
python manage.py poblar_datos_ejemplo --asignar-tutores

# Ver distribución de estudiantes por sección
python manage.py poblar_datos_ejemplo --ver-distribucion

# Combinaciones
python manage.py poblar_datos_ejemplo --profesores --estudiantes --cantidad-profesores=12 --cantidad-estudiantes=50