# Solo profesores (10 por defecto)
python manage.py poblar_datos_ejemplo --profesores

# Solo estudiantes (30 estudiantes)
python manage.py poblar_datos_ejemplo --estudiantes --cantidad-estudiantes=30

# Solo lapsos para 2do año
python manage.py poblar_datos_ejemplo --lapsos --ano=2

# Solo asignaciones de materias
python manage.py poblar_datos_ejemplo --asignaciones

# Solo matrículas
python manage.py poblar_datos_ejemplo --matriculas

# Solo calificaciones
python manage.py poblar_datos_ejemplo --calificaciones

# Combinaciones
python manage.py poblar_datos_ejemplo --profesores --estudiantes --cantidad-profesores=12 --cantidad-estudiantes=50