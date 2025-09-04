# pages/ordenar.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone
import uuid

# Configuración básica
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
CURRENT_PARTITION_KEY = "ordenes"
couchdb_utils.generarLogin(archivo_actual_relativo)
st.set_page_config(layout="wide", page_title="Tomar Orden", page_icon="../assets/LOGO.png")

# Estilos CSS
st.markdown("""
<style>
    .menu-button {
        width: 100%;
        height: 80px;
        margin: 5px 0;
        white-space: normal;
    }
    .cart-item {
        border-bottom: 1px solid #eee;
        padding: 8px 0;
    }
    .summary-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        background-color: #f9f9f9;
    }
    .menu-category {
        font-size: 1.2em;
        font-weight: bold;
        margin-top: 15px;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # --- Inicialización ---
        if 'orden_actual' not in st.session_state:
            st.session_state.orden_actual = {
                'mesa': None,
                'mesero': None,
                'items': [],
                'comentarios': '',
                'numero_orden': couchdb_utils.get_next_order_number(db)
            }
        
        if 'plato_seleccionado' not in st.session_state:
            st.session_state.plato_seleccionado = None
        
        # --- Obtener datos ---
        def get_activos(docs):
            return [doc for doc in docs if doc.get('activo', 0) == 1]
        meseros = couchdb_utils.get_users_by_role(db, 3)
        # meseros = [doc for doc in couchdb_utils.get_documents_by_partition(db, "usuario") if doc.get('id_rol') == 3]
        mesas = get_activos(couchdb_utils.get_documents_by_partition(db, "mesas"))
        menus = get_activos(couchdb_utils.get_documents_by_partition(db, "menus"))
        platos = get_activos(couchdb_utils.get_documents_by_partition(db, "platos"))
        
        # --- Crear estructuras de relación ---
        menu_dict = {menu['_id']: menu for menu in menus}
        plato_dict = {plato['_id']: plato for plato in platos}
        
        # Agrupar platos por menú
        platos_por_menu = {}
        for plato in platos:
            menu_id = plato.get('id_menu')
            if menu_id in menu_dict:
                if menu_id not in platos_por_menu:
                    platos_por_menu[menu_id] = []
                platos_por_menu[menu_id].append(plato)
        
        # --- Encabezado ---
        st.title(f"Orden #{st.session_state.orden_actual['numero_orden']}")
        
        # --- Selección de mesa y mesero ---
        col1, col2 = st.columns(2)
        with col1:
            if mesas:
                mesa_seleccionada = st.selectbox(
                    "Seleccionar Mesa:",
                    options=[(m['_id'], m.get('descripcion', m['_id'])) for m in mesas],
                    format_func=lambda x: x[1],
                    key='select_mesa'
                )
                st.session_state.orden_actual['mesa'] = mesa_seleccionada[0]
            else:
                st.error("No hay mesas disponibles")
        
        with col2:
            if meseros:
                mesero_seleccionado = st.selectbox(
                    "Seleccionar Mesero:",
                    options=[(m['_id'], m.get('nombre', m['_id'])) for m in meseros],
                    format_func=lambda x: x[1],
                    key='select_mesero'
                )
                st.session_state.orden_actual['mesero'] = mesero_seleccionado[0]
            else:
                st.error("No hay meseros disponibles (rol_id=3)")
        
        if not st.session_state.orden_actual['mesa'] or not st.session_state.orden_actual['mesero']:
            st.error("Debes seleccionar mesa y mesero para continuar")
            st.stop()
        
        st.markdown("---")
        
        # --- Menú de Platos ---
        st.subheader("Menú")
        
        if not menus or not platos:
            st.error("No hay menús o platos disponibles")
            st.stop()
        
        # Agrupar menús por zona
        zonas = list(set(menu.get('zona', 'Sin zona') for menu in menus))
        
        tabs = st.tabs([f"📍 {zona}" for zona in zonas])
        
        for i, zona in enumerate(zonas):
            with tabs[i]:
                menus_zona = [m for m in menus if m.get('zona') == zona]
                
                if not menus_zona:
                    st.warning(f"No hay menús en la zona {zona}")
                    continue
                
                for menu in menus_zona:
                    with st.expander(f"🍽️ {menu.get('nombre', 'Sin nombre')}", expanded=False):
                        platos_menu = platos_por_menu.get(menu['_id'], [])
                        
                        if not platos_menu:
                            st.warning("No hay platos en este menú")
                            continue
                        
                        cols = st.columns(3)
                        for j, plato in enumerate(platos_menu):
                            with cols[j % 3]:
                                precio_normal = plato.get('precio_normal', 0)
                                precio_oferta = plato.get('precio_oferta')
                                
                                if precio_oferta and precio_oferta < precio_normal:
                                    precio_text = f"~~${precio_normal:.2f}~~ **${precio_oferta:.2f}**"
                                else:
                                    precio_text = f"${precio_normal:.2f}"
                                
                                if st.button(
                                    f"**{plato.get('descripcion', 'Sin nombre')}**\n\n{precio_text}",
                                    key=f"plato_{plato['_id']}_{menu['_id']}",
                                    help=plato.get('descripcion', ''),
                                    use_container_width=True
                                ):
                                    st.session_state.plato_seleccionado = plato
                                    st.rerun()
        
        # --- Detalles del Plato Seleccionado ---
        if st.session_state.plato_seleccionado:
            plato = st.session_state.plato_seleccionado
            st.markdown("---")
            st.subheader(f"🍲 {plato.get('descripcion', 'Plato')}")
            
            col_precio, col_cant, col_com = st.columns([1, 1, 2])
            with col_precio:
                if plato.get('precio_oferta') and plato['precio_oferta'] < plato.get('precio_normal', 0):
                    precio_options = {
                        'Normal': plato.get('precio_normal', 0),
                        'Promoción': plato.get('precio_oferta', 0)
                    }
                    precio_seleccionado = st.radio(
                        "Tipo de precio:",
                        options=list(precio_options.keys()),
                        index=1,
                        horizontal=True
                    )
                    precio = precio_options[precio_seleccionado]
                else:
                    precio = plato.get('precio_normal', 0)
                    st.write(f"**Precio:** ${precio:.2f}")
            
            with col_cant:
                cantidad = st.number_input(
                    "Cantidad:",
                    min_value=1,
                    value=1,
                    step=1
                )
            
            with col_com:
                comentarios = st.text_input("Comentarios/Especificaciones:")
            
            if st.button("➕ Agregar a la Orden", type="primary"):
                nuevo_item = {
                    'plato_id': plato['_id'],
                    'nombre': plato.get('descripcion', 'Plato'),
                    'precio_unitario': precio,
                    'cantidad': cantidad,
                    'comentarios': comentarios,
                    'tipo_precio': precio_seleccionado if 'precio_seleccionado' in locals() else 'Normal'
                }
                st.session_state.orden_actual['items'].append(nuevo_item)
                st.success(f"{cantidad} x {nuevo_item['nombre']} agregado a la orden!")
                st.session_state.plato_seleccionado = None
                st.rerun()
        
       # En la sección del carrito de compras, reemplaza con:

# --- Carrito de Compras ---
st.markdown("---")
expander_carrito = st.expander(f"🛒 Carrito de Compra ({len(st.session_state.orden_actual['items'])} items)", expanded=True)

with expander_carrito:
    if not st.session_state.orden_actual['items']:
        st.info("El carrito está vacío. Selecciona platos del menú para agregar.")
    else:
        # Mostrar items en el carrito
        for idx, item in enumerate(st.session_state.orden_actual['items']):
            cols = st.columns([4, 2, 2, 2, 1])
            with cols[0]:
                st.write(f"**{item['nombre']}**")
                if item['comentarios']:
                    st.caption(f"Notas: {item['comentarios']}")
            with cols[1]:
                st.write(f"${item['precio_unitario']:.2f}")
            with cols[2]:
                # Hacer la cantidad editable
                nueva_cantidad = st.number_input(
                    "Cantidad",
                    min_value=1,
                    value=item['cantidad'],
                    key=f"cant_{idx}",
                    label_visibility="collapsed"
                )
                if nueva_cantidad != item['cantidad']:
                    st.session_state.orden_actual['items'][idx]['cantidad'] = nueva_cantidad
                    st.rerun()
            with cols[3]:
                st.write(f"${item['precio_unitario'] * item['cantidad']:.2f}")
            with cols[4]:
                if st.button("❌", key=f"remove_{idx}"):
                    st.session_state.orden_actual['items'].pop(idx)
                    st.rerun()
        
        st.markdown("---")
        
        # Resumen y acciones
        col_resumen, col_acciones = st.columns([1, 2])
        
        with col_resumen:
            st.subheader("Resumen")
            total_items = sum(item['cantidad'] for item in st.session_state.orden_actual['items'])
            subtotal = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_actual['items'])
            
            st.markdown(f"""
            <div class="summary-card">
                <p><strong>Número de Orden:</strong> #{st.session_state.orden_actual['numero_orden']}</p>
                <p><strong>Total Items:</strong> {total_items}</p>
                <p><strong>Subtotal:</strong> ${subtotal:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_acciones:
            st.subheader("Acciones")
            comentarios_orden = st.text_area("Comentarios generales de la orden:", 
                                          value=st.session_state.orden_actual.get('comentarios', ''))
            st.session_state.orden_actual['comentarios'] = comentarios_orden
            
            col_enviar, col_limpiar, col_agregar = st.columns([1, 1, 1])
            with col_enviar:
                if st.button("🚀 Enviar Orden", type="primary", use_container_width=True, key="enviar_orden"):
                    if not st.session_state.orden_actual['items']:
                        st.error("¡El carrito está vacío! Agrega productos antes de enviar.")
                    else:
                        # Validar que tenemos mesa y mesero
                        if not st.session_state.orden_actual['mesa']:
                            st.error("Debes seleccionar una mesa antes de enviar la orden")
                        elif not st.session_state.orden_actual['mesero']:
                            st.error("Debes seleccionar un mesero antes de enviar la orden")
                        else:
                            # Crear documento de orden
                            orden_doc = {
                                "_id": f"{CURRENT_PARTITION_KEY}:{str(uuid.uuid4())}",
                                "type": CURRENT_PARTITION_KEY,
                                "numero_orden": st.session_state.orden_actual['numero_orden'],
                                "mesa_id": st.session_state.orden_actual['mesa'],
                                "mesero_id": st.session_state.orden_actual['mesero'],
                                "items": st.session_state.orden_actual['items'],
                                "comentarios": st.session_state.orden_actual.get('comentarios', ''),
                                "estado": "pendiente",
                                "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                                "total": sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_actual['items'])
                            }
                            
                            try:
                                # Guardar en la base de datos
                                db.save(orden_doc)
                                
                                # Mostrar confirmación
                                st.success(f"✅ Orden #{orden_doc['numero_orden']} enviada a cocina exitosamente!")
                                
                                # Logging de la acción
                                logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                couchdb_utils.log_action(db, logged_in_user, f"Orden #{orden_doc['numero_orden']} creada para mesa {orden_doc['mesa_id']}")
                                
                                # Resetear la orden (pero mantener mesa y mesero)
                                st.session_state.orden_actual = {
                                    'mesa': st.session_state.orden_actual['mesa'],
                                    'mesero': st.session_state.orden_actual['mesero'],
                                    'items': [],
                                    'comentarios': '',
                                    'numero_orden': couchdb_utils.get_next_order_number(db)
                                }
                                
                                # Opcional: Mostrar resumen de la orden enviada
                                with st.expander("Ver resumen de orden enviada", expanded=True):
                                    st.json(orden_doc)
                                
                                st.balloons()  # Efecto visual de celebración
                                
                            except Exception as e:
                                st.error(f"❌ Error al guardar la orden: {str(e)}")
                                st.error("Por favor intenta nuevamente o contacta al administrador")
            with col_limpiar:
                if st.button("♻️ Limpiar", type="secondary", use_container_width=True):
                    st.session_state.orden_actual['items'] = []
                    st.rerun()
            with col_agregar:
                if st.button("➕ Agregar Más", type="secondary", use_container_width=True):
                    st.session_state.plato_seleccionado = None
                    st.rerun()