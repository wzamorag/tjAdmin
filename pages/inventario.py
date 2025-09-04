# pages/inventario.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone
import pandas as pd
import uuid

# Configuración básica
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
CURRENT_PARTITION_KEY = "inventario"
couchdb_utils.generarLogin(archivo_actual_relativo)
st.set_page_config(layout="wide", page_title="Gestión de Inventario", page_icon="../assets/LOGO.png")

# Estilos CSS
st.markdown("""
<style>
    .card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .positive {
        color: green;
        font-weight: bold;
    }
    .negative {
        color: red;
        font-weight: bold;
    }
    .table-header {
        background-color: #2c3e50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # --- Funciones auxiliares ---
        def get_ingredientes_activos():
            ingredientes = couchdb_utils.get_documents_by_partition(db, "ingredientes")
            return [i for i in ingredientes if i.get('activo', 0) == 1]
        
        def get_movimientos_inventario():
            return couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
        
        def get_stock_actual(ingrediente_id):
            movimientos = get_movimientos_inventario()
            stock = 0
            for mov in movimientos:
                if mov.get('ingrediente_id') == ingrediente_id:
                    stock += mov.get('cantidad', 0)
            return stock
        
        # --- Sección de Entradas/Salidas ---
        st.title("📦 Gestión de Inventario")
        st.markdown("---")
        
        # Pestañas para diferentes operaciones
        tab1, tab2, tab3 = st.tabs(["Movimientos", "Registrar Entrada", "Registrar Salida"])
        
        with tab1:
            # --- Visualización de Movimientos ---
            st.subheader("Historial de Movimientos")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                ingredientes = get_ingredientes_activos()
                ingrediente_options = {i['_id']: i.get('descripcion', 'Sin descripción') for i in ingredientes}
                ingrediente_filtro = st.selectbox(
                    "Filtrar por ingrediente:",
                    options=["Todos"] + list(ingrediente_options.keys()),
                    format_func=lambda x: "Todos" if x == "Todos" else ingrediente_options[x]
                )
            
            with col2:
                tipo_filtro = st.selectbox(
                    "Filtrar por tipo:",
                    options=["Todos", "entrada", "salida"]
                )
            
            # Obtener movimientos filtrados
            movimientos = get_movimientos_inventario()
            if ingrediente_filtro != "Todos":
                movimientos = [m for m in movimientos if m.get('ingrediente_id') == ingrediente_filtro]
            if tipo_filtro != "Todos":
                movimientos = [m for m in movimientos if m.get('tipo') == tipo_filtro]
            
            # Mostrar tabla de movimientos
            if movimientos:
                data = []
                for mov in movimientos:
                    # Para movimientos de ingredientes
                    if mov.get('ingrediente_id'):
                        ingrediente = next((i for i in ingredientes if i['_id'] == mov.get('ingrediente_id')), None)
                        item_name = ingrediente.get('descripcion', 'N/A') if ingrediente else 'N/A'
                        unidad = ingrediente.get('unidad', 'unidad') if ingrediente else 'unidad'
                    # Para movimientos de platos (ventas)
                    elif mov.get('plato_id'):
                        item_name = mov.get('plato_nombre', 'Plato desconocido')
                        unidad = 'plato'
                    else:
                        item_name = 'N/A'
                        unidad = 'unidad'
                    
                    data.append({
                        'Fecha': mov.get('fecha_creacion', 'N/A'),
                        'Item': item_name,
                        'Tipo': mov.get('tipo', 'N/A'),
                        'Cantidad': mov.get('cantidad', 0),
                        'Unidad': unidad,
                        'Responsable': mov.get('usuario', 'N/A'),
                        'Comentarios': mov.get('comentarios', mov.get('motivo', ''))
                    })
                
                df = pd.DataFrame(data)
                # Ordenar por fecha de forma descendente (más reciente primero)
                df['Fecha'] = pd.to_datetime(df['Fecha'], utc=True)  # Interpretar como UTC
                df = df.sort_values('Fecha', ascending=False)
                # Convertir a hora local y formatear para mejor visualización
                df['Fecha'] = df['Fecha'].dt.tz_convert('America/El_Salvador').dt.strftime('%Y-%m-%d %H:%M:%S')
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "Cantidad": st.column_config.NumberColumn(
                            "Cantidad",
                            format="%.2f",
                            help="Valor positivo para entradas, negativo para salidas"
                        )
                    }
                )
            else:
                st.info("No hay movimientos registrados con los filtros seleccionados")
        
        with tab2:
            # --- Registrar Entrada ---
            st.subheader("➕ Registrar Entrada de Inventario")
            
            ingredientes = get_ingredientes_activos()
            if not ingredientes:
                st.error("No hay ingredientes activos disponibles")
            else:
                with st.form("entrada_form"):
                    # Selección de ingrediente
                    ingrediente_id = st.selectbox(
                        "Ingrediente:",
                        options=[i['_id'] for i in ingredientes],
                        format_func=lambda x: next((i.get('descripcion', 'Sin descripción') for i in ingredientes if i['_id'] == x), 'Sin descripción'),
                        key="entrada_ingrediente"
                    )
                    
                    # Datos de la entrada
                    col1, col2 = st.columns(2)
                    with col1:
                        cantidad = st.number_input(
                            "Cantidad:",
                            min_value=0.01,
                            step=0.01,
                            format="%.2f",
                            key="entrada_cantidad"
                        )
                    with col2:
                        unidad = next((i.get('unidad', 'unidad') for i in ingredientes if i['_id'] == ingrediente_id), 'unidad')
                        st.text_input("Unidad:", value=unidad, disabled=True)
                    
                    comentarios = st.text_area("Comentarios:")
                    
                    if st.form_submit_button("Registrar Entrada"):
                        # Crear documento de movimiento
                        movimiento = {
                            "_id": f"{CURRENT_PARTITION_KEY}:{str(uuid.uuid4())}",
                            "type": CURRENT_PARTITION_KEY,
                            "ingrediente_id": ingrediente_id,
                            "cantidad": cantidad,
                            "tipo": "entrada",
                            "usuario": st.session_state.get('user_data', {}).get('usuario', 'Desconocido'),
                            "comentarios": comentarios,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds')
                        }
                        
                        try:
                            db.save(movimiento)
                            st.success("✅ Entrada registrada correctamente!")
                            st.balloons()
                            
                            # Logging
                            logged_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            ingrediente_nombre = next((i.get('descripcion', 'N/A') for i in ingredientes if i['_id'] == ingrediente_id), 'N/A')
                            couchdb_utils.log_action(
                                db,
                                logged_user,
                                f"Entrada de inventario: {cantidad} {unidad} de {ingrediente_nombre}"
                            )
                            
                        except Exception as e:
                            st.error(f"Error al registrar entrada: {str(e)}")
        
        with tab3:
            # --- Registrar Salida ---
            st.subheader("➖ Registrar Salida de Inventario")
            
            ingredientes = get_ingredientes_activos()
            if not ingredientes:
                st.error("No hay ingredientes activos disponibles")
            else:
                with st.form("salida_form"):
                    # Selección de ingrediente con stock disponible
                    ingredientes_con_stock = []
                    for i in ingredientes:
                        stock = get_stock_actual(i['_id'])
                        if stock > 0:
                            ingredientes_con_stock.append({
                                'id': i['_id'],
                                'descripcion': i.get('descripcion', 'Sin descripción'),
                                'stock': stock,
                                'unidad': i.get('unidad', 'unidad')
                            })
                    
                    if not ingredientes_con_stock:
                        st.error("No hay ingredientes con stock disponible")
                        st.stop()
                    
                    ingrediente_id = st.selectbox(
                        "Ingrediente:",
                        options=[i['id'] for i in ingredientes_con_stock],
                        format_func=lambda x: f"{next(i['descripcion'] for i in ingredientes_con_stock if i['id'] == x)} (Stock: {next(i['stock'] for i in ingredientes_con_stock if i['id'] == x)})",
                        key="salida_ingrediente"
                    )
                    
                    # Datos de la salida
                    ingrediente_seleccionado = next((i for i in ingredientes_con_stock if i['id'] == ingrediente_id), None)
                    col1, col2 = st.columns(2)
                    with col1:
                        cantidad = st.number_input(
                            "Cantidad:",
                            min_value=0.01,
                            max_value=float(ingrediente_seleccionado['stock']) if ingrediente_seleccionado else 0.01,
                            step=0.01,
                            format="%.2f",
                            key="salida_cantidad"
                        )
                    with col2:
                        st.text_input("Unidad:", value=ingrediente_seleccionado['unidad'] if ingrediente_seleccionado else 'unidad', disabled=True)
                    
                    comentarios = st.text_area("Comentarios:", key="salida_comentarios")
                    
                    if st.form_submit_button("Registrar Salida"):
                        # Crear documento de movimiento
                        movimiento = {
                            "_id": f"{CURRENT_PARTITION_KEY}:{str(uuid.uuid4())}",
                            "type": CURRENT_PARTITION_KEY,
                            "ingrediente_id": ingrediente_id,
                            "cantidad": -cantidad,  # Negativo para salidas
                            "tipo": "salida",
                            "usuario": st.session_state.get('user_data', {}).get('usuario', 'Desconocido'),
                            "comentarios": comentarios,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds')
                        }
                        
                        try:
                            db.save(movimiento)
                            st.success("✅ Salida registrada correctamente!")
                            
                            # Logging
                            logged_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            ingrediente_nombre = ingrediente_seleccionado['descripcion'] if ingrediente_seleccionado else 'N/A'
                            ingrediente_unidad = ingrediente_seleccionado['unidad'] if ingrediente_seleccionado else 'unidad'
                            couchdb_utils.log_action(
                                db,
                                logged_user,
                                f"Salida de inventario: {cantidad} {ingrediente_unidad} de {ingrediente_nombre}"
                            )
                            
                        except Exception as e:
                            st.error(f"Error al registrar salida: {str(e)}")
        
        # --- Resumen de Inventario ---
        st.markdown("---")
        st.subheader("📊 Resumen de Inventario")
        
        ingredientes = get_ingredientes_activos()
        if ingredientes:
            data = []
            for ingrediente in ingredientes:
                stock = get_stock_actual(ingrediente['_id'])
                data.append({
                    'Ingrediente': ingrediente.get('descripcion', 'Sin descripción'),
                    'Stock Actual': stock,
                    'Unidad': ingrediente.get('unidad', 'unidad'),
                    'Estado': 'Disponible' if stock > 0 else 'Agotado'
                })
            
            df = pd.DataFrame(data)
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Stock Actual": st.column_config.ProgressColumn(
                        "Stock Actual",
                        help="Nivel de inventario actual",
                        format="%.2f",
                        min_value=0,
                        max_value=df['Stock Actual'].max() * 1.1 if not df.empty else 1  # Margen para visualización
                    ),
                    "Estado": st.column_config.TextColumn(
                        "Estado",
                        help="Disponibilidad del ingrediente"
                    )
                }
            )
        else:
            st.info("No hay ingredientes activos para mostrar")
    
    else:
        st.error("No se pudo conectar a la base de datos")
else:
    st.warning("Por favor inicie sesión para acceder al inventario")