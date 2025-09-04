# pages/proveedores.py
import streamlit as st
import json
from datetime import datetime, timezone
import couchdb_utils
import os
import pandas as pd
import uuid

# Obtener la ruta relativa de la página
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = "proveedores"

# Llama a la función de login/menú/validación
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Gestión de Proveedores", page_icon="../assets/LOGO.png")

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
        # --- Sección de Crear Nuevo Proveedor ---
        st.header("Crear Nuevo Proveedor")
        
        # Usamos st.expander como alternativa al diálogo
        with st.expander("➕ Crear Nuevo Proveedor", expanded=False):
            with st.form("new_proveedor_form", clear_on_submit=True):
                # Primera fila de campos
                col1, col2 = st.columns(2)
                with col1:
                    new_proveedor_nombre = st.text_input("Nombre:", key="new_proveedor_nombre").strip()
                with col2:
                    new_proveedor_direccion = st.text_input("Dirección:", key="new_proveedor_direccion").strip()
                
                # Segunda fila de campos
                col3, col4 = st.columns(2)
                with col3:
                    departamento_options = ["Santa Ana Centro", "Santa Ana Oeste", "Otro"]
                    new_proveedor_departamento = st.selectbox(
                        "Departamento:", 
                        options=departamento_options,
                        key="new_proveedor_departamento"
                    )
                with col4:
                    nacionalidad_options = ["Salvadoreña", "Extranjera"]
                    new_proveedor_nacionalidad = st.selectbox(
                        "Nacionalidad:",
                        options=nacionalidad_options,
                        index=nacionalidad_options.index("Salvadoreña"),
                        key="new_proveedor_nacionalidad"
                    )

                # Tercera fila de campos
                col5, col6,col7 = st.columns(3)
                with col5:
                    new_proveedor_telefono = st.text_input("Teléfono:", key="new_proveedor_telefono").strip()
                with col6:
                    new_proveedor_nrc = st.text_input("NRC:", key="new_proveedor_nrc").strip()
                
                # # Cuarta fila de campos
                # col7, col8 = st.columns(2)
                # with col7:
                #     condicion_options = ["contado", "crédito"]
                #     new_proveedor_condicion = st.selectbox(
                #         "Condición de la operación:", 
                #         options=condicion_options,
                #         key="new_proveedor_condicion"
                #     )
                with col7:
                    new_proveedor_nit_dui = st.text_input("NIT/DUI:", key="new_proveedor_nit_dui").strip()
                col8, col9 = st.columns(2)
                with col8:
                    # Quinta fila de campos
                    new_proveedor_correo = st.text_input("Correo:", key="new_proveedor_correo").strip()
                with col9:
                    # Quinta fila de campos
                    new_proveedor_giro = st.text_input("Giro:", key="new_proveedor_giro").strip()
                
                new_proveedor_activo = st.checkbox("Activo", value=True, key="new_proveedor_activo")
                
                st.markdown("---")
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit_button = st.form_submit_button("Guardar Nuevo Proveedor", type="primary")
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancelar")

                if submit_button:
                    if not new_proveedor_nombre:
                        st.error("El nombre es obligatorio.")
                    else:
                        # Generamos un ID único con el formato correcto para particiones
                        doc_id = f"{CURRENT_PARTITION_KEY}:{str(uuid.uuid4())}"
                        
                        new_proveedor_doc = {
                            "_id": doc_id,
                            "nombre": new_proveedor_nombre,
                            "direccion": new_proveedor_direccion,
                            "departamento": new_proveedor_departamento,
                            "nacionalidad": new_proveedor_nacionalidad,
                            "telefono": new_proveedor_telefono,
                            "nrc": new_proveedor_nrc,
                            # "condicion": new_proveedor_condicion,
                            "nit_dui": new_proveedor_nit_dui,
                            "giro": new_proveedor_giro,
                            "correo": new_proveedor_correo,
                            "activo": 1 if new_proveedor_activo else 0,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                            "type": CURRENT_PARTITION_KEY
                        }
                        try:
                            db.save(new_proveedor_doc)
                            st.success(f"Proveedor '{new_proveedor_nombre}' creado exitosamente.")
                            
                            # LOGGING
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Proveedor '{new_proveedor_nombre}' agregado satisfactoriamente.")
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear proveedor: {str(e)}")
                
                if cancel_button:
                    st.rerun()

        # --- Sección de Ver Proveedores Activos ---
        st.header("Lista de Proveedores Activos")

        if 'selected_proveedor_doc' not in st.session_state: 
            st.session_state.selected_proveedor_doc = None

        col_filter_nombre, col_refresh_btn = st.columns([2, 1])
        with col_filter_nombre:
            filter_nombre = st.text_input("Filtrar por Nombre:", help="Escribe parte del nombre para filtrar.", key="filter_proveedor_nombre").strip().lower()
        with col_refresh_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualizar Lista de Proveedores", key="refresh_proveedor_table_btn"):
                st.session_state.selected_proveedor_doc = None
                st.rerun()

        all_proveedores_raw = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
        
        active_proveedores = [
            item for item in all_proveedores_raw 
            if item.get('activo', 0) == 1 
            and (not filter_nombre or filter_nombre in item.get('nombre', '').lower())
        ]
        
        disabled_proveedores = [
            item for item in all_proveedores_raw 
            if item.get('activo', 0) == 0 
            and (not filter_nombre or filter_nombre in item.get('nombre', '').lower())
        ]

        # --- Función para editar proveedor ---
        if 'show_edit_proveedor_dialog' not in st.session_state:
            st.session_state.show_edit_proveedor_dialog = False

        if st.session_state.show_edit_proveedor_dialog:
            proveedor_to_edit = st.session_state.selected_proveedor_doc.copy()
            
            with st.expander(f"✏️ Editando: {proveedor_to_edit.get('nombre', 'N/A')}", expanded=True):
                with st.form("edit_proveedor_form"):
                    st.caption(f"ID: `{proveedor_to_edit.get('_id', 'N/A')}`")
                    st.caption(f"Revisión: `{proveedor_to_edit.get('_rev', 'N/A')}`")

                    # Primera fila de campos
                    col1, col2 = st.columns(2)
                    with col1:
                        edited_nombre = st.text_input("Nombre:", value=proveedor_to_edit.get("nombre", ""), key="edit_proveedor_nombre")
                    with col2:
                        edited_direccion = st.text_input("Dirección:", value=proveedor_to_edit.get("direccion", ""), key="edit_proveedor_direccion")
                    
                    # Segunda fila de campos
                    col3, col4 = st.columns(2)
                    with col3:
                        departamento_options = ["Santa Ana Centro", "Santa Ana Oeste", "Otro"]
                        current_departamento_index = departamento_options.index(proveedor_to_edit.get("departamento", "Santa Ana Centro")) if proveedor_to_edit.get("departamento", "Santa Ana Centro") in departamento_options else 0
                        edited_departamento = st.selectbox(
                            "Departamento:", 
                            options=departamento_options,
                            index=current_departamento_index,
                            key="edit_proveedor_departamento"
                        )
                    with col4:
                        nacionalidad_options = ["Salvadoreña", "Extranjera"]
                        current_nacionalidad_index = nacionalidad_options.index(proveedor_to_edit.get("nacionalidad", "Salvadoreña")) if proveedor_to_edit.get("nacionalidad", "Salvadoreña") in nacionalidad_options else 0
                        edited_nacionalidad = st.selectbox(
                            "Nacionalidad:",
                            options=nacionalidad_options,
                            index=current_nacionalidad_index,
                            key="edit_proveedor_nacionalidad"
                        )

                    # Tercera fila de campos
                    col5, col6,col7 = st.columns(3)
                    with col5:
                        edited_telefono = st.text_input("Teléfono:", value=proveedor_to_edit.get("telefono", ""), key="edit_proveedor_telefono")
                    with col6:
                        edited_nrc = st.text_input("NRC:", value=proveedor_to_edit.get("nrc", ""), key="edit_proveedor_nrc")
                    
                    # # Cuarta fila de campos
                    # col7, col8 = st.columns(2)
                    # with col7:
                    #     condicion_options = ["contado", "crédito"]
                    #     current_condicion_index = condicion_options.index(proveedor_to_edit.get("condicion", "contado")) if proveedor_to_edit.get("condicion", "contado") in condicion_options else 0
                    #     edited_condicion = st.selectbox(
                    #         "Condición de la operación:", 
                    #         options=condicion_options,
                    #         index=current_condicion_index,
                    #         key="edit_proveedor_condicion"
                    #     )
                    with col7:
                        edited_nit_dui = st.text_input("NIT/DUI:", value=proveedor_to_edit.get("nit_dui", ""), key="edit_proveedor_nit_dui")
                    col8, col9 = st.columns(2)
                    with col8:
                        # Quinta fila de campos
                        edited_giro = st.text_input("Giro:", value=proveedor_to_edit.get("giro", ""), key="edit_proveedor_giro")
                    with col9:
                        # Quinta fila de campos
                        edited_correo = st.text_input("Correo:", value=proveedor_to_edit.get("correo", ""), key="edit_proveedor_correo")
                    
                    edited_activo = st.checkbox("Activo", value=bool(proveedor_to_edit.get("activo", 0)), key="edit_proveedor_activo")
                    
                    st.markdown("---")
                    col_submit, col_cancel, col_toggle_active = st.columns(3)
                    
                    with col_submit:
                        save_button = st.form_submit_button("Guardar Cambios", type="primary")
                    with col_cancel:
                        cancel_button = st.form_submit_button("Cancelar")
                    with col_toggle_active:
                        toggle_active_label = "🚫 Deshabilitar" if bool(proveedor_to_edit.get("activo", 0)) else "✅ Habilitar"
                        toggle_active_button = st.form_submit_button(toggle_active_label)

                    if save_button:
                        updated_doc = {
                            "_id": proveedor_to_edit["_id"],
                            "_rev": proveedor_to_edit["_rev"],
                            "nombre": edited_nombre,
                            "direccion": edited_direccion,
                            "departamento": edited_departamento,
                            "nacionalidad": edited_nacionalidad,
                            "telefono": edited_telefono,
                            "nrc": edited_nrc,
                            # "condicion": edited_condicion,
                            "nit_dui": edited_nit_dui,
                            "giro": edited_giro,
                            "correo": edited_correo,
                            "activo": 1 if edited_activo else 0,
                            "fecha_creacion": proveedor_to_edit.get("fecha_creacion"),
                            "type": CURRENT_PARTITION_KEY
                        }
                        
                        try:
                            db.save(updated_doc)
                            st.success(f"Proveedor '{edited_nombre}' actualizado exitosamente.")
                            
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Proveedor '{edited_nombre}' actualizado satisfactoriamente.")

                            st.session_state.selected_proveedor_doc = None
                            st.session_state.show_edit_proveedor_dialog = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar los cambios: {str(e)}")
                    
                    if cancel_button:
                        st.session_state.selected_proveedor_doc = None
                        st.session_state.show_edit_proveedor_dialog = False
                        st.rerun()

                    if toggle_active_button:
                        toggled_doc = {
                            "_id": proveedor_to_edit["_id"],
                            "_rev": proveedor_to_edit["_rev"],
                            "nombre": proveedor_to_edit["nombre"],
                            "direccion": proveedor_to_edit["direccion"],
                            "departamento": proveedor_to_edit["departamento"],
                            "nacionalidad": proveedor_to_edit["nacionalidad"],
                            "telefono": proveedor_to_edit["telefono"],
                            "nrc": proveedor_to_edit["nrc"],
                            # "condicion": proveedor_to_edit["condicion"],
                            "nit_dui": proveedor_to_edit["nit_dui"],
                            "giro": proveedor_to_edit["giro"],
                            "correo": proveedor_to_edit["correo"],
                            "activo": 0 if bool(proveedor_to_edit.get("activo", 0)) else 1,
                            "fecha_creacion": proveedor_to_edit.get("fecha_creacion"),
                            "type": CURRENT_PARTITION_KEY
                        }
                        
                        try:
                            db.save(toggled_doc)
                            status_text = "deshabilitado" if toggled_doc["activo"] == 0 else "habilitado"
                            st.success(f"Proveedor '{toggled_doc['nombre']}' {status_text} exitosamente.")
                            
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Proveedor '{toggled_doc['nombre']}' {status_text} satisfactoriamente.")

                            st.session_state.selected_proveedor_doc = None
                            st.session_state.show_edit_proveedor_dialog = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al cambiar estado: {str(e)}")

        # Función para manejar el clic en el botón "Editar"
        def on_edit_button_click(proveedor_doc):
            st.session_state.selected_proveedor_doc = proveedor_doc
            st.session_state.show_edit_proveedor_dialog = True
            st.rerun()

        # Mostrar proveedores activos
        if active_proveedores:
            # Encabezados de la tabla
            col_id_header, col_nombre_header, col_direccion_header, col_departamento_header, col_telefono_header, col_correo_header,col_activo_header, col_edit_header = st.columns([1, 2, 2, 1.5, 1,1, 0.5, 0.7])
            with col_id_header:
                st.markdown("**ID**")
            with col_nombre_header:
                st.markdown("**Nombre**")
            with col_direccion_header:
                st.markdown("**Dirección**")
            with col_departamento_header:
                st.markdown("**Departamento**")
            with col_telefono_header:
                st.markdown("**Teléfono**")
            with col_correo_header:
                st.markdown("**Correo**")
            with col_activo_header:
                st.markdown("**Activo**")
            with col_edit_header:
                st.markdown("**Acciones**")
            st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)

            for proveedor in active_proveedores:
                with st.container():
                    col_id, col_nombre, col_direccion, col_departamento, col_telefono, col_correo, col_activo, col_edit = st.columns([1, 2, 2, 1.5, 1, 1, 0.5, 0.7])
                    with col_id:
                        st.caption(proveedor.get('_id', 'N/A'))
                    with col_nombre:
                        st.write(proveedor.get('nombre', 'N/A'))
                    with col_direccion:
                        st.write(proveedor.get('direccion', 'N/A'))
                    with col_departamento:
                        st.write(proveedor.get('departamento', 'N/A'))
                    with col_telefono:
                        st.write(proveedor.get('telefono', 'N/A'))
                    with col_correo:
                        st.write(proveedor.get('correo', 'N/A'))
                    with col_activo:
                        st.checkbox("Activo", value=bool(proveedor.get('activo', 0)), disabled=True, key=f"activo_{proveedor.get('_id')}", label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"edit_btn_{proveedor.get('_id')}"):
                            on_edit_button_click(proveedor)
                    st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)
        else:
            st.info("No hay proveedores activos en la base de datos o no coinciden con el filtro.")

        # --- Sección de Proveedores Deshabilitados ---
        st.header("Proveedores Deshabilitados")

        if disabled_proveedores:
            # Encabezados de la tabla
            col_id_header_dis, col_nombre_header_dis, col_direccion_header_dis, col_departamento_header_dis, col_telefono_header_dis, col_correo_header_dis, col_activo_header_dis, col_edit_header_dis = st.columns([1, 2, 2, 1.5, 1, 1, 0.5, 0.7])
            with col_id_header_dis:
                st.markdown("**ID**")
            with col_nombre_header_dis:
                st.markdown("**Nombre**")
            with col_direccion_header_dis:
                st.markdown("**Dirección**")
            with col_departamento_header_dis:
                st.markdown("**Departamento**")
            with col_telefono_header_dis:
                st.markdown("**Teléfono**")
            with col_correo_header_dis:
                st.markdown("**Correo**")
            with col_activo_header_dis:
                st.markdown("**Activo**")
            with col_edit_header_dis:
                st.markdown("**Acciones**")
            st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)

            for proveedor in disabled_proveedores:
                with st.container():
                    col_id, col_nombre, col_direccion, col_departamento, col_telefono, col_correo, col_activo, col_edit = st.columns([1, 2, 2, 1.5, 1, 1, 0.5, 0.7])
                    with col_id:
                        st.caption(proveedor.get('_id', 'N/A'))
                    with col_nombre:
                        st.write(proveedor.get('nombre', 'N/A'))
                    with col_direccion:
                        st.write(proveedor.get('direccion', 'N/A'))
                    with col_departamento:
                        st.write(proveedor.get('departamento', 'N/A'))
                    with col_telefono:
                        st.write(proveedor.get('telefono', 'N/A'))
                    with col_correo:
                        st.write(proveedor.get('correo', 'N/A'))
                    with col_activo:
                        st.checkbox("Activo", value=bool(proveedor.get('activo', 0)), disabled=True, key=f"dis_activo_{proveedor.get('_id')}", label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"dis_edit_btn_{proveedor.get('_id')}"):
                            on_edit_button_click(proveedor)
                    st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)
        else:
            st.info("No hay proveedores deshabilitados en la base de datos o no coinciden con el filtro.")

    else:
        st.error("No se pudo conectar o configurar la base de datos. Revisa los mensajes de conexión.")