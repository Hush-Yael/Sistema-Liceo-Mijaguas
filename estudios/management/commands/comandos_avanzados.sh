# Para tercer año con muchos estudiantes
python manage.py poblar_datos_ejemplo --ano=3 --estudiantes --cantidad-estudiantes=100

# Limpiar solo profesores y recrearlos
python manage.py poblar_datos_ejemplo --limpiar-todo --profesores --cantidad-profesores=15

# Datos completos para cuarto año
python manage.py poblar_datos_ejemplo --ano=4 --todo --cantidad-estudiantes=35 --cantidad-profesores=10