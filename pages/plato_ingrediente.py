# pages/plato_ingrediente.py
import streamlit as st
from datetime import datetime, timezone
import couchdb_utils
import os
import uuid
import pandas as pd

UNIDADES_CONVERSION = {
    "botella": {
        "shot": 24,
        "unidad": 1
    },
    "litro": {
        "shot": 36,
        "unidad": 1
    },
    "medio litro": {
        "shot": 18,
        "unidad": 1
    }
}
# Obtener la ruta relativa de la página
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = "plato_ingrediente"

# Llama a la función de login/menú/validación
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Relación Plato-Ingrediente", page_icon="../assets/LOGO.png")

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
        # Obtener datos necesarios
        def get_platos_activos():
            platos = couchdb_utils.get_documents_by_partition(db, "platos")
            return [p for p in platos if p.get('activo', 0) == 1]

        def get_ingredientes_activos():
            ingredientes = couchdb_utils.get_documents_by_partition(db, "ingredientes")
            return [i for i in ingredientes if i.get('activo', 0) == 1]

        def get_plato_ingredientes():
            return couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)

        # Inicializar estado de la sesión
        if 'plato_seleccionado' not in st.session_state:
            st.session_state.plato_seleccionado = None
        # if 'ingredientes_agregados' not in st.session_state:
        #     st.session_state.ingredientes_agregados = pd.DataFrame(columns=['Ingrediente ID', 'Descripción', 'Cantidad', 'Unidad'])
        if 'ingredientes_agregados' not in st.session_state:
            st.session_state.ingredientes_agregados = pd.DataFrame(columns=[
                'Ingrediente ID', 
                'Descripción', 
                'Cantidad', 
                'Unidad',
                'CantidadShots',
                'Seleccionar' 
            ])

        # --- Sección de Crear/Editar Relación Plato-Ingrediente ---
        st.header("Relacionar Plato con Ingredientes")

        # Selección de plato
        platos = get_platos_activos()
        plato_options = {p['_id']: p.get('descripcion', 'Sin descripción') for p in platos}
        
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_plato_id = st.selectbox(
                "Seleccionar Plato:",
                options=list(plato_options.keys()),
                format_func=lambda x: plato_options[x],
                key="select_plato"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Cargar Plato", key="btn_cargar_plato"):
                st.session_state.plato_seleccionado = selected_plato_id
                # Cargar ingredientes existentes si los hay
                relaciones = get_plato_ingredientes()
                ingredientes_existentes = [r for r in relaciones if r.get('plato_id') == selected_plato_id]
                
               
                
                if ingredientes_existentes:
                    data = []
                    for rel in ingredientes_existentes:
                        ingrediente = next((i for i in get_ingredientes_activos() if i['_id'] == rel.get('ingrediente_id')), None)
                        if ingrediente:
                            data.append({
                                'Ingrediente ID': rel.get('ingrediente_id'),
                                'Descripción': ingrediente.get('descripcion', 'Sin descripción'),
                                'Cantidad': rel.get('cantidad', 0),
                                'Unidad': ingrediente.get('unidad', 'unidad'),
                                'CantidadShots': None,  # Add this if needed
                                'Seleccionar': False  # Add default value
                            })
                    st.session_state.ingredientes_agregados = pd.DataFrame(data)
                else:
                    st.session_state.ingredientes_agregados = pd.DataFrame(columns=[
                        'Ingrediente ID', 
                        'Descripción', 
                        'Cantidad', 
                        'Unidad',
                        'CantidadShots',
                        'Seleccionar'
                    ])
                st.rerun()

        # Mostrar información del plato seleccionado
        if st.session_state.plato_seleccionado:
            plato_seleccionado = next((p for p in platos if p['_id'] == st.session_state.plato_seleccionado), None)
            if plato_seleccionado:
                st.subheader(f"Plato: {plato_seleccionado.get('descripcion', 'N/A')}")
                
                # Selección de ingredientes para agregar
                ingredientes = get_ingredientes_activos()
                ingredientes_disponibles = [i for i in ingredientes if i['_id'] not in st.session_state.ingredientes_agregados['Ingrediente ID'].values]
                
                col3, col4, col5, col6 = st.columns([2, 2, 1, 1])
                with col3:
                    selected_ingrediente_id = st.selectbox(
                        "Seleccionar Ingrediente:",
                        options=[i['_id'] for i in ingredientes_disponibles],
                        format_func=lambda x: next((i.get('descripcion', 'Sin descripción') for i in ingredientes if i['_id'] == x), ''),
                        key="select_ingrediente"
                    )
                # with col4:
                #     cantidad_ingrediente = st.number_input("Cantidad:", min_value=1, step=1,  key="cantidad_ingrediente") #format="%.2f",
                with col4:
                    ingrediente_seleccionado = next((i for i in ingredientes if i['_id'] == selected_ingrediente_id), None)
                    unidad_ingrediente = ingrediente_seleccionado.get('unidad', 'unidad') if ingrediente_seleccionado else 'unidad'
                    
                    if unidad_ingrediente in UNIDADES_CONVERSION:
                        # Mostrar opción de unidad de consumo
                        opcion_unidad = st.radio(
                            "Unidad de consumo:",
                            options=["Usar unidad completa", "Usar shots"],
                            horizontal=True,
                            key=f"unidad_opcion_{selected_ingrediente_id}"
                        )
                        
                        if opcion_unidad == "Usar shots":
                            cantidad_ingrediente = st.number_input(
                                "Cantidad (shots):",
                                min_value=1,
                                step=1,
                                key=f"cantidad_shots_{selected_ingrediente_id}"
                            )
                            # Convertir shots a la unidad original
                            cantidad_unidad_original = cantidad_ingrediente / UNIDADES_CONVERSION[unidad_ingrediente]["shot"]
                        else:
                            cantidad_ingrediente = st.number_input(
                                "Cantidad:",
                                min_value=1,
                                step=1,
                                # format="%.2f",
                                key=f"cantidad_{selected_ingrediente_id}"
                            )
                            cantidad_unidad_original = cantidad_ingrediente
                    else:
                        cantidad_ingrediente = st.number_input(
                            "Cantidad:",
                            min_value=1,
                            step=1,
                            # format="%.2f",
                            key=f"cantidad_{selected_ingrediente_id}"
                        )
                        cantidad_unidad_original = cantidad_ingrediente

                with col5:
                    st.markdown("<br>", unsafe_allow_html=True)
                   
                    if st.button("Agregar Ingrediente", key="btn_agregar_ingrediente"):
                        ingrediente = next((i for i in ingredientes if i['_id'] == selected_ingrediente_id), None)
                        if ingrediente:
                            # Definir valores por defecto para ingredientes no convertibles
                            cantidad_shots = None
                            cantidad_unidad_original = cantidad_ingrediente
                            
                            # Solo para unidades convertibles
                            if ingrediente.get('unidad') in UNIDADES_CONVERSION:
                                # Verificar si opcion_unidad está definida (puede no estarlo en algunos casos)
                                opcion_unidad = st.session_state.get(f"unidad_opcion_{selected_ingrediente_id}", "Usar unidad completa")
                                if opcion_unidad == "Usar shots":
                                    cantidad_shots = cantidad_ingrediente
                                    cantidad_unidad_original = cantidad_ingrediente / UNIDADES_CONVERSION[ingrediente['unidad']]["shot"]
                            
                           
                            nuevo_ingrediente = {
                                'Ingrediente ID': selected_ingrediente_id,
                                'Descripción': ingrediente.get('descripcion', 'Sin descripción'),
                                'Cantidad': cantidad_unidad_original,
                                'Unidad': ingrediente.get('unidad', 'unidad'),
                                'CantidadShots': cantidad_shots , # Será None para unidades no convertibles
                                'Seleccionar': False
                            }
                            
                            st.session_state.ingredientes_agregados = pd.concat([
                                st.session_state.ingredientes_agregados,
                                pd.DataFrame([nuevo_ingrediente])
                            ], ignore_index=True)
                            st.rerun()

                with col6:
                    st.markdown("<br>", unsafe_allow_html=True)
                    # if st.button("Limpiar Todo", key="btn_limpiar_todo"):
                    #     st.session_state.ingredientes_agregados = pd.DataFrame(columns=['Ingrediente ID', 'Descripción', 'Cantidad', 'Unidad'])
                    #     st.rerun()
                    if st.button("Limpiar Todo", key="btn_limpiar_todo"):
                        st.session_state.ingredientes_agregados = pd.DataFrame(columns=[
                            'Ingrediente ID', 
                            'Descripción', 
                            'Cantidad', 
                            'Unidad',
                            'CantidadShots',
                            'Seleccionar'
                        ])
                        st.rerun()
                if not st.session_state.ingredientes_agregados.empty:
                    st.subheader("Ingredientes del Plato")
                    
                    # Preparar datos para mostrar
                    display_df = st.session_state.ingredientes_agregados.copy()
                    display_df['Cantidad a Descontar'] = display_df.apply(
                        lambda row: f"{row['CantidadShots']} shots" if pd.notnull(row['CantidadShots']) 
                                    else f"{row['Cantidad']:.2f} {row['Unidad']}",
                        axis=1
                    )
                    
                    # Mostrar tabla editable
                    edited_df = st.data_editor(
                        st.session_state.ingredientes_agregados,
                        key="ingredientes_editor",
                        num_rows="fixed",
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Ingrediente ID": None,
                            "Descripción": st.column_config.TextColumn("Descripción", disabled=True),
                            "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.01, step=0.01, format="%.2f"),
                            "Unidad": st.column_config.TextColumn("Unidad", disabled=True),
                            "CantidadShots": None,  # Ocultar esta columna
                            "Seleccionar": st.column_config.CheckboxColumn("Seleccionar", default=False, required=True)
                        },
                        disabled=["Ingrediente ID", "Descripción", "Unidad", "CantidadShots"],
                        column_order=["Seleccionar", "Descripción", "Cantidad", "Unidad"]
                    )
                    if edited_df is not None:
                        st.session_state.ingredientes_agregados = edited_df.copy()

                    # Botones para eliminar y guardar
                    col7, col8, col9 = st.columns([1, 1, 2])
                    with col7:
                        if st.button("Eliminar Seleccionados", type="primary", key="btn_eliminar_seleccionados"):
                            if st.session_state.ingredientes_agregados.empty:
                                st.warning("No hay ingredientes para eliminar")
                            else:
                                # Usar el DataFrame editado directamente
                                df = st.session_state.ingredientes_agregados
                                # Filtrar solo las filas donde "Seleccionar" es True
                                selected_rows = df[df['Seleccionar'] == True]
                                
                                if not selected_rows.empty:
                                    # Eliminar las filas seleccionadas
                                    st.session_state.ingredientes_agregados = df[df['Seleccionar'] == False].reset_index(drop=True)
                                    st.success(f"Se eliminaron {len(selected_rows)} ingrediente(s)")
                                    st.rerun()
                                else:
                                    st.warning("Por favor seleccione al menos un ingrediente marcando la casilla correspondiente")
                    # with col7:
                    #     if st.button("Eliminar Seleccionados", type="primary", key="btn_eliminar_seleccionados"):
                    #         if st.session_state.ingredientes_agregados.empty:
                    #             st.warning("No hay ingredientes para eliminar")
                    #         else:
                    #             # Obtener filas seleccionadas directamente del session_state
                    #             df = st.session_state.ingredientes_agregados
                    #             filas_a_eliminar = df[df.get("Seleccionar", False)].index.tolist() if "Seleccionar" in df.columns else []
                                
                    #             if filas_a_eliminar:
                    #                 st.session_state.ingredientes_agregados = df.drop(filas_a_eliminar).reset_index(drop=True)
                    #                 st.success(f"Se eliminaron {len(filas_a_eliminar)} ingrediente(s)")
                    #                 st.rerun()
                    #             else:
                    #                 st.warning("Por favor seleccione al menos un ingrediente marcando la casilla correspondiente")
                   
                   
                   
                   
                    # Modificar la sección del botón "Guardar Relación" así:
                    with col8:
                        if st.button("Guardar Relación", type="primary", key="btn_guardar_relacion"):
                            # Verificar que tenemos datos válidos
                            if st.session_state.ingredientes_agregados.empty:
                                st.error("No hay ingredientes para guardar")
                            else:
                                try:
                                    # Eliminar relaciones existentes para este plato
                                    relaciones_existentes = [r for r in get_plato_ingredientes() if r.get('plato_id') == st.session_state.plato_seleccionado]
                                    for rel in relaciones_existentes:
                                        try:
                                            db.delete(rel)
                                        except Exception as e:
                                            st.error(f"Error al eliminar relación existente: {str(e)}")
                                            continue

                                    # Crear nuevas relaciones
                                    success = True
                                    for _, row in st.session_state.ingredientes_agregados.iterrows():
                                        try:
                                            # Verificar que tenemos todos los campos necesarios
                                            required_fields = ['Ingrediente ID', 'Descripción', 'Cantidad', 'Unidad']
                                            if not all(field in row for field in required_fields):
                                                st.error(f"Faltan campos requeridos en la fila: {row}")
                                                success = False
                                                continue

                                            nueva_relacion = {
                                                "_id": f"{CURRENT_PARTITION_KEY}:{str(uuid.uuid4())}",
                                                "plato_id": st.session_state.plato_seleccionado,
                                                "plato_descripcion": plato_seleccionado.get('descripcion', 'N/A'),
                                                "ingrediente_id": str(row['Ingrediente ID']),  # Asegurar que es string
                                                "ingrediente_descripcion": str(row['Descripción']),
                                                "cantidad": float(row['Cantidad']),
                                                "unidad": str(row['Unidad']),
                                                "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                                                "type": CURRENT_PARTITION_KEY
                                            }
                                            db.save(nueva_relacion)
                                        except Exception as e:
                                            st.error(f"Error al guardar relación para ingrediente {row.get('Ingrediente ID', 'N/A')}: {str(e)}")
                                            success = False

                                    if success:
                                        st.success("Relación plato-ingrediente guardada exitosamente!")
                                        
                                        # LOGGING
                                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                        couchdb_utils.log_action(
                                            db, 
                                            logged_in_user, 
                                            f"Relación plato-ingrediente actualizada para {plato_seleccionado.get('descripcion', 'N/A')} con {len(st.session_state.ingredientes_agregados)} ingredientes"
                                        )
                                         # Limpiar el estado y refrescar
                                        st.session_state.plato_seleccionado = None
                                        st.session_state.ingredientes_agregados = pd.DataFrame(columns=[
                                            'Ingrediente ID', 
                                            'Descripción', 
                                            'Cantidad', 
                                            'Unidad',
                                            'CantidadShots',
                                            'Seleccionar'
                                        ])
                                        st.rerun() 
                                    # st.rerun()
                                except Exception as e:
                                    st.error(f"Error general al guardar: {str(e)}")
                    with col9:
                        if st.button("Cancelar", key="btn_cancelar"):
                            st.session_state.plato_seleccionado = None
                            st.session_state.ingredientes_agregados = pd.DataFrame(columns=[
                                'Ingrediente ID', 
                                'Descripción', 
                                'Cantidad', 
                                'Unidad',
                                'CantidadShots',
                                'Seleccionar'
                            ])
                            st.rerun()
        
        # --- Sección de Consulta de Relaciones ---
        st.header("Consultar Relaciones Plato-Ingrediente")

        # Filtro por plato
        plato_consulta_id = st.selectbox(
            "Seleccionar Plato para Consultar:",
            options=[""] + list(plato_options.keys()),
            format_func=lambda x: "Seleccione un plato" if x == "" else plato_options[x],
            key="select_plato_consulta"
        )

        if plato_consulta_id:
            relaciones = get_plato_ingredientes()
            ingredientes_plato = [r for r in relaciones if r.get('plato_id') == plato_consulta_id]
            
            if ingredientes_plato:
                plato_descripcion = next((p.get('descripcion', 'N/A') for p in platos if p['_id'] == plato_consulta_id), 'N/A')
                st.subheader(f"Ingredientes para: {plato_descripcion}")
                
                # Crear DataFrame para mostrar
                data = []
                for rel in ingredientes_plato:
                    # Determinar qué mostrar según la unidad
                    unidad = rel.get('unidad', 'unidad')
                    cantidad = rel.get('cantidad', 0)
                    
                    if unidad in UNIDADES_CONVERSION:
                        # Calcular shots si es unidad convertible
                        shots = cantidad * UNIDADES_CONVERSION[unidad]['shot']
                        display_text = f"{cantidad:.3f} {unidad} ({shots:.0f} shots)"
                    else:
                        display_text = f"{cantidad:.2f} {unidad}"
                    
                    data.append({
                        'Ingrediente': rel.get('ingrediente_descripcion', 'N/A'),
                        'Cantidad': display_text,
                        'Tipo': 'Convertible' if unidad in UNIDADES_CONVERSION else 'Normal'
                    })
                
                df_consulta = pd.DataFrame(data)
                
                # Mostrar tabla
                st.dataframe(
                    df_consulta[['Ingrediente', 'Cantidad']],  # Solo mostrar columnas relevantes
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Ingrediente': st.column_config.TextColumn("Ingrediente"),
                        'Cantidad': st.column_config.TextColumn("Cantidad"),
                    }
                )
                
                # Botón para cargar esta relación en el editor
                if st.button("Cargar para Editar", key="btn_cargar_para_editar"):
                    st.session_state.plato_seleccionado = plato_consulta_id
                    
                   
                    edit_data = []
                    for rel in ingredientes_plato:
                        ingrediente_info = {
                            'Ingrediente ID': rel.get('ingrediente_id'),
                            'Descripción': rel.get('ingrediente_descripcion', 'N/A'),
                            'Cantidad': rel.get('cantidad', 0),
                            'Unidad': rel.get('unidad', 'unidad'),
                            'Seleccionar': False  # Add default value
                        }
                        
                        # Calcular CantidadShots solo si es unidad convertible
                        unidad = rel.get('unidad', '')
                        if unidad in UNIDADES_CONVERSION:
                            factor_conversion = UNIDADES_CONVERSION[unidad].get('shot', 1)
                            ingrediente_info['CantidadShots'] = float(rel.get('cantidad', 0)) * factor_conversion
                        else:
                            ingrediente_info['CantidadShots'] = None
                        
                        edit_data.append(ingrediente_info)

                    
                    st.session_state.ingredientes_agregados = pd.DataFrame(edit_data)
                    st.rerun()
               
            else:
                st.info("Este plato no tiene ingredientes asociados")
        

    else:
        st.error("No se pudo conectar o configurar la base de datos. Revisa los mensajes de conexión.")