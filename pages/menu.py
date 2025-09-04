# pages/menu.py
import streamlit as st
import json
from datetime import datetime, timezone
import couchdb_utils # Importa el módulo de utilidades
import os
import pandas as pd # Necesario para st.dataframe

# Obtener la ruta relativa de la página (ej. 'pages/menu.py')
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = "menus" # Clave de partición para los documentos de menú

# Llama a la función de login/menú/validación con la ruta corregida
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Gestión de Menús)", page_icon="../assets/LOGO.png")





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

    # Helper function to log actions (re-using from couchdb_utils)
    # No es necesario redefinirla aquí, se usa la de couchdb_utils directamente
    # def log_action(db_instance, user_who_performed_action, description):
    #     ...

    if db:
        # --- Sección de Crear Nuevo Elemento de Menú (Diálogo Modal) ---
        st.header("Crear Nuevo Elemento de Menú")

        # Initialize session state for dialog visibility
        if 'show_new_menu_dialog' not in st.session_state:
            st.session_state.show_new_menu_dialog = False
        if 'show_edit_menu_dialog' not in st.session_state:
            st.session_state.show_edit_menu_dialog = False

        # Botón para abrir el diálogo de nuevo elemento
        if st.button("➕ Crear Nuevo Elemento", key="open_new_menu_item_dialog_btn"):
            st.session_state.show_new_menu_dialog = True # Set state to show dialog

        # --- Función para el contenido del diálogo de creación de nuevo elemento de menú ---
        @st.dialog("Nuevo Menu") # Decorador para definir el diálogo
        def render_new_menu_item_form_dialog():
            # st.markdown("### Crear Nuevo Elemento de Menú")
            # st.markdown("---")
            with st.form("new_menu_item_form_dialog", clear_on_submit=True):
                new_menu_nombre = st.text_input("Nombre del Menú:", key="dialog_new_menu_nombre_input").strip()
                # MODIFICACIÓN: Usar st.selectbox para la zona
                zona_options = ["Bar", "Cocina","Admin"]
                new_menu_zona = st.selectbox("Zona:", options=zona_options, key="dialog_new_menu_zona_input")

                # new_menu_zona = st.text_input("Zona (ej. 'Comida', 'Bebida'):", key="dialog_new_menu_zona_input").strip()
                new_menu_imagen = st.text_input("URL Imagen (opcional):", value="", key="dialog_new_menu_imagen_input")
                new_menu_activo = st.checkbox("Activo", value=True, key="dialog_new_menu_activo_input")
                
                st.markdown("---")
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit_button = st.form_submit_button("Guardar Nuevo Elemento", type="primary")
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancelar")

                if submit_button:
                    if not new_menu_nombre or not new_menu_zona:
                        st.error("Nombre del Menú y Zona son obligatorios.")
                    else:
                        new_menu_doc = {
                            "nombre": new_menu_nombre,
                            "zona": new_menu_zona,
                            "imagen": new_menu_imagen,
                            "activo": 1 if new_menu_activo else 0,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds')
                        }
                        if couchdb_utils.save_document_with_partition(db, new_menu_doc, CURRENT_PARTITION_KEY, 'nombre'):
                            st.success(f"Elemento de menú '{new_menu_nombre}' creado exitosamente.")
                            
                            # LOGGING: Elemento de menú agregado
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Elemento de menú '{new_menu_nombre}' agregado satisfactoriamente.")

                            st.session_state.show_new_menu_dialog = False # Close dialog
                            st.rerun() # Recargar para cerrar el diálogo y actualizar la lista
                
                if cancel_button:
                    st.session_state.show_new_menu_dialog = False # Close dialog
                    st.rerun() # Recargar para cerrar el diálogo sin guardar

        # Conditional call to display the dialog
        if st.session_state.show_new_menu_dialog:
            render_new_menu_item_form_dialog()


        # st.markdown("---")

        # --- Sección de Ver Elementos de Menú Activos ---
        st.header("Lista de Elementos de Menú Activos")

        if 'selected_menu_item_doc' not in st.session_state: st.session_state.selected_menu_item_doc = None

        col_filter_menu_name, col_refresh_btn = st.columns([2, 1])
        with col_filter_menu_name:
            filter_menu_name = st.text_input("Filtrar por Nombre del Menú:", help="Escribe el nombre del menú exacto para filtrar.", key="filter_menu_name_table").strip().lower()
        with col_refresh_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualizar Lista de Menús", key="refresh_menu_table_btn"):
                st.session_state.selected_menu_item_doc = None # Limpiar selección al refrescar
                st.rerun()

        all_menu_items_raw = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
        
        active_menu_items = [item for item in all_menu_items_raw if item.get('activo', 0) == 1 and (not filter_menu_name or item.get('nombre', '').lower() == filter_menu_name)]
        disabled_menu_items = [item for item in all_menu_items_raw if item.get('activo', 0) == 0 and (not filter_menu_name or item.get('nombre', '').lower() == filter_menu_name)]


        # --- Función para el contenido del diálogo de edición de elemento de menú ---
       # --- Función para el contenido del diálogo de edición de elemento de menú ---
        @st.dialog("Editar Menu")
        def edit_menu_item_dialog_content():
            if 'selected_menu_item_doc' not in st.session_state or not st.session_state.selected_menu_item_doc:
                st.error("No se ha seleccionado ningún elemento de menú para editar.")
                return

            menu_item_to_edit = st.session_state.selected_menu_item_doc.copy()

            st.markdown(f"### Editar Elemento: {menu_item_to_edit.get('nombre', 'N/A')}")
            st.markdown("---")

            with st.form("edit_menu_item_form", clear_on_submit=False):
                st.caption(f"ID: `{menu_item_to_edit.get('_id', 'N/A')}`")
                st.caption(f"Revisión: `{menu_item_to_edit.get('_rev', 'N/A')}`")

                edited_nombre = st.text_input("Nombre del Menú:", value=menu_item_to_edit.get("nombre", ""), key="edit_menu_nombre")
                zona_options = ["Bar", "Cocina", "Admin"]
                current_zona_index = zona_options.index(menu_item_to_edit.get("zona", "Bar")) if menu_item_to_edit.get("zona", "Bar") in zona_options else 0
                edited_zona = st.selectbox("Zona:", options=zona_options, index=current_zona_index, key="edit_menu_zona")
                edited_imagen = st.text_input("URL Imagen (opcional):", value=menu_item_to_edit.get("imagen", ""), key="edit_menu_imagen")
                edited_activo = st.checkbox("Activo", value=bool(menu_item_to_edit.get("activo", 0)), key="edit_menu_activo")
                
                st.markdown("---")
                col_submit, col_cancel, col_toggle_active = st.columns(3)
                
                with col_submit:
                    save_button = st.form_submit_button("Guardar Cambios", type="primary")
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancelar")
                with col_toggle_active:
                    toggle_active_label = "🚫 Deshabilitar Elemento" if bool(menu_item_to_edit.get("activo", 0)) else "✅ Habilitar Elemento"
                    toggle_active_button = st.form_submit_button(toggle_active_label)

                if save_button:
                    # Mantenemos el _id y _rev originales para actualizar el documento existente
                    updated_doc = {
                        "_id": menu_item_to_edit["_id"],
                        "_rev": menu_item_to_edit["_rev"],
                        "nombre": edited_nombre,
                        "zona": edited_zona,
                        "imagen": edited_imagen,
                        "activo": 1 if edited_activo else 0,
                        "fecha_creacion": menu_item_to_edit.get("fecha_creacion"),  # Mantenemos la fecha original
                        "type": CURRENT_PARTITION_KEY  # Asegurar que el type se mantenga
                    }
                    
                    try:
                        # Usamos put en lugar de save_document_with_partition para actualización directa
                        db.save(updated_doc)
                        st.success(f"Elemento '{edited_nombre}' actualizado exitosamente.")
                        
                        # LOGGING
                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        couchdb_utils.log_action(db, logged_in_user, f"Elemento de menú '{edited_nombre}' actualizado satisfactoriamente.")

                        st.session_state.selected_menu_item_doc = None
                        st.session_state.show_edit_menu_dialog = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar los cambios: {str(e)}")
                
                if cancel_button:
                    st.session_state.selected_menu_item_doc = None
                    st.session_state.show_edit_menu_dialog = False
                    st.rerun()

                if toggle_active_button:
                    try:
                        # Para alternar estado, también mantenemos _id y _rev
                        toggled_doc = {
                            "_id": menu_item_to_edit["_id"],
                            "_rev": menu_item_to_edit["_rev"],
                            "nombre": menu_item_to_edit["nombre"],
                            "zona": menu_item_to_edit["zona"],
                            "imagen": menu_item_to_edit.get("imagen", ""),
                            "activo": 0 if bool(menu_item_to_edit.get("activo", 0)) else 1,
                            "fecha_creacion": menu_item_to_edit.get("fecha_creacion"),
                            "type": CURRENT_PARTITION_KEY
                        }
                        
                        db.save(toggled_doc)
                        status_text = "deshabilitado" if toggled_doc["activo"] == 0 else "habilitado"
                        st.success(f"Elemento '{toggled_doc['nombre']}' {status_text} exitosamente.")
                        
                        # LOGGING
                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        couchdb_utils.log_action(db, logged_in_user, f"Elemento de menú '{toggled_doc['nombre']}' {status_text} satisfactoriamente.")

                        st.session_state.selected_menu_item_doc = None
                        st.session_state.show_edit_menu_dialog = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al cambiar estado: {str(e)}")

        # Función para manejar el clic en el botón "Editar" de la tabla
        # def on_edit_button_click(menu_item_doc):
        #     st.session_state.selected_menu_item_doc = menu_item_doc # Almacenar el doc seleccionado
        #     st.session_state.show_edit_menu_dialog = True # Set state to show dialog
        def on_edit_button_click(menu_item_doc):
            st.session_state.selected_menu_item_doc = menu_item_doc # Almacenar el doc seleccionado
            st.session_state.show_edit_menu_dialog = True # Set state to show dialog
            st.rerun() # Force a rerun to immediately display the dialog

        # Conditional call to display the edit dialog
        if st.session_state.show_edit_menu_dialog:
            edit_menu_item_dialog_content()


        if active_menu_items: # Mostrar solo elementos de menú activos
            # st.subheader("Elementos de Menú Activos:")
            # Display headers
            col_id_header, col_nombre_header, col_zona_header, col_imagen_header, col_activo_header, col_edit_header = st.columns([1, 1, 1, 2, 0.5, 0.7])
            with col_id_header:
                st.markdown("**ID Documento**")
            with col_nombre_header:
                st.markdown("**Nombre**")
            with col_zona_header:
                st.markdown("**Zona**")
            with col_imagen_header:
                st.markdown("**Imagen (URL)**")
            with col_activo_header:
                st.markdown("**Activo**")
            with col_edit_header:
                st.markdown("**Acciones**")
            st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True) # Separador para los encabezados

            for i, menu_item_doc in enumerate(active_menu_items): # Iterar sobre active_menu_items
                with st.container():
                    col_id, col_nombre, col_zona, col_imagen, col_activo, col_edit = st.columns([1, 1, 1, 2, 0.5, 0.7])
                    with col_id:
                        st.caption(menu_item_doc.get('_id', 'N/A'))
                    with col_nombre:
                        st.write(menu_item_doc.get('nombre', 'N/A'))
                    with col_zona:
                        st.write(menu_item_doc.get('zona', 'N/A'))
                    with col_imagen:
                        if menu_item_doc.get('imagen'):
                            st.image(menu_item_doc['imagen'], width=50, caption="Imagen", use_column_width="always") # Ajusta el ancho según necesidad
                        else:
                            st.write("N/A")
                    with col_activo:
                        st.checkbox("Estado Activo", value=bool(menu_item_doc.get('activo', 0)), disabled=True, key=f"active_status_{menu_item_doc.get('_id', i)}",label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"edit_btn_{menu_item_doc.get('_id', i)}"):
                            on_edit_button_click(menu_item_doc)
                    st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True) # Separador para cada fila

        else:
            st.info("No hay elementos de menú activos en la base de datos o no coinciden con el filtro.")

        # st.markdown("---")

        # --- NUEVA SECCIÓN: Elementos de Menú Deshabilitados ---
        st.header("Elementos de Menú Deshabilitados") # Nueva sección para deshabilitados

        if disabled_menu_items: # Mostrar solo elementos de menú deshabilitados
            # Display headers for the disabled menu item list
            col_id_header_dis, col_nombre_header_dis, col_zona_header_dis, col_imagen_header_dis, col_activo_header_dis, col_edit_header_dis = st.columns([1, 1, 1, 2, 0.5, 0.7])
            with col_id_header_dis:
                st.markdown("**ID Documento**")
            with col_nombre_header_dis:
                st.markdown("**Nombre**")
            with col_zona_header_dis:
                st.markdown("**Zona**")
            with col_imagen_header_dis:
                st.markdown("**Imagen (URL)**")
            with col_activo_header_dis:
                st.markdown("**Activo**")
            with col_edit_header_dis:
                st.markdown("**Acciones**")
            st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True) # Separador para los encabezados

            for i, menu_item_doc in enumerate(disabled_menu_items): # Iterar sobre disabled_menu_items
                with st.container():
                    col_id, col_nombre, col_zona, col_imagen, col_activo, col_edit = st.columns([1, 1, 1, 2, 0.5, 0.7])
                    with col_id:
                        st.caption(menu_item_doc.get('_id', 'N/A'))
                    with col_nombre:
                        st.write(menu_item_doc.get('nombre', 'N/A'))
                    with col_zona:
                        st.write(menu_item_doc.get('zona', 'N/A'))
                    with col_imagen:
                        if menu_item_doc.get('imagen'):
                            st.image(menu_item_doc['imagen'], width=50, caption="Imagen", use_column_width="always")
                        else:
                            st.write("N/A")
                    with col_activo:
                        st.checkbox("Estado Deshabilitado", value=bool(menu_item_doc.get('activo', 0)), disabled=True, key=f"disabled_active_status_{menu_item_doc.get('_id', i)}",label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"disabled_edit_btn_{menu_item_doc.get('_id', i)}"):
                            on_edit_button_click(menu_item_doc)
                    st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True) # Separador para cada fila
        else:
            st.info("No hay elementos de menú deshabilitados en la base de datos o no coinciden con el filtro.")

       
    else:
        st.error("No se pudo conectar o configurar la base de datos 'tiajuana'. Revisa los mensajes de conexión.")
