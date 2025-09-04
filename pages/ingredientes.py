# pages/ingredientes.py
import streamlit as st
import json
from datetime import datetime, timezone
import couchdb_utils
import os
import pandas as pd
import uuid

# Agregar al inicio del archivo, después de los imports
UNIDAD_CONVERSION = {
    "botella": {
        "shot": 24,  # 1 botella = 24 shots
        "unidad": 1   # 1 botella = 1 unidad (para mantener compatibilidad)
    },
    "litro": {
        "shot": 36,   # 1 litro = 36 shots
        "unidad": 1    # 1 litro = 1 unidad
    },
    "medio litro": {
        "shot": 18,    # 0.5 litro = 18 shots
        "unidad": 1     # 0.5 litro = 1 unidad
    },
    # "shot": {
    #     "shot": 1,      # 1 shot = 1 shot
    #     "unidad": 1/24  # 1 shot = 1/24 de botella
    # },
    # "unidad": {
    #     "shot": 1,      # Para compatibilidad
    #     "unidad": 1
    # }
}

# Obtener la ruta relativa de la página
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = "ingredientes"

# Llama a la función de login/menú/validación
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Gestión de Ingredientes", page_icon="../assets/LOGO.png")

# --- CSS EXTERNO ---
css_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'style.css')
if os.path.exists(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning(f"Archivo CSS no encontrado en: {css_file_path}")

def convertir_a_shots(cantidad, unidad_origen):
    """
    Convierte a shots solo si la unidad está en la tabla de conversión
    
    Args:
        cantidad: cantidad a convertir
        unidad_origen: unidad original (solo convierte "botella", "litro", "medio litro")
    
    Returns:
        float: cantidad en shots (o None si no aplica conversión)
    """
    if unidad_origen in UNIDAD_CONVERSION:
        return cantidad * UNIDAD_CONVERSION[unidad_origen]["shot"]
    return None  # No hay conversión para esta unidad

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()

    if db:
        # --- Sección de Crear Nuevo Ingrediente ---
        st.header("Crear Nuevo Ingrediente")
        
        # Usamos st.expander como alternativa al diálogo
        with st.expander("➕ Crear Nuevo Ingrediente", expanded=False):
            with st.form("new_ingrediente_form", clear_on_submit=True):
                new_ingrediente_descripcion = st.text_input("Descripción:", key="new_ingrediente_descripcion").strip()
                
                # Nuevo campo: Cantidad
                new_ingrediente_cantidad = st.number_input(
                    "Cantidad en inventario:", 
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key="new_ingrediente_cantidad"
                )
                
                
                # unidad_options = ["botella", "litro", "medio litro", "shot", "unidad"]
                # new_ingrediente_unidad = st.selectbox(
                #     "Unidad de Medida:", 
                #     options=unidad_options,
                #     key="new_ingrediente_unidad"
                # )

                # # Agregar campo para mostrar la equivalencia en shots
                # if new_ingrediente_unidad in UNIDAD_CONVERSION:
                #     shots_equivalent = new_ingrediente_cantidad * UNIDAD_CONVERSION[new_ingrediente_unidad]["shot"]
                #     st.caption(f"Equivalente a: {shots_equivalent:.2f} shots")
                unidad_options = ["unidad", "botella", "litro", "medio litro"]  # "unidad" primero como default

                new_ingrediente_unidad = st.selectbox(
                    "Unidad de Medida:", 
                    options=unidad_options,
                    key="new_ingrediente_unidad"
                )

                # Mostrar equivalencia solo para las unidades con conversión
                if new_ingrediente_unidad in UNIDAD_CONVERSION:
                    shots_equivalent = new_ingrediente_cantidad * UNIDAD_CONVERSION[new_ingrediente_unidad]["shot"]
                    st.caption(f"Equivalente a: {shots_equivalent:.2f} shots")
                
                new_ingrediente_imagen = st.text_input("URL Imagen (opcional):", value="", key="new_ingrediente_imagen")
                new_ingrediente_activo = st.checkbox("Activo", value=True, key="new_ingrediente_activo")
                
                st.markdown("---")
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit_button = st.form_submit_button("Guardar Nuevo Ingrediente", type="primary")
                with col_cancel:
                    cancel_button = st.form_submit_button("Cancelar")

                if submit_button:
                    if not new_ingrediente_descripcion:
                        st.error("La descripción es obligatoria.")
                    else:
                        # Generamos un ID único con el formato correcto para particiones
                        doc_id = f"{CURRENT_PARTITION_KEY}:{str(uuid.uuid4())}"
                        
                        new_ingrediente_doc = {
                            "_id": doc_id,
                            "descripcion": new_ingrediente_descripcion,
                            "cantidad": float(new_ingrediente_cantidad),
                            "unidad": new_ingrediente_unidad,
                            "imagen": new_ingrediente_imagen,
                            "activo": 1 if new_ingrediente_activo else 0,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                            "type": CURRENT_PARTITION_KEY
                        }
                        try:
                            db.save(new_ingrediente_doc)
                            st.success(f"Ingrediente '{new_ingrediente_descripcion}' creado exitosamente.")
                            
                            # LOGGING
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Ingrediente '{new_ingrediente_descripcion}' agregado satisfactoriamente.")
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear ingrediente: {str(e)}")
                
                if cancel_button:
                    st.rerun()

        # --- Sección de Ver Ingredientes Activos ---
        st.header("Lista de Ingredientes Activos")

        if 'selected_ingrediente_doc' not in st.session_state: 
            st.session_state.selected_ingrediente_doc = None

        col_filter_desc, col_refresh_btn = st.columns([2, 1])
        with col_filter_desc:
            filter_desc = st.text_input("Filtrar por Descripción:", help="Escribe parte de la descripción para filtrar.", key="filter_ingrediente_desc").strip().lower()
        with col_refresh_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualizar Lista de Ingredientes", key="refresh_ingrediente_table_btn"):
                st.session_state.selected_ingrediente_doc = None
                st.rerun()

        all_ingredientes_raw = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
        
        active_ingredientes = [
            item for item in all_ingredientes_raw 
            if item.get('activo', 0) == 1 
            and (not filter_desc or filter_desc in item.get('descripcion', '').lower())
        ]
        
        disabled_ingredientes = [
            item for item in all_ingredientes_raw 
            if item.get('activo', 0) == 0 
            and (not filter_desc or filter_desc in item.get('descripcion', '').lower())
        ]

        # --- Función para editar ingrediente ---
        if 'show_edit_ingrediente_dialog' not in st.session_state:
            st.session_state.show_edit_ingrediente_dialog = False

        if st.session_state.show_edit_ingrediente_dialog:
            ingrediente_to_edit = st.session_state.selected_ingrediente_doc.copy()
            
            with st.expander(f"✏️ Editando: {ingrediente_to_edit.get('descripcion', 'N/A')}", expanded=True):
                with st.form("edit_ingrediente_form"):
                    st.caption(f"ID: `{ingrediente_to_edit.get('_id', 'N/A')}`")
                    st.caption(f"Revisión: `{ingrediente_to_edit.get('_rev', 'N/A')}`")

                    edited_descripcion = st.text_input("Descripción:", value=ingrediente_to_edit.get("descripcion", ""), key="edit_ingrediente_descripcion")
                    
                    edited_cantidad = st.number_input(
                        "Cantidad en inventario:", 
                        min_value=0.0,
                        step=0.1,
                        format="%.2f",
                        value=float(ingrediente_to_edit.get("cantidad", 0.0)),
                        key="edit_ingrediente_cantidad"
                    )
                    
                    unidad_options = ["unidad", "botella", "litro", "medio litro"]
                    current_unidad_index = unidad_options.index(ingrediente_to_edit.get("unidad", "unidad")) if ingrediente_to_edit.get("unidad", "unidad") in unidad_options else 0
                    edited_unidad = st.selectbox(
                        "Unidad de Medida:", 
                        options=unidad_options,
                        index=current_unidad_index,
                        key="edit_ingrediente_unidad"
                    )
                    
                    edited_imagen = st.text_input("URL Imagen (opcional):", value=ingrediente_to_edit.get("imagen", ""), key="edit_ingrediente_imagen")
                    edited_activo = st.checkbox("Activo", value=bool(ingrediente_to_edit.get("activo", 0)), key="edit_ingrediente_activo")
                    
                    st.markdown("---")
                    col_submit, col_cancel, col_toggle_active = st.columns(3)
                    
                    with col_submit:
                        save_button = st.form_submit_button("Guardar Cambios", type="primary")
                    with col_cancel:
                        cancel_button = st.form_submit_button("Cancelar")
                    with col_toggle_active:
                        toggle_active_label = "🚫 Deshabilitar" if bool(ingrediente_to_edit.get("activo", 0)) else "✅ Habilitar"
                        toggle_active_button = st.form_submit_button(toggle_active_label)

                    if save_button:
                        updated_doc = {
                            "_id": ingrediente_to_edit["_id"],
                            "_rev": ingrediente_to_edit["_rev"],
                            "descripcion": edited_descripcion,
                            "cantidad": float(edited_cantidad),
                            "unidad": edited_unidad,
                            "imagen": edited_imagen,
                            "activo": 1 if edited_activo else 0,
                            "fecha_creacion": ingrediente_to_edit.get("fecha_creacion"),
                            "type": CURRENT_PARTITION_KEY
                        }
                        
                        try:
                            db.save(updated_doc)
                            st.success(f"Ingrediente '{edited_descripcion}' actualizado exitosamente.")
                            
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Ingrediente '{edited_descripcion}' actualizado satisfactoriamente.")

                            st.session_state.selected_ingrediente_doc = None
                            st.session_state.show_edit_ingrediente_dialog = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar los cambios: {str(e)}")
                    
                    if cancel_button:
                        st.session_state.selected_ingrediente_doc = None
                        st.session_state.show_edit_ingrediente_dialog = False
                        st.rerun()

                    if toggle_active_button:
                        toggled_doc = {
                            "_id": ingrediente_to_edit["_id"],
                            "_rev": ingrediente_to_edit["_rev"],
                            "descripcion": ingrediente_to_edit["descripcion"],
                            "cantidad": ingrediente_to_edit.get("cantidad", 0.0),
                            "unidad": ingrediente_to_edit["unidad"],
                            "imagen": ingrediente_to_edit.get("imagen", ""),
                            "activo": 0 if bool(ingrediente_to_edit.get("activo", 0)) else 1,
                            "fecha_creacion": ingrediente_to_edit.get("fecha_creacion"),
                            "type": CURRENT_PARTITION_KEY
                        }
                        
                        try:
                            db.save(toggled_doc)
                            status_text = "deshabilitado" if toggled_doc["activo"] == 0 else "habilitado"
                            st.success(f"Ingrediente '{toggled_doc['descripcion']}' {status_text} exitosamente.")
                            
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Ingrediente '{toggled_doc['descripcion']}' {status_text} satisfactoriamente.")

                            st.session_state.selected_ingrediente_doc = None
                            st.session_state.show_edit_ingrediente_dialog = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al cambiar estado: {str(e)}")

        # Función para manejar el clic en el botón "Editar"
        def on_edit_button_click(ingrediente_doc):
            st.session_state.selected_ingrediente_doc = ingrediente_doc
            st.session_state.show_edit_ingrediente_dialog = True
            st.rerun()

        # Mostrar ingredientes activos
        if active_ingredientes:
            # Encabezados de la tabla (actualizados con el nuevo campo)
            col_id_header, col_desc_header, col_cantidad_header, col_unidad_header, col_imagen_header, col_activo_header, col_edit_header = st.columns([1, 2, 1, 1, 1, 0.5, 0.7])
            with col_id_header:
                st.markdown("**ID**")
            with col_desc_header:
                st.markdown("**Descripción**")
            with col_cantidad_header:
                st.markdown("**Cantidad**")
            with col_unidad_header:
                st.markdown("**Unidad**")
            with col_imagen_header:
                st.markdown("**Imagen**")
            with col_activo_header:
                st.markdown("**Activo**")
            with col_edit_header:
                st.markdown("**Acciones**")
            st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)

            for ingrediente in active_ingredientes:
                with st.container():
                    col_id, col_desc, col_cantidad, col_unidad, col_imagen, col_activo, col_edit = st.columns([1, 2, 1, 1, 1, 0.5, 0.7])
                    with col_id:
                        st.caption(ingrediente.get('_id', 'N/A'))
                    with col_desc:
                        st.write(ingrediente.get('descripcion', 'N/A'))
                    # with col_cantidad:
                    #     st.write(f"{ingrediente.get('cantidad', 0.0):.2f}")
                    with col_cantidad:
                        st.write(f"{ingrediente.get('cantidad', 0.0):.2f} {ingrediente.get('unidad', '')}")
                        # Mostrar conversión solo si aplica
                        if ingrediente.get('unidad') in UNIDAD_CONVERSION:
                            shots = convertir_a_shots(ingrediente.get('cantidad', 0.0), ingrediente.get('unidad', ''))
                            st.caption(f"({shots:.2f} shots)")
                    with col_unidad:
                        st.write(ingrediente.get('unidad', 'N/A'))
                    with col_imagen:
                        if ingrediente.get('imagen'):
                            st.image(ingrediente['imagen'], width=50, use_column_width="always")
                        else:
                            st.write("N/A")
                    with col_activo:
                        st.checkbox("Activo", value=bool(ingrediente.get('activo', 0)), disabled=True, key=f"activo_{ingrediente.get('_id')}", label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"edit_btn_{ingrediente.get('_id')}"):
                            on_edit_button_click(ingrediente)
                    st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)
        else:
            st.info("No hay ingredientes activos en la base de datos o no coinciden con el filtro.")

        # --- Sección de Ingredientes Deshabilitados ---
        st.header("Ingredientes Deshabilitados")

        if disabled_ingredientes:
            # Encabezados de la tabla (actualizados con el nuevo campo)
            col_id_header_dis, col_desc_header_dis, col_cantidad_header_dis, col_unidad_header_dis, col_imagen_header_dis, col_activo_header_dis, col_edit_header_dis = st.columns([1, 2, 1, 1, 1, 0.5, 0.7])
            with col_id_header_dis:
                st.markdown("**ID**")
            with col_desc_header_dis:
                st.markdown("**Descripción**")
            with col_cantidad_header_dis:
                st.markdown("**Cantidad**")
            with col_unidad_header_dis:
                st.markdown("**Unidad**")
            with col_imagen_header_dis:
                st.markdown("**Imagen**")
            with col_activo_header_dis:
                st.markdown("**Activo**")
            with col_edit_header_dis:
                st.markdown("**Acciones**")
            st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)

            for ingrediente in disabled_ingredientes:
                with st.container():
                    col_id, col_desc, col_cantidad, col_unidad, col_imagen, col_activo, col_edit = st.columns([1, 2, 1, 1, 1, 0.5, 0.7])
                    with col_id:
                        st.caption(ingrediente.get('_id', 'N/A'))
                    with col_desc:
                        st.write(ingrediente.get('descripcion', 'N/A'))
                    # with col_cantidad:
                    #     st.write(f"{ingrediente.get('cantidad', 0.0):.2f}")
                    with col_cantidad:
                        st.write(f"{ingrediente.get('cantidad', 0.0):.2f} {ingrediente.get('unidad', '')}")
                        # Mostrar conversión solo si aplica
                        if ingrediente.get('unidad') in UNIDAD_CONVERSION:
                            shots = convertir_a_shots(ingrediente.get('cantidad', 0.0), ingrediente.get('unidad', ''))
                            st.caption(f"({shots:.2f} shots)")
                    with col_unidad:
                        st.write(ingrediente.get('unidad', 'N/A'))
                    with col_imagen:
                        if ingrediente.get('imagen'):
                            st.image(ingrediente['imagen'], width=50, use_column_width="always")
                        else:
                            st.write("N/A")
                    with col_activo:
                        st.checkbox("Activo", value=bool(ingrediente.get('activo', 0)), disabled=True, key=f"dis_activo_{ingrediente.get('_id')}", label_visibility="collapsed")
                    with col_edit:
                        if st.button("Editar", key=f"dis_edit_btn_{ingrediente.get('_id')}"):
                            on_edit_button_click(ingrediente)
                    st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)
        else:
            st.info("No hay ingredientes deshabilitados en la base de datos o no coinciden con el filtro.")

    else:
        st.error("No se pudo conectar o configurar la base de datos. Revisa los mensajes de conexión.")