# auth.py
import streamlit as st
from streamlit_cookies_controller import CookieController
import uuid

def get_controller():
    # Crear un controlador único por sesión usando session_id
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    session_key = f'_cookie_controller_{st.session_state.session_id}'
    
    if not hasattr(st, session_key):
        # Crear un controlador único para esta sesión
        controller = CookieController()
        # Evitamos el conflicto con st.session_state
        controller._CookieController__cookies = {}
        setattr(st, session_key, controller)
    
    return getattr(st, session_key)

def initialize_auth():
    # Inicialización segura por sesión
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    session_auth_key = f'_auth_initialized_{st.session_state.session_id}'
    
    if not hasattr(st, session_auth_key):
        get_controller()  # Esto inicializa el controlador para esta sesión
        setattr(st, session_auth_key, True)

