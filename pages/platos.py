# pages/platos.py
import streamlit as st
import json
from datetime import datetime, timezone
import couchdb_utils
import os
import pandas as pd

# Obtener la ruta relativa de la página
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = "platos"

# Llama a la función de login/menú/validación
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Gestión de Platos", page_icon="../assets/LOGO.png")

# --- CSS EXTERNO ---
css_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'style.css')
if os.path.exists(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning(f"Archivo CSS no encontrado en: {css_file_path}")

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()

    if db:
        # --- Sección de Crear Nuevo Plato ---
        st.header("Crear Nuevo Plato")

        # Initialize session state for dialogs
        if 'show_new_plato_dialog' not in st.session_state:
            st.session_state.show_new_plato_dialog = False
        if 'show_edit_plato_dialog' not in st.session_state:
            st.session_state.show_edit_plato_dialog = False

        # Botón para abrir el diálogo de nuevo plato
        if st.button("➕ Crear Nuevo Plato", key="open_new_plato_dialog_btn"):
            st.session_state.show_new_plato_dialog = True

        # --- Función para el diálogo de creación de nuevo plato ---
        @st.dialog("Nuevo Plato")
        def render_new_plato_form_dialog():
            with st.form("new_plato_form_dialog", clear_on_submit=True):
                # Obtener los menús disponibles para el selectbox
                menu_items = couchdb_utils.get_documents_by_partition(db, "menus")
                active_menus = [item for item in menu_items if item.get('activo', 0) == 1]
                menu_options = {item['nombre']: item['_id'] for item in active_menus}
                
                new_plato_descripcion = st.text_area("Descripción:", key="dialog_new_plato_descripcion").strip()
                new_plato_id_menu = st.selectbox(
                    "Menú:", 
                    options=list(menu_options.keys()),
                    format_func=lambda x: x,
                    key="dialog_new_plato_menu"
                )
                new_plato_usa_ingrediente = st.checkbox("Usa Ingrediente", value=True, key="dialog_new_plato_usa_ingrediente")
                new_plato_precio_normal = st.number_input("Precio Normal:", min_value=0.0, step=0.5, key="dialog_new_plato_precio_normal")
                new_plato_precio_oferta = st.number_input("Precio Oferta (opcional):", min_value=0.0, step=0.5, key="dialog_new_plato_precio_oferta")
                new_plato_imagen = st.text_input("URL Imagen (opcional):", value="", key="dialog_new_plato_imagen")
                new_plato_activo = st.checkbox("Activo", value=True, key="dialog_new_plato_activo")
                
                st.markdown("---")
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit_button = st.form_submit_button("Guardar Nuevo Plato", type="primary")
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancelar")

                if submit_button:
                    if not new_plato_descripcion or not new_plato_id_menu:
                        st.error("Descripción y Menú son obligatorios.")
                    else:
                        new_plato_doc = {
                            "descripcion": new_plato_descripcion,
                            "id_menu": menu_options[new_plato_id_menu],
                            "nombre_menu": new_plato_id_menu,  # Guardamos también el nombre para fácil referencia
                            "usa_ingrediente": 1 if new_plato_usa_ingrediente else 0,
                            "precio_normal": float(new_plato_precio_normal),
                            "precio_oferta": float(new_plato_precio_oferta) if new_plato_precio_oferta else None,
                            "imagen": new_plato_imagen,
                            "activo": 1 if new_plato_activo else 0,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds')
                        }
                        if couchdb_utils.save_document_with_partition(db, new_plato_doc, CURRENT_PARTITION_KEY, 'descripcion'):
                            st.success(f"Plato '{new_plato_descripcion}' creado exitosamente.")
                            
                            # LOGGING
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Plato '{new_plato_descripcion}' agregado satisfactoriamente.")

                            st.session_state.show_new_plato_dialog = False
                            st.rerun()
                
                if cancel_button:
                    st.session_state.show_new_plato_dialog = False
                    st.rerun()

        # Mostrar diálogo de creación si está activo
        if st.session_state.show_new_plato_dialog:
            render_new_plato_form_dialog()

        # --- Sección de Ver Platos Activos ---
        st.header("Lista de Platos Activos")

        if 'selected_plato_doc' not in st.session_state: 
            st.session_state.selected_plato_doc = None

        col_filter_plato_desc, col_refresh_btn = st.columns([2, 1])
        with col_filter_plato_desc:
            filter_plato_desc = st.text_input("Filtrar por Descripción:", help="Escribe parte de la descripción para filtrar.", key="filter_plato_desc").strip().lower()
        with col_refresh_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualizar Lista de Platos", key="refresh_plato_table_btn"):
                st.session_state.selected_plato_doc = None
                st.rerun()

        all_platos_raw = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
        
        # Obtener nombres de menú para mostrar
        menu_items = couchdb_utils.get_documents_by_partition(db, "menus")
        menu_names = {item['_id']: item['nombre'] for item in menu_items}
        
        active_platos = []
        for plato in all_platos_raw:
            if plato.get('activo', 0) == 1:
                if not filter_plato_desc or filter_plato_desc in plato.get('descripcion', '').lower():
                    plato['nombre_menu'] = menu_names.get(plato.get('id_menu', ''), 'Menú no encontrado')
                    active_platos.append(plato)
        
        disabled_platos = []
        for plato in all_platos_raw:
            if plato.get('activo', 0) == 0:
                if not filter_plato_desc or filter_plato_desc in plato.get('descripcion', '').lower():
                    plato['nombre_menu'] = menu_names.get(plato.get('id_menu', ''), 'Menú no encontrado')
                    disabled_platos.append(plato)

        # --- Función para el diálogo de edición de plato ---
        @st.dialog("Editar Plato")
        def edit_plato_dialog_content():
            if 'selected_plato_doc' not in st.session_state or not st.session_state.selected_plato_doc:
                st.error("No se ha seleccionado ningún plato para editar.")
                return

            plato_to_edit = st.session_state.selected_plato_doc.copy()

            st.markdown(f"### Editar Plato: {plato_to_edit.get('descripcion', 'N/A')}")
            # st.markdown("---")

            with st.form("edit_plato_form", clear_on_submit=False):
                # st.caption(f"ID: `{plato_to_edit.get('_id', 'N/A')}`")
                # st.caption(f"Revisión: `{plato_to_edit.get('_rev', 'N/A')}`")

                # Obtener menús disponibles para el selectbox
                menu_items = couchdb_utils.get_documents_by_partition(db, "menus")
                active_menus = [item for item in menu_items if item.get('activo', 0) == 1]
                menu_options = {item['nombre']: item['_id'] for item in active_menus}
                
                edited_descripcion = st.text_area("Descripción:", value=plato_to_edit.get("descripcion", ""), key="edit_plato_descripcion")
                
                # Establecer el menú actual como valor por defecto
                current_menu_name = plato_to_edit.get('nombre_menu', '')
                default_index = list(menu_options.keys()).index(current_menu_name) if current_menu_name in menu_options else 0
                edited_menu_name = st.selectbox(
                    "Menú:", 
                    options=list(menu_options.keys()),
                    index=default_index,
                    key="edit_plato_menu"
                )
                
                edited_usa_ingrediente = st.checkbox("Usa Ingrediente", value=bool(plato_to_edit.get("usa_ingrediente", 0)), key="edit_plato_usa_ingrediente")
                edited_precio_normal = st.number_input("Precio Normal:", min_value=0.0, step=0.5, value=float(plato_to_edit.get("precio_normal", 0)), key="edit_plato_precio_normal")
                edited_precio_oferta = st.number_input("Precio Oferta (opcional):", min_value=0.0, step=0.5, value=float(plato_to_edit.get("precio_oferta", 0)) if plato_to_edit.get("precio_oferta") else st.number_input("Precio Oferta (opcional):", min_value=0.0, step=0.5, key="edit_plato_precio_oferta"))
                edited_imagen = st.text_input("URL Imagen (opcional):", value=plato_to_edit.get("imagen", ""), key="edit_plato_imagen")
                edited_activo = st.checkbox("Activo", value=bool(plato_to_edit.get("activo", 0)), key="edit_plato_activo")
                
                # st.markdown("---")
                col_submit, col_cancel, col_toggle_active = st.columns(3)
                
                with col_submit:
                    save_button = st.form_submit_button("Guardar Cambios", type="primary")
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancelar")
                with col_toggle_active:
                    toggle_active_label = "🚫 Deshabilitar" if bool(plato_to_edit.get("activo", 0)) else "✅ Habilitar"
                    toggle_active_button = st.form_submit_button(toggle_active_label)

                if save_button:
                    plato_to_edit["descripcion"] = edited_descripcion
                    plato_to_edit["id_menu"] = menu_options[edited_menu_name]
                    plato_to_edit["nombre_menu"] = edited_menu_name
                    plato_to_edit["usa_ingrediente"] = 1 if edited_usa_ingrediente else 0
                    plato_to_edit["precio_normal"] = float(edited_precio_normal)
                    plato_to_edit["precio_oferta"] = float(edited_precio_oferta) if edited_precio_oferta else None
                    plato_to_edit["imagen"] = edited_imagen
                    plato_to_edit["activo"] = 1 if edited_activo else 0
                    
                    if couchdb_utils.save_document_with_partition(db, plato_to_edit, CURRENT_PARTITION_KEY, 'descripcion'):
                        st.success(f"Plato '{plato_to_edit.get('descripcion')}' actualizado exitosamente.")
                        
                        # LOGGING
                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        couchdb_utils.log_action(db, logged_in_user, f"Plato '{plato_to_edit.get('descripcion')}' actualizado satisfactoriamente.")

                        st.session_state.selected_plato_doc = None
                        st.session_state.show_edit_plato_dialog = False
                        st.rerun()
                
                if cancel_button:
                    st.session_state.selected_plato_doc = None
                    st.session_state.show_edit_plato_dialog = False
                    st.rerun()

                if toggle_active_button:
                    plato_to_toggle = plato_to_edit.copy()
                    new_status = 0 if bool(plato_to_edit.get("activo", 0)) else 1
                    plato_to_toggle['activo'] = new_status
                    
                    if couchdb_utils.save_document_with_partition(db, plato_to_toggle, CURRENT_PARTITION_KEY, 'descripcion'):
                        st.session_state.selected_plato_doc = None
                        st.session_state.show_edit_plato_dialog = False
                        status_text = "deshabilitado" if new_status == 0 else "habilitado"
                        st.success(f"Plato '{plato_to_toggle.get('descripcion')}' {status_text} exitosamente.")
                        
                        # LOGGING
                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        couchdb_utils.log_action(db, logged_in_user, f"Plato '{plato_to_toggle.get('descripcion')}' {status_text} satisfactoriamente.")

                        st.rerun()

        # Función para manejar el clic en el botón "Editar"
        def on_edit_button_click(plato_doc):
            st.session_state.selected_plato_doc = plato_doc
            st.session_state.show_edit_plato_dialog = True
            st.rerun()

        # Mostrar diálogo de edición si está activo
        if st.session_state.show_edit_plato_dialog:
            edit_plato_dialog_content()

        # Mostrar platos activos
        if active_platos:
            # Encabezados de la tabla
            col_id_header, col_desc_header, col_menu_header, col_ingrediente_header, col_precio_header, col_imagen_header, col_activo_header, col_edit_header = st.columns([1, 2, 1, 0.8, 1, 1, 0.5, 0.7])
            with col_id_header:
                st.markdown("**ID**")
            with col_desc_header:
                st.markdown("**Descripción**")
            with col_menu_header:
                st.markdown("**Menú**")
            with col_ingrediente_header:
                st.markdown("**Usa Ingrediente**")
            with col_precio_header:
                st.markdown("**Precio**")
            with col_imagen_header:
                st.markdown("**Imagen**")
            with col_activo_header:
                st.markdown("**Activo**")
            with col_edit_header:
                st.markdown("**Acciones**")
            # st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)

            for plato in active_platos:
                with st.container():
                    col_id, col_desc, col_menu, col_ingrediente, col_precio, col_imagen, col_activo, col_edit = st.columns([1, 2, 1, 0.8, 1, 1, 0.5, 0.7])
                    with col_id:
                        st.caption(plato.get('_id', 'N/A'))
                    with col_desc:
                        st.write(plato.get('descripcion', 'N/A'))
                    with col_menu:
                        st.write(plato.get('nombre_menu', 'N/A'))
                    with col_ingrediente:
                        st.checkbox("usa ingrediente", value=bool(plato.get('usa_ingrediente', 0)), disabled=True, key=f"ingrediente_{plato.get('_id')}", label_visibility="collapsed")
                    with col_precio:
                        precio_normal = plato.get('precio_normal', 0)
                        precio_oferta = plato.get('precio_oferta')
                        col1, col2 = st.columns([1,1])
                        with col1:
                            st.write(f"${precio_normal:.2f}")
                        with col2:
                            st.write(f"${precio_oferta:.2f}")
                        # if precio_oferta:
                        #     st.markdown(f"<span style='text-decoration: line-through; color: gray;'>${precio_normal:.2f}</span> <span style='color: red;'>${precio_oferta:.2f}</span>", unsafe_allow_html=True)
                        # else:
                        #     st.write(f"${precio_normal:.2f}")
                    with col_imagen:
                        if plato.get('imagen'):
                            st.image(plato['imagen'], width=50, use_column_width="always")
                        else:
                            st.write("N/A")
                    with col_activo:
                        st.checkbox("estado activo", value=bool(plato.get('activo', 0)), disabled=True, key=f"activo_{plato.get('_id')}", label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"edit_btn_{plato.get('_id')}"):
                            on_edit_button_click(plato)
                    # st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)
        else:
            st.info("No hay platos activos en la base de datos o no coinciden con el filtro.")

        # --- Sección de Platos Deshabilitados ---
        st.header("Platos Deshabilitados")

        if disabled_platos:
            # Encabezados de la tabla
            col_id_header_dis, col_desc_header_dis, col_menu_header_dis, col_ingrediente_header_dis, col_precio_header_dis, col_imagen_header_dis, col_activo_header_dis, col_edit_header_dis = st.columns([1, 2, 1, 0.8, 1, 1, 0.5, 0.7])
            with col_id_header_dis:
                st.markdown("**ID**")
            with col_desc_header_dis:
                st.markdown("**Descripción**")
            with col_menu_header_dis:
                st.markdown("**Menú**")
            with col_ingrediente_header_dis:
                st.markdown("**Usa Ingrediente**")
            with col_precio_header_dis:
                st.markdown("**Precio**")
            with col_imagen_header_dis:
                st.markdown("**Imagen**")
            with col_activo_header_dis:
                st.markdown("**Activo**")
            with col_edit_header_dis:
                st.markdown("**Acciones**")
            # st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)

            for plato in disabled_platos:
                with st.container():
                    col_id, col_desc, col_menu, col_ingrediente, col_precio, col_imagen, col_activo, col_edit = st.columns([1, 2, 1, 0.8, 1, 1, 0.5, 0.7])
                    with col_id:
                        st.caption(plato.get('_id', 'N/A'))
                    with col_desc:
                        st.write(plato.get('descripcion', 'N/A'))
                    with col_menu:
                        st.write(plato.get('nombre_menu', 'N/A'))
                    with col_ingrediente:
                        st.checkbox("usa ingrediente", value=bool(plato.get('usa_ingrediente', 0)), disabled=True, key=f"dis_ingrediente_{plato.get('_id')}", label_visibility="collapsed")
                    with col_precio:
                        precio_normal = plato.get('precio_normal', 0)
                        precio_oferta = plato.get('precio_oferta')
                        col1, col2 = st.columns([1,1])
                        with col1:
                            st.write(f"${precio_normal:.2f}")
                        with col2:
                            st.write(f"${precio_oferta:.2f}")
                        # if precio_oferta:
                        #     st.markdown(f"<span style='text-decoration: line-through; color: gray;'>${precio_normal:.2f}</span> <span style='color: red;'>${precio_oferta:.2f}</span>", unsafe_allow_html=True)
                        # else:
                        #     st.write(f"${precio_normal:.2f}")
                    with col_imagen:
                        if plato.get('imagen'):
                            st.image(plato['imagen'], width=50, use_column_width="always")
                        else:
                            st.write("N/A")
                    with col_activo:
                        st.checkbox("", value=bool(plato.get('activo', 0)), disabled=True, key=f"dis_activo_{plato.get('_id')}", label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"dis_edit_btn_{plato.get('_id')}"):
                            on_edit_button_click(plato)
                    # st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)
        else:
            st.info("No hay platos deshabilitados en la base de datos o no coinciden con el filtro.")

    else:
        st.error("No se pudo conectar o configurar la base de datos. Revisa los mensajes de conexión.")