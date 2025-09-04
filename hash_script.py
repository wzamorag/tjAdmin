import sys
import os

# Asegúrate de que la ruta a couchdb_utils.py esté en sys.path
# Si tu script está en la misma carpeta que couchdb_utils.py, esto no es estrictamente necesario,
# pero es una buena práctica si lo ejecutas desde otro lugar.
# Por ejemplo, si couchdb_utils.py está en 'tjAdminPy', y ejecutas esto desde 'tjAdminPy':
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# O si lo ejecutas desde la raíz del proyecto y couchdb_utils.py está en 'tjAdminPy':
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tjAdminPy'))

# Para este ejemplo, asumiremos que puedes importar couchdb_utils directamente
# Si no funciona, revisa tu PYTHONPATH o las rutas de importación.
try:
    import couchdb_utils
except ImportError:
    print("Error: No se pudo importar 'couchdb_utils.py'. Asegúrate de que el archivo esté en la misma carpeta o en tu PYTHONPATH.")
    sys.exit(1)

password_to_hash = "tiajuana2020"
hashed_password = couchdb_utils.hash_password(password_to_hash)

print(f"La contraseña original es: {password_to_hash}")
print(f"La contraseña encriptada (hashed) es: {hashed_password}")

# Puedes verificarla (opcional)
if couchdb_utils.check_password(password_to_hash, hashed_password):
    print("La verificación del hash fue exitosa.")
else:
    print("¡Advertencia! La verificación del hash falló.")