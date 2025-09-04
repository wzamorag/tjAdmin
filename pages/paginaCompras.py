import streamlit as st
import os

import couchdb_utils # ¡Importa os!


# Obtener la ruta relativa de la página para la validación
# Esto convertirá '/home/.../pages/usuarios.py' a 'pages/usuarios.py'
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# O, si quieres que solo sea 'usuarios.py' y tu CSV está configurado así:
# archivo_actual_relativo = os.path.basename(__file__)


# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = couchdb_utils.PARTITION_KEY

# Llama a la función de login/menú/validación con la ruta corregida
couchdb_utils.generarLogin(archivo_actual_relativo) 

if 'usuario' in st.session_state:
    st.header('Página :red[Compras]')