import streamlit as st
import os
import hashlib
from datetime import datetime, timezone
import couchdb_utils

# --- Configuración Inicial ---
st.set_page_config(layout="wide", page_title="Perfil Personal", page_icon="../assets/LOGO.png")
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)

# --- Mapeo de roles ---
ROLES_MAP = {
    1: "1-Admin",
    2: "2-Caja", 
    3: "3-Mesero",
    4: "4-Bar",
    5: "5-Cocina",
    6: "6-Operativo"
}

def get_role_name(role_id):
    """Obtiene el nombre del rol basado en el ID"""
    return ROLES_MAP.get(role_id, f"{role_id}-Desconocido")

# --- Funciones auxiliares ---
def hash_password(password):
    """Hashea una contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def validar_password(password):
    """Valida los requisitos de la contraseña"""
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    if not any(c.isdigit() for c in password):
        return False, "La contraseña debe contener al menos un número"
    if not any(c.isalpha() for c in password):
        return False, "La contraseña debe contener al menos una letra"
    return True, ""

# --- Lógica Principal ---
if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        st.title("👤 Mi Perfil Personal")
        
        # Obtener datos del usuario actual
        user_id = st.session_state.get('user_data', {}).get('_id')
        current_username = st.session_state.get('user_data', {}).get('usuario')
        
        if not user_id:
            st.error("No se pudo obtener la información del usuario actual.")
        else:
            try:
                # Obtener los datos actuales del usuario desde la base de datos
                user_doc = db[user_id]
                
                st.markdown("---")
                
                # Mostrar información actual
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader("📋 Información Actual")
                    st.markdown(f"""
                    **👤 Usuario:** {user_doc.get('usuario', 'N/A')}  
                    **📝 Nombre:** {user_doc.get('nombre', 'N/A')} {user_doc.get('apellido', '')}  
                    **📧 Correo:** {user_doc.get('correo', 'N/A')}  
                    **📞 Teléfono:** {user_doc.get('telefono', 'N/A')}  
                    **🏢 Rol:** {get_role_name(user_doc.get('id_rol', 0)) if user_doc.get('id_rol') else 'N/A'}  
                    **📅 Última actualización:** {user_doc.get('fecha_modificacion', 'N/A')[:10] if user_doc.get('fecha_modificacion') else 'N/A'}
                    """)
                
                with col2:
                    st.subheader("✏️ Editar Mi Información")
                    
                    with st.form("editar_perfil", clear_on_submit=False):
                        # Campos editables
                        nuevo_nombre = st.text_input("Nombre *", value=user_doc.get('nombre', ''), max_chars=50)
                        nuevo_apellido = st.text_input("Apellido", value=user_doc.get('apellido', ''), max_chars=50)
                        nuevo_correo = st.text_input("Correo Electrónico *", value=user_doc.get('correo', ''), max_chars=100)
                        nuevo_telefono = st.text_input("Teléfono", value=user_doc.get('telefono', ''), max_chars=15)
                        
                        st.markdown("**Cambiar Contraseña (Opcional)**")
                        nueva_password = st.text_input("Nueva Contraseña", type="password", help="Deja en blanco para mantener la actual")
                        confirmar_password = st.text_input("Confirmar Nueva Contraseña", type="password")
                        
                        # Botón de actualización
                        submitted = st.form_submit_button("💾 Actualizar Mi Información", type="primary", use_container_width=True)
                        
                        if submitted:
                            # Validaciones
                            errores = []
                            
                            if not nuevo_nombre.strip():
                                errores.append("El nombre es obligatorio")
                            
                            if not nuevo_correo.strip():
                                errores.append("El correo es obligatorio")
                            elif "@" not in nuevo_correo:
                                errores.append("El correo debe tener un formato válido")
                            
                            # Validar contraseña si se proporciona
                            if nueva_password:
                                if nueva_password != confirmar_password:
                                    errores.append("Las contraseñas no coinciden")
                                else:
                                    password_valid, password_error = validar_password(nueva_password)
                                    if not password_valid:
                                        errores.append(password_error)
                            
                            if errores:
                                for error in errores:
                                    st.error(f"❌ {error}")
                            else:
                                try:
                                    # Actualizar los datos
                                    user_doc['nombre'] = nuevo_nombre.strip()
                                    user_doc['apellido'] = nuevo_apellido.strip()
                                    user_doc['correo'] = nuevo_correo.strip().lower()
                                    user_doc['telefono'] = nuevo_telefono.strip()
                                    user_doc['fecha_modificacion'] = datetime.now(timezone.utc).isoformat()
                                    
                                    # Actualizar contraseña si se proporcionó
                                    if nueva_password:
                                        user_doc['password'] = hash_password(nueva_password)
                                    
                                    # Guardar en la base de datos
                                    db.save(user_doc)
                                    
                                    # Actualizar session state con los nuevos datos
                                    st.session_state.user_data.update({
                                        'nombre': nuevo_nombre.strip(),
                                        'apellido': nuevo_apellido.strip(),
                                        'correo': nuevo_correo.strip().lower(),
                                        'telefono': nuevo_telefono.strip(),
                                        'fecha_modificacion': user_doc['fecha_modificacion']
                                    })
                                    
                                    # Log de la acción
                                    couchdb_utils.log_action(
                                        db, 
                                        current_username, 
                                        f"Usuario '{current_username}' actualizó su perfil personal"
                                    )
                                    
                                    st.success("✅ Tu información ha sido actualizada exitosamente!")
                                    
                                    # Recargar la página para mostrar los cambios
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ Error al actualizar tu información: {str(e)}")
                
                # Sección adicional: Información de sesión
                st.markdown("---")
                st.subheader("🔐 Información de Sesión")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.markdown(f"""
                    **🆔 ID de Usuario:** `{user_id[:12]}...`  
                    **⏰ Sesión iniciada:** {st.session_state.get('login_time', 'N/A')}  
                    **🔑 Estado:** Activo  
                    """)
                
                with col4:
                    if st.button("🚪 Cerrar Sesión", type="secondary", use_container_width=True):
                        # Limpiar session state
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.success("Sesión cerrada exitosamente")
                        st.rerun()
                
                # Sección de ayuda
                st.markdown("---")
                with st.expander("ℹ️ Información y Ayuda"):
                    st.markdown("""
                    ### 📖 Cómo usar esta página:
                    
                    **✏️ Editar Información:**
                    - Modifica tus datos personales en el formulario de la derecha
                    - Los campos marcados con * son obligatorios
                    - Los cambios se guardan inmediatamente al hacer clic en "Actualizar"
                    
                    **🔒 Cambiar Contraseña:**
                    - Solo llena los campos de contraseña si quieres cambiarla
                    - La contraseña debe tener al menos 6 caracteres con números y letras
                    - Deja los campos vacíos para mantener tu contraseña actual
                    
                    **⚠️ Importante:**
                    - Todos los cambios quedan registrados en el log del sistema
                    - Si cambias tu correo, asegúrate de que sea válido
                    - Si tienes problemas, contacta al administrador
                    """)
                
            except Exception as e:
                st.error(f"❌ Error al cargar tu información: {str(e)}")
    
    else:
        st.error("❌ No se pudo conectar a la base de datos.")
        
else:
    st.info("🔐 Por favor, inicia sesión para acceder a tu perfil personal.")