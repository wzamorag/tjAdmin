# pages/login_page.py
from datetime import time
import streamlit as st
import couchdb_utils
import os

from auth import get_controller
# Obtener controlador específico de esta sesión
controller = get_controller()
if 'usuario' in st.session_state or controller.get('usuario'):
    # Limpieza total usando la función de logout segura
    couchdb_utils.logout_user()
    # La función logout_user ya maneja la limpieza completa
    
    # JavaScript de respaldo
    js = """
    <script>
        if (!window.location.href.includes('login_page')) {
            localStorage.clear();
            sessionStorage.clear();
            window.location.replace(window.location.origin + '/login_page.py');
        }
    </script>
    """
    st.components.v1.html(js, height=0)
    time.sleep(0.5)  # Pequeña pausa para asegurar la ejecución
    st.rerun()
st.set_page_config(
    page_title="Iniciar Sesión", # Puedes poner un título específico para la pestaña del navegador
    layout="centered",          # Esto centrará el contenido y le dará un ancho fijo
    page_icon="../assets/LOGO.png"  # Favicon del sitio
    # initial_sidebar_state="collapsed" # Asegúrate de que el sidebar esté colapsado por defecto aquí
)
# Obtén la ruta relativa para la validación, si es necesario (aunque para el login_page, no hay permisos)
# archivo_para_validacion = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
# O simplemente:
archivo_para_validacion = "pages/login_page.py" # O lo que decidas que sea su identificador si lo pusieras en CSV

# Asegúrate de que no haya sidebar ni contenido adicional al inicio
# Si ya se intentó un login y falló o la sesión se borró, mostrar el formulario de login.
# La función generarLogin en couchdb_utils.py ya maneja esto.

# Llamar directamente al formulario de login.
# Aquí no necesitamos validar permisos para esta página porque es la de login.
couchdb_utils.generarLogin(archivo_para_validacion)

# Puedes añadir un mensaje o un st.empty() para asegurarte de que no haya contenido duplicado
# st.empty() # Esto ayuda a limpiar la página si algo se renderizó antes