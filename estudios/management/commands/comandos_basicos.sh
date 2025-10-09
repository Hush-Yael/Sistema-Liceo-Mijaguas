# Solo datos estáticos (una vez)
python manage.py poblar_datos_estaticos

# Todos los datos dinámicos para primer año
python manage.py poblar_datos_ejemplo --todo

# Limpiar todo y recrear
python manage.py poblar_datos_ejemplo --limpiar-todo --todo