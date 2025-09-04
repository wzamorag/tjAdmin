# pages/usuarios.py
# import pytz
import streamlit as st
# import json
from datetime import datetime, timezone
import couchdb_utils # Importa el módulo de utilidades
import os
import pandas as pd # Necesario para st.dataframe
# Obtener la ruta relativa de la página (ej. 'pages/usuarios.py')
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = couchdb_utils.PARTITION_KEY

# Mapeo de roles para mostrar nombres descriptivos
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

def get_role_options():
    """Retorna las opciones de roles para selectbox"""
    return list(ROLES_MAP.values())

def get_role_id_from_option(role_option):
    """Obtiene el ID del rol a partir de la opción seleccionada"""
    for role_id, role_name in ROLES_MAP.items():
        if role_name == role_option:
            return role_id
    return 1  # Default admin si no se encuentra

# Llama a la función de login/menú/validación con la ruta corregida
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Gestión Usuarios (CouchDB)", page_icon="../assets/LOGO.png")

# Restaurar el título principal y la información


# --- INICIO DE LA MODIFICACIÓN PARA CSS EXTERNO ---
# Ruta al archivo CSS (asumiendo que está en la misma carpeta raíz del proyecto)
css_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'style.css')

if os.path.exists(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning(f"Archivo CSS no encontrado en: {css_file_path}. Asegúrate de que 'style.css' esté en la ubicación correcta.")
# --- FIN DE LA MODIFICACIÓN PARA CSS EXTERNO ---

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()

  
    if db:
    

        # --- Sección de Crear Nuevo Usuario (Diálogo Modal) ---
        st.header("Crear Nuevo Usuario") # Restaurado

        # Initialize session state for dialog visibility
        if 'show_new_user_dialog' not in st.session_state:
            st.session_state.show_new_user_dialog = False
        if 'show_edit_user_dialog' not in st.session_state:
            st.session_state.show_edit_user_dialog = False

        # Botón para abrir el diálogo de nuevo usuario
        if st.button("➕ Crear Nuevo Usuario", key="open_new_user_dialog_btn"):
            st.session_state.show_new_user_dialog = True # Set state to show dialog

        # --- Función para el contenido del diálogo de creación de nuevo usuario (AHORA CON DECORADOR) ---
        @st.dialog("Crear Nuevo Usuario") # Decorador para definir el diálogo
        def render_new_user_form_dialog():
            st.markdown("### Crear Nuevo Usuario") # Restaurado
            st.markdown("---") # Restaurado
            with st.form("new_user_form_dialog", clear_on_submit=True): # Usar un key diferente para este formulario
                col_name, col_surname = st.columns(2)
                with col_name:
                    new_user_name = st.text_input("Nombre:", key="dialog_new_user_name_input") # Key única
                with col_surname:
                    new_user_apellido = st.text_input("Apellido:", key="dialog_new_user_apellido_input") # Key única
                
                col_email, col_username = st.columns(2)
                with col_email:
                    new_user_correo = st.text_input("Correo:", key="dialog_new_user_correo_input") # Key única
                with col_username:
                    new_user_username = st.text_input("Nombre de Usuario:", key="dialog_new_user_username_input").strip().lower() # Key única

                col_pass, col_image = st.columns(2)
                with col_pass:
                    new_user_password = st.text_input("Contraseña:", type="password", key="dialog_new_user_password_input") # Key única
                with col_image:
                    new_user_imagen = st.text_input("URL Imagen (opcional):", value="", key="dialog_new_user_imagen_input") # Key única

                col_rol, col_active = st.columns(2)
                with col_rol:
                    selected_role_option = st.selectbox("Rol:", options=get_role_options(), index=0, key="dialog_new_user_role_select")
                    new_user_id_rol = get_role_id_from_option(selected_role_option)
                with col_active:
                    new_user_activo = st.checkbox("Activo", value=True, key="dialog_new_user_activo_input") # Key única
                
                st.markdown("---") # Restaurado
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit_button = st.form_submit_button("Guardar Nuevo Usuario", type="primary")
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancelar")

                if submit_button:
                    if not new_user_username or not new_user_name or not new_user_password:
                        st.error("Nombre de Usuario, Nombre y Contraseña son obligatorios.")
                    else:
                        new_user_doc = {
                            "id_usr": 0, 
                            "nombre": new_user_name,
                            "apellido": new_user_apellido,
                            "correo": new_user_correo,
                            "usuario": new_user_username,
                            "password": couchdb_utils.hash_password(new_user_password), # ¡RECUERDA HASHEAR EN PROD!
                            "imagen": new_user_imagen,
                            "id_rol": new_user_id_rol,
                            "activo": 1 if new_user_activo else 0,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds')
                        }
                        if couchdb_utils.save_document_with_partition(db, new_user_doc, CURRENT_PARTITION_KEY, 'usuario'):
                            st.success(f"Usuario '{new_user_username}' creado exitosamente.")
                            
                            # LOGGING: Usuario agregado
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Usuario '{new_user_username}' agregado satisfactoriamente.")
                            
                            st.session_state.show_new_user_dialog = False # Close dialog
                            st.rerun() # Recargar para cerrar el diálogo y actualizar la lista
                
                if cancel_button:
                    st.session_state.show_new_user_dialog = False # Close dialog
                    st.rerun() # Recargar para cerrar el diálogo sin guardar

        # Conditional call to display the dialog
        if st.session_state.show_new_user_dialog:
            render_new_user_form_dialog()


        # st.markdown("---") # Restaurado

        # --- Sección de Ver Usuarios (Ahora con tabla interactiva) ---
        st.header("Lista de Usuarios Activos") # Restaurado

        if 'selected_user_doc' not in st.session_state: st.session_state.selected_user_doc = None
        if 'current_active_page' not in st.session_state: st.session_state.current_active_page = 0
        if 'current_disabled_page' not in st.session_state: st.session_state.current_disabled_page = 0
        if 'users_per_page' not in st.session_state: st.session_state.users_per_page = 10


        col_filter_username, col_refresh_btn = st.columns([2, 1])
        with col_filter_username:
            filter_username = st.text_input("Filtrar por Nombre de Usuario:", help="Escribe el nombre de usuario exacto para filtrar.", key="filter_username_table").strip().lower()
        with col_refresh_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualizar Lista", key="refresh_users_table_btn"):
                st.session_state.current_active_page = 0 # Reset pagination on refresh
                st.session_state.current_disabled_page = 0 # Reset pagination on refresh
                st.session_state.selected_user_doc = None # Limpiar selección al refrescar
                st.rerun()

        all_users_raw = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
        
        # Aplicar filtro por el campo 'usuario' y por estado 'activo'
        active_users = [user for user in all_users_raw if user.get('activo', 0) == 1 and (not filter_username or user.get('usuario', '').lower() == filter_username)]
        disabled_users = [user for user in all_users_raw if user.get('activo', 0) == 0 and (not filter_username or user.get('usuario', '').lower() == filter_username)]


        # --- Función para el contenido del diálogo de edición ---
        @st.dialog("Editar Usuario") # Decorador para definir el diálogo
        def edit_user_dialog_content():
            # Asegurarse de que el documento seleccionado está disponible
            if 'selected_user_doc' not in st.session_state or not st.session_state.selected_user_doc:
                st.error("No se ha seleccionado ningún usuario para editar. Por favor, cierra este diálogo y selecciona uno de la tabla.")
                return # Salir de la función si no hay datos

            user_to_edit = st.session_state.selected_user_doc.copy() # Trabajar con una copia


            with st.form("edit_user_form", clear_on_submit=False): # No limpiar al enviar para ver los cambios
                # st.caption(f"ID: `{user_to_edit.get('_id', 'N/A')}`")
                # st.caption(f"Revisión: `{user_to_edit.get('_rev', 'N/A')}`")

                col_name, col_surname = st.columns(2)
                with col_name:
                    edited_name = st.text_input("Nombre:", value=user_to_edit.get("nombre", ""), key="edit_user_name")
                with col_surname:
                    edited_apellido = st.text_input("Apellido:", value=user_to_edit.get("apellido", ""), key="edit_user_apellido")
                
                col_email, col_username = st.columns(2)
                with col_email:
                    edited_correo = st.text_input("Correo:", value=user_to_edit.get("correo", ""), key="edit_user_correo")
                with col_username:
                    # El nombre de usuario (parte de la clave de partición) no debería ser editable directamente aquí si se usa para el _id
                    st.text_input("Nombre de Usuario:", value=user_to_edit.get("usuario", ""), disabled=True, key="edit_user_username_display")

                col_pass, col_image = st.columns(2)
                with col_pass:
                    # La contraseña no se pre-rellena por seguridad, se edita si es necesario
                    edited_password = st.text_input("Nueva Contraseña (dejar vacío para no cambiar):", type="password", key="edit_user_password")
                with col_image:
                    edited_imagen = st.text_input("URL Imagen (opcional):", value=user_to_edit.get("imagen", ""), key="edit_user_imagen")

                col_rol, col_active = st.columns(2)
                with col_rol:
                    current_role_id = user_to_edit.get("id_rol", 1)
                    current_role_name = get_role_name(current_role_id)
                    current_index = get_role_options().index(current_role_name) if current_role_name in get_role_options() else 0
                    selected_role_option_edit = st.selectbox("Rol:", options=get_role_options(), index=current_index, key="edit_user_role_select")
                    edited_id_rol = get_role_id_from_option(selected_role_option_edit)
                with col_active:
                    edited_activo = st.checkbox("Activo", value=bool(user_to_edit.get("activo", 0)), key="edit_user_activo")
                
                st.markdown("---") # Restaurado
                col_submit, col_cancel, col_disable_dialog = st.columns(3)
                
                with col_submit:
                    save_button = st.form_submit_button("Guardar Cambios", type="primary")
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancelar")
                with col_disable_dialog:
                    # Botón de deshabilitar dentro del diálogo para el usuario actual
                    # disable_button_dialog = st.form_submit_button("✅ Habilitar Usuario")
                    toggle_active_button = "🚫 Deshabilitar Elemento" if bool(user_to_edit.get("activo", 0)) else "✅ Habilitar Elemento"
                    disable_button_dialog = st.form_submit_button(toggle_active_button)
                    

                if save_button:
                    # Actualizar el documento con los nuevos valores del formulario
                    user_to_edit["nombre"] = edited_name
                    user_to_edit["apellido"] = edited_apellido
                    user_to_edit["correo"] = edited_correo
                    user_to_edit["imagen"] = edited_imagen
                    user_to_edit["id_rol"] = edited_id_rol
                    user_to_edit["activo"] = 1 if edited_activo else 0
                    
                    # Solo actualizar la contraseña si se proporcionó una nueva
                    if edited_password:
                        user_to_edit["password"] = couchdb_utils.hash_password(edited_password) # HASHEAR LA NUEVA CONTRASEÑA AQUÍ
                    # Si no se proporciona una nueva contraseña, la contraseña existente (hasheada) se mantiene

                    if couchdb_utils.save_document_with_partition(db, user_to_edit, CURRENT_PARTITION_KEY, 'usuario'):
                        st.success(f"Usuario '{user_to_edit.get('usuario')}' actualizado exitosamente.")
                        
                        # LOGGING: Usuario actualizado
                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        if not couchdb_utils.log_action(db, logged_in_user, f"Usuario '{user_to_edit.get('usuario')}' actualizado satisfactoriamente."):
                            st.warning("No se pudo registrar la actividad de actualización de usuario en los logs.") 

                        st.session_state.selected_user_doc = None # Limpiar selección
                        st.session_state.show_edit_user_dialog = False # Close dialog
                        st.rerun() # Recargar para cerrar el diálogo y actualizar la lista
                    else:
                        st.error("Error al guardar los cambios del usuario.")
                
                if cancel_button:
                    st.session_state.selected_user_doc = None # Limpiar selección
                    st.session_state.show_edit_user_dialog = False # Close dialog
                    st.rerun() # Recargar para cerrar el diálogo sin guardar

                if disable_button_dialog:
                    user_to_disable = user_to_edit.copy()
                    new_status = 0 if bool(user_to_edit.get("activo", 0)) else 1
                    user_to_disable['activo'] = new_status
                    # user_to_disable['activo'] = 0 # Establecer activo a 0
                    
                    
                    if couchdb_utils.save_document_with_partition(db, user_to_disable, CURRENT_PARTITION_KEY, 'usuario'):
                        st.session_state.selected_user_doc = None # Limpiar selección
                        st.session_state.show_edit_user_dialog = False # Close dialog
                        st.success(f"Usuario '{user_to_disable.get('usuario')}' deshabilitado exitosamente.")
                        
                        # LOGGING: Usuario deshabilitado
                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        if new_status == 0:
                            couchdb_utils.log_action(db, logged_in_user, f"Usuario '{user_to_disable.get('usuario')}' deshabilitado satisfactoriamente.")
                        else:
                            couchdb_utils.log_action(db, logged_in_user, f"Usuario '{user_to_disable.get('usuario')}' habilitado satisfactoriamente.")
                        # if not couchdb_utils.log_action(db, logged_in_user, f"Usuario '{user_to_disable.get('usuario')}' deshabilitado satisfactoriamente."):
                        #     st.warning("No se pudo registrar la actividad de deshabilitación de usuario en los logs.") 

                        st.rerun()
                    else:
                        st.error("Error al deshabilitar el usuario.")


        # Función para manejar el clic en el botón "Editar" de la tabla
        def on_edit_button_click(user_doc):
            st.session_state.selected_user_doc = user_doc # Almacenar el doc seleccionado
            st.session_state.show_edit_user_dialog = True # Set state to show dialog
            st.rerun() # Force a rerun to immediately display the dialog


        # Conditional call to display the edit dialog
        if st.session_state.show_edit_user_dialog:
            edit_user_dialog_content()


        if active_users: # Mostrar solo usuarios activos
            st.subheader("Usuarios Registrados:") # Restaurado
            # Display headers for the user list
            col_id_header, col_user_header, col_name_header, col_email_header, col_role_header, col_active_header, col_edit_header = st.columns([1, 1, 1, 2, 0.5, 0.5, 0.7])
            with col_id_header:
                st.markdown("**ID Documento**")
            with col_user_header:
                st.markdown("**Usuario**")
            with col_name_header:
                st.markdown("**Nombre Completo**")
            with col_email_header:
                st.markdown("**Correo Electrónico**")
            with col_role_header:
                st.markdown("**Rol**")
            with col_active_header:
                st.markdown("**Activo**")
            with col_edit_header:
                st.markdown("**Acciones**")
            st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True) # Separador para los encabezados

            # Paginación para usuarios activos
            total_active_users = len(active_users)
            total_active_pages = (total_active_users + st.session_state.users_per_page - 1) // st.session_state.users_per_page
            
            start_active_idx = st.session_state.current_active_page * st.session_state.users_per_page
            end_active_idx = min(start_active_idx + st.session_state.users_per_page, total_active_users)
            
            active_users_to_display = active_users[start_active_idx:end_active_idx]

            for i, user_doc in enumerate(active_users_to_display): # MODIFICADO: Iterar sobre active_users_to_display
                # Usamos un contenedor para cada fila para agrupar los elementos y el botón
                with st.container():
                    col_id, col_user, col_name, col_email, col_role, col_active, col_edit = st.columns([1, 1, 1, 2, 0.5, 0.5, 0.7])
                    with col_id:
                        st.caption(user_doc.get('_id', 'N/A'))
                    with col_user:
                        st.write(user_doc.get('usuario', 'N/A'))
                    with col_name:
                        st.write(f"{user_doc.get('nombre', 'N/A')} {user_doc.get('apellido', '')}")
                    with col_email:
                        st.write(user_doc.get('correo', 'N/A'))
                    with col_role:
                        role_id = user_doc.get('id_rol', 'N/A')
                        st.write(get_role_name(role_id) if role_id != 'N/A' else 'N/A')
                    with col_active:
                        st.checkbox("Estado Activo", value=bool(user_doc.get('activo', 0)), disabled=True, key=f"active_status_{user_doc.get('_id', i)}",label_visibility="collapsed")
                    with col_edit:
                        # Pass the entire user_doc to the on_edit_button_click function
                        if st.button("Editar", key=f"edit_btn_{user_doc.get('_id', i)}"):
                            on_edit_button_click(user_doc)
                    st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True) # Separador para cada fila de usuario

            # Controles de paginación para usuarios activos
            col_prev_active, col_page_info_active, col_next_active = st.columns([1, 2, 1])
            with col_prev_active:
                if st.button("Página Anterior (Activos)", key="prev_active_page_btn", disabled=st.session_state.current_active_page == 0):
                    st.session_state.current_active_page -= 1
                    st.rerun()
            with col_page_info_active:
                st.markdown(f"Página {st.session_state.current_active_page + 1} de {total_active_pages} (Total: {total_active_users} activos)")
            with col_next_active:
                if st.button("Página Siguiente (Activos)", key="next_active_page_btn", disabled=st.session_state.current_active_page >= total_active_pages - 1):
                    st.session_state.current_active_page += 1
                    st.rerun()

        else:
            st.info("No hay usuarios activos en la base de datos o no coinciden con el filtro.")

        # st.markdown("---") # Restaurado

        # --- NUEVA SECCIÓN: Usuarios Deshabilitados ---
        st.header("Usuarios Deshabilitados") # Restaurado

        if disabled_users: # Mostrar solo usuarios deshabilitados
            # Display headers for the disabled user list
            col_id_header_dis, col_user_header_dis, col_name_header_dis, col_email_header_dis, col_role_header_dis, col_active_header_dis, col_edit_header_dis = st.columns([1, 1, 1, 2, 0.5, 0.5, 0.7])
            with col_id_header_dis:
                st.markdown("**ID Documento**")
            with col_user_header_dis:
                st.markdown("**Usuario**")
            with col_name_header_dis:
                st.markdown("**Nombre Completo**")
            with col_email_header_dis:
                st.markdown("**Correo Electrónico**")
            with col_role_header_dis:
                st.markdown("**Rol**")
            with col_active_header_dis:
                st.markdown("**Activo**")
            with col_edit_header_dis:
                st.markdown("**Acciones**")
            st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True) # Separador para los encabezados

            # Paginación para usuarios deshabilitados
            total_disabled_users = len(disabled_users)
            total_disabled_pages = (total_disabled_users + st.session_state.users_per_page - 1) // st.session_state.users_per_page
            
            start_disabled_idx = st.session_state.current_disabled_page * st.session_state.users_per_page
            end_disabled_idx = min(start_disabled_idx + st.session_state.users_per_page, total_disabled_users)
            
            disabled_users_to_display = disabled_users[start_disabled_idx:end_disabled_idx]

            for i, user_doc in enumerate(disabled_users_to_display): # MODIFICADO: Iterar sobre disabled_users_to_display
                with st.container():
                    col_id, col_user, col_name, col_email, col_role, col_active, col_edit = st.columns([1, 1, 1, 2, 0.5, 0.5, 0.7])
                    with col_id:
                        st.caption(user_doc.get('_id', 'N/A'))
                    with col_user:
                        st.write(user_doc.get('usuario', 'N/A'))
                    with col_name:
                        st.write(f"{user_doc.get('nombre', 'N/A')} {user_doc.get('apellido', '')}")
                    with col_email:
                        st.write(user_doc.get('correo', 'N/A'))
                    with col_role:
                        role_id = user_doc.get('id_rol', 'N/A')
                        st.write(get_role_name(role_id) if role_id != 'N/A' else 'N/A')
                    with col_active:
                        st.checkbox("Estado Desactivado", value=bool(user_doc.get('activo', 0)), disabled=True, key=f"disabled_active_status_{user_doc.get('_id', i)}",label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"disabled_edit_btn_{user_doc.get('_id', i)}"):
                            on_edit_button_click(user_doc)
                    st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True) # Separador para cada fila de usuario
            # Controles de paginación para usuarios deshabilitados
            col_prev_disabled, col_page_info_disabled, col_next_disabled = st.columns([1, 2, 1])
            with col_prev_disabled:
                if st.button("Página Anterior (Deshabilitados)", key="prev_disabled_page_btn", disabled=st.session_state.current_disabled_page == 0):
                    st.session_state.current_disabled_page -= 1
                    st.rerun()
            with col_page_info_disabled:
                st.markdown(f"Página {st.session_state.current_disabled_page + 1} de {total_disabled_pages} (Total: {total_disabled_users} deshabilitados)")
            with col_next_disabled:
                if st.button("Página Siguiente (Deshabilitados)", key="next_disabled_page_btn", disabled=st.session_state.current_disabled_page >= total_disabled_pages - 1):
                    st.session_state.current_disabled_page += 1
                    st.rerun()
        else:
            st.info("No hay usuarios deshabilitados en la base de datos o no coinciden con el filtro.")

       

    else:
        st.error("No se pudo conectar o configurar la base de datos 'tiajuana'. Revisa los mensajes de conexión.")
