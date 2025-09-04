# pages/restaurant_main.py (or modify pages/ordenar.py)
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone
import uuid
import base64 # Import base64 for embedding PDF

# --- Configuración Inicial ---
st.set_page_config(layout="wide", page_title="Operaciones de Restaurante", page_icon="../assets/LOGO.png")
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)

# --- Estilos CSS ---
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
        margin-bottom: 10px;
    }
    .menu-category {
        font-size: 1.2em;
        font-weight: bold;
        margin-top: 15px;
        color: #2c3e50;
    }
    .order-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    .item-row {
        border-bottom: 1px solid #eee;
        padding: 5px 0;
        font-size: 0.9em;
    }
    .action-button {
        margin: 2px;
    }
    .beverage-ready {
        background-color: #d4edda;
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 8px;
        margin: 5px 0;
        animation: pulse-green 2s infinite;
    }
    .beverage-process {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 8px;
        margin: 5px 0;
    }
    @keyframes pulse-green {
        0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
    }
    .notification-badge {
        background-color: #dc3545;
        color: white;
        border-radius: 50%;
        padding: 2px 6px;
        font-size: 0.75em;
        margin-left: 5px;
    }
    .orden-title {
        color: #ff9500 !important;
    }
    
    /* Cambiar el fondo del expander a naranja claro */
    .streamlit-expanderHeader {
        background-color: #ffe4b3 !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="expander"] > div:first-child {
        background-color: #ffe4b3 !important;
        border-radius: 8px !important;
    }
    
    /* Estilos para botones de categorías */
    .category-bebidas button {
        background: linear-gradient(135deg, #ff6b9d 0%, #ff8a9b 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 8px rgba(255, 107, 157, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .category-bebidas button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(255, 107, 157, 0.4) !important;
    }
    
    .category-comida button {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 8px rgba(0, 184, 148, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .category-comida button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0, 184, 148, 0.4) !important;
    }
    
    /* Estilos para promociones */
    .stButton > button[data-baseweb="button"]:has([class*="promo_bar_"]) {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
        color: #000 !important;
        font-weight: bold !important;
        border: 2px solid #FF6347 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 8px rgba(255, 215, 0, 0.4) !important;
        animation: promo-glow 2s ease-in-out infinite alternate;
    }
    
    .stButton > button[data-baseweb="button"]:has([class*="promo_cocina_"]) {
        background: linear-gradient(135deg, #32CD32 0%, #228B22 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: 2px solid #FF6347 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 8px rgba(50, 205, 50, 0.4) !important;
        animation: promo-glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes promo-glow {
        0% { 
            box-shadow: 0 4px 8px rgba(255, 215, 0, 0.4);
            transform: scale(1);
        }
        100% { 
            box-shadow: 0 8px 16px rgba(255, 215, 0, 0.8);
            transform: scale(1.02);
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Función para generar colores dinámicos ---
def get_dynamic_color(plato_id, index=0):
    """Genera un color de fondo dinámico basado en el ID del plato"""
    colores = [
        "#e8f5e8",  # Verde claro
        "#e8f4fd",  # Azul claro
        "#fff3e0",  # Naranja claro
        "#f3e5f5",  # Morado claro
        "#fff8e1",  # Amarillo claro
        "#e0f2f1",  # Verde agua claro
        "#fce4ec",  # Rosa claro
        "#f1f8e9",  # Verde lima claro
        "#e3f2fd",  # Azul cielo claro
        "#fff9c4",  # Amarillo pastel
        "#f9fbe7",  # Verde pastel
        "#fdf2e9"   # Durazno claro
    ]
    # Usar el hash del plato_id para seleccionar un color consistente
    color_index = hash(plato_id) % len(colores)
    return colores[color_index]

# --- Lógica Principal de la Pantalla ---
if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # --- Inicialización de Session State ---
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
            
        if 'plato_desplegado' not in st.session_state:
            st.session_state.plato_desplegado = None
            
        if 'cantidad_desplegado' not in st.session_state:
            st.session_state.cantidad_desplegado = 1
            
        if 'comentarios_desplegado' not in st.session_state:
            st.session_state.comentarios_desplegado = ""
            
        if 'orden_editar' not in st.session_state:
            st.session_state.orden_editar = None # Stores the order object being edited
            
        if 'just_processed_ticket_display' not in st.session_state:
            st.session_state['just_processed_ticket_display'] = None

        # --- Display PDF and Download Button if a ticket was just processed ---
        if st.session_state['just_processed_ticket_display'] is not None:
            info = st.session_state.pop('just_processed_ticket_display')
            st.success(info['message'])
            
            st.download_button(
                label="📄 Descargar Ticket en PDF",
                data=info['pdf_data'],
                file_name=info['file_name'],
                mime="application/pdf"
            )
            
            # Optional: Display PDF directly using base64
            base64_pdf = base64.b64encode(info['pdf_data']).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border: none;"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            st.markdown("---") # Add a separator after displaying PDF

        # --- Funciones para promociones ---
        def obtener_promociones_activas(tipo_menu):
            """Obtiene promociones activas para un tipo de menu especifico"""
            try:
                from datetime import datetime, timezone
                promociones = couchdb_utils.get_documents_by_partition(db, "promociones")
                ahora = datetime.now(timezone.utc)
                
                promociones_activas = []
                for promo in promociones:
                    if (promo.get('estado') == 'activa' and 
                        promo.get('activo', True) and 
                        promo.get('tipo_menu') == tipo_menu):
                        
                        # Verificar que aún esté dentro del tiempo válido
                        try:
                            fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                            if ahora <= fecha_fin:
                                promociones_activas.append(promo)
                        except:
                            continue
                
                return promociones_activas
            except Exception as e:
                st.error(f"Error obteniendo promociones: {str(e)}")
                return []

        # --- Layout: Menu (Left) + Cart (Right) ---
        col_menu, col_cart = st.columns([2, 1])  # 66% menu, 33% cart
        
        with col_menu:
            # --- Get Data for Menu ---
            def get_activos(docs):
                return [doc for doc in docs if doc.get('activo', 0) == 1]
            
            # Obtener informacion del usuario logueado
            user_data = st.session_state.get('user_data', {})
            user_role = user_data.get('id_rol')
            user_id = user_data.get('_id')
            
            # Convert meseros and mesas to dictionaries for easy lookup by _id
            meseros_list = couchdb_utils.get_users_by_role(db, 3)
            meseros = {m['_id']: m for m in meseros_list}

            mesas_list = get_activos(couchdb_utils.get_documents_by_partition(db, "mesas"))
            mesas = {m['_id']: m for m in mesas_list}

            # --- Mesa y Mesero Selection ---
            st.subheader("📍 Nueva Orden")
            
            # Mesa Selection
            if mesas_list:
                mesa_opciones = {mesa['_id']: f"Mesa {mesa.get('descripcion', 'N/A')}" for mesa in mesas_list}
                mesa_seleccionada_id = st.selectbox(
                    "Seleccionar Mesa:",
                    options=list(mesa_opciones.keys()),
                    format_func=lambda x: mesa_opciones[x],
                    key='select_mesa'
                )
                st.session_state.orden_actual['mesa'] = mesa_seleccionada_id
            else:
                st.error("No hay mesas disponibles")
                
            # Mesero Selection (depends on user role)
            if user_role == 3:
                # Para meseros: asignar automaticamente su propio ID
                st.session_state.orden_actual['mesero'] = user_id
                st.info(f"👤 Mesero asignado: {user_data.get('nombre', 'Tú')}")
            else:
                # Para otros roles: permitir seleccion de mesero
                if meseros:
                    mesero_seleccionado_id = st.selectbox(
                        "Seleccionar Mesero:",
                        options=list(meseros.keys()),
                        format_func=lambda x: meseros[x].get('nombre', x),
                        key='select_mesero'
                    )
                    st.session_state.orden_actual['mesero'] = mesero_seleccionado_id
                else:
                    st.error("No hay meseros disponibles (rol_id=3)")

            # Validacion diferente segun el rol
            if user_role == 3:
                # Para meseros: solo validar mesa
                if not st.session_state.orden_actual['mesa']:
                    st.warning("Debes seleccionar una mesa para tomar la orden.")
            else:
                # Para otros roles: validar mesa y mesero
                if not st.session_state.orden_actual['mesa'] or not st.session_state.orden_actual['mesero']:
                    st.warning("Debes seleccionar mesa y mesero para tomar una nueva orden.")

            st.markdown("---")

            # --- Menu de Platos ---
            st.subheader("🍽️ Menú de Platos")
            
            # Obtener menus y filtrar segun el rol del usuario
            todos_menus = get_activos(couchdb_utils.get_documents_by_partition(db, "menus"))
            
            if user_role == 3:
                # Para meseros (rol 3): filtrar menus de bebidas y comida
                # Menus de bebidas (bar)
                menus_bebidas = ['cocteles', 'bebidas naturales', 'bebidas sin alcohol', 'cerveza', 'cover', 'botellas', 'shots']
                # Menus de comida (cocina)  
                menus_comida = ['comida mexicana', 'platos fuertes', 'boquitas']
                
                menus_permitidos = menus_bebidas + menus_comida
                
                menus = [menu for menu in todos_menus 
                        if menu.get('nombre', '').lower() in menus_permitidos]
            else:
                # Para otros roles: mostrar todos los menus
                menus = todos_menus
            
            platos = get_activos(couchdb_utils.get_documents_by_partition(db, "platos"))
            
            menu_dict = {menu['_id']: menu for menu in menus}
            plato_dict = {plato['_id']: plato for plato in platos}
            
            platos_por_menu = {}
            for plato in platos:
                menu_id = plato.get('id_menu')
                if menu_id in menu_dict:
                    if menu_id not in platos_por_menu:
                        platos_por_menu[menu_id] = []
                    platos_por_menu[menu_id].append(plato)
            
            if not menus or not platos:
                if user_role == 3:
                    st.error("No hay menús de cocina o bar disponibles.")
                else:
                    st.error("No hay menús o platos disponibles.")
            else:
                # Función para obtener color por categoría de menú
                def get_menu_color(menu_name):
                    menu_colors = {
                        'cocteles': '#ff6b9d',
                        'bebidas naturales': '#4ecdc4', 
                        'bebidas sin alcohol': '#45b7d1',
                        'cerveza': '#f9ca24',
                        'cover': '#6c5ce7',
                        'botellas': '#a29bfe',
                        'shots': '#fd79a8',
                        'comida mexicana': '#e17055',
                        'platos fuertes': '#00b894',
                        'boquitas': '#fdcb6e'
                    }
                    return menu_colors.get(menu_name.lower(), '#74b9ff')
                
                # Organizar platos por categoría de manera más visual
                st.markdown("### 🍹 **BEBIDAS**")
                
                # Bebidas en una sola fila con scroll horizontal
                bebidas_menus = [m for m in menus if m.get('nombre', '').lower() in ['cocteles', 'bebidas naturales', 'bebidas sin alcohol', 'cerveza', 'cover', 'botellas', 'shots']]
                
                if bebidas_menus:
                    cols_bebidas = st.columns(min(len(bebidas_menus), 4))
                    for idx, menu in enumerate(bebidas_menus):
                        with cols_bebidas[idx % 4]:
                            color = get_menu_color(menu.get('nombre', ''))
                            
                            # Botón de categoría de bebidas
                            if st.button(
                                f"🍹 **{menu.get('nombre', 'Sin nombre')}**",
                                key=f"menu_bebidas_{menu['_id']}",
                                help=f"Ver bebidas de {menu.get('nombre', '')}",
                                use_container_width=True
                            ):
                                # Cerrar todos los otros menús antes de abrir el seleccionado
                                for all_menu in menus:
                                    if all_menu['_id'] != menu['_id']:
                                        st.session_state[f"show_menu_{all_menu['_id']}"] = False
                                
                                # Toggle del menú seleccionado
                                st.session_state[f"show_menu_{menu['_id']}"] = not st.session_state.get(f"show_menu_{menu['_id']}", False)
                    
                    # Mostrar platos de bebidas seleccionadas
                    for menu in bebidas_menus:
                        if st.session_state.get(f"show_menu_{menu['_id']}", False):
                            platos_menu = platos_por_menu.get(menu['_id'], [])
                            if platos_menu:
                                st.markdown(f"**🍹 {menu.get('nombre', '')}:**")
                                cols_platos = st.columns(4)
                                
                                for j, plato in enumerate(platos_menu):
                                    with cols_platos[j % 4]:
                                        precio_normal = plato.get('precio_normal', 0)
                                        precio_oferta = plato.get('precio_oferta')
                                        
                                        precio_final = precio_oferta if precio_oferta and precio_oferta < precio_normal else precio_normal
                                        color = get_menu_color(menu.get('nombre', ''))
                                        
                                        # Botón de plato con desplegable
                                        if st.button(
                                            f"**{plato.get('descripcion', 'Sin nombre')}**\n💰 ${precio_final:.2f}",
                                            key=f"plato_bebida_{plato['_id']}",
                                            help=f"Seleccionar {plato.get('descripcion', '')}",
                                            use_container_width=True
                                        ):
                                            if st.session_state.plato_desplegado == plato['_id']:
                                                # Si ya está desplegado, lo cerramos
                                                st.session_state.plato_desplegado = None
                                            else:
                                                # Desplegamos este plato
                                                st.session_state.plato_desplegado = plato['_id']
                                                st.session_state.plato_seleccionado = plato
                                                st.session_state.cantidad_desplegado = 1
                                                st.session_state.comentarios_desplegado = ""
                                            st.rerun()
                
                # Mostrar desplegable de plato seleccionado (BEBIDAS)
                bebidas_platos_ids = []
                for menu in bebidas_menus:
                    if menu['_id'] in platos_por_menu:
                        bebidas_platos_ids.extend([p['_id'] for p in platos_por_menu[menu['_id']]])
                
                if (st.session_state.plato_desplegado and 
                    st.session_state.plato_seleccionado and
                    not st.session_state.plato_seleccionado.get('es_promocion', False) and
                    st.session_state.plato_desplegado in bebidas_platos_ids):
                    
                    plato_actual = st.session_state.plato_seleccionado
                    
                    with st.container():
                        st.markdown("### 🍹 Agregar al Carrito")
                        
                        # Crear tarjeta visual del plato
                        precio_normal = plato_actual.get('precio_normal', 0)
                        precio_oferta = plato_actual.get('precio_oferta')
                        precio_final = precio_oferta if precio_oferta and precio_oferta < precio_normal else precio_normal
                        
                        st.markdown(f"""
                        <div style="background-color: #e8f4fd; padding: 15px; border-radius: 10px; border: 2px solid #45b7d1; margin: 10px 0;">
                            <h4 style="color: #2c3e50; margin: 0;">🍹 {plato_actual.get('descripcion', 'Bebida')}</h4>
                            <p style="color: #007bb5; font-size: 1.1em; font-weight: bold; margin: 5px 0;">💰 ${precio_final:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Controles
                        col_qty, col_total = st.columns([2, 1])
                        
                        with col_qty:
                            st.session_state.cantidad_desplegado = st.number_input(
                                "Cantidad:", 
                                min_value=1, 
                                value=st.session_state.cantidad_desplegado, 
                                step=1, 
                                key="bebida_qty_control"
                            )
                            
                            st.session_state.comentarios_desplegado = st.text_input(
                                "Comentarios/Notas:",
                                value=st.session_state.comentarios_desplegado,
                                key="bebida_comments_control"
                            )
                        
                        with col_total:
                            total_item = precio_final * st.session_state.cantidad_desplegado
                            st.metric("Total", f"${total_item:.2f}")
                        
                        # Botones de acción
                        col_add, col_cancel = st.columns(2)
                        
                        with col_add:
                            if st.button("✅ Agregar al Carrito", type="primary", key="add_bebida_desplegado"):
                                tipo_precio = 'Oferta' if precio_oferta and precio_oferta < precio_normal else 'Normal'
                                
                                nuevo_item = {
                                    'plato_id': plato_actual['_id'],
                                    'nombre': plato_actual.get('descripcion', 'Bebida'),
                                    'precio_unitario': precio_final,
                                    'cantidad': st.session_state.cantidad_desplegado,
                                    'comentarios': st.session_state.comentarios_desplegado,
                                    'tipo_precio': tipo_precio
                                }
                                
                                # Agregar al carrito correcto
                                if st.session_state.orden_editar:
                                    st.session_state.orden_editar['items'].append(nuevo_item)
                                    st.session_state.orden_editar['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_editar['items'])
                                else:
                                    st.session_state.orden_actual['items'].append(nuevo_item)
                                    st.session_state.orden_actual['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_actual['items'])
                                
                                # Limpiar desplegable
                                st.session_state.plato_desplegado = None
                                st.session_state.plato_seleccionado = None
                                st.session_state.cantidad_desplegado = 1
                                st.session_state.comentarios_desplegado = ""
                                
                                st.success(f"✅ {nuevo_item['nombre']} agregado al carrito!")
                                st.rerun()
                        
                        with col_cancel:
                            if st.button("❌ Cancelar", key="cancel_bebida_desplegado"):
                                st.session_state.plato_desplegado = None
                                st.session_state.plato_seleccionado = None
                                st.session_state.cantidad_desplegado = 1
                                st.session_state.comentarios_desplegado = ""
                                st.rerun()
                        
                        st.markdown("---")
                
                st.markdown("---")
                
                # === SECCION DE PROMOCIONES BAR ===
                # Solo mostrar promociones para meseros (rol 3) y admins (rol 1)
                if user_role in [1, 3]:
                    promociones_bar = obtener_promociones_activas('promoBar')
                    
                    # Debug: mostrar información sobre promociones (remover después)
                    if st.checkbox("🔍 Debug: Mostrar info promociones", help="Para diagnóstico"):
                        st.write(f"**Rol usuario:** {user_role}")
                        st.write(f"**Total promociones bar encontradas:** {len(promociones_bar)}")
                        if promociones_bar:
                            st.write("**Promociones bar:**")
                            for i, p in enumerate(promociones_bar):
                                st.write(f"{i+1}. {p.get('nombre_promocion')} - Estado: {p.get('estado')} - Activo: {p.get('activo')}")
                        
                        promociones_todas = []
                        try:
                            from datetime import datetime, timezone
                            promociones_todas = couchdb_utils.get_documents_by_partition(db, "promociones")
                            st.write(f"**Total promociones en DB:** {len(promociones_todas)}")
                            if promociones_todas:
                                st.write("**Todas las promociones:**")
                                for i, p in enumerate(promociones_todas):
                                    st.write(f"{i+1}. {p.get('nombre_promocion')} - Tipo: {p.get('tipo_menu')} - Estado: {p.get('estado')} - Activo: {p.get('activo')}")
                        except Exception as e:
                            st.error(f"Error obteniendo promociones: {e}")
                else:
                    promociones_bar = []
                
                if promociones_bar:
                    st.markdown("### 🎉 **PROMOCIONES BAR** ⭐")
                    
                    # Mostrar promociones en grid
                    cols_promo_bar = st.columns(min(len(promociones_bar), 4))
                    
                    for idx, promo in enumerate(promociones_bar):
                        with cols_promo_bar[idx % 4]:
                            # Calcular tiempo restante
                            try:
                                from datetime import datetime, timezone
                                fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                                tiempo_restante = fecha_fin - datetime.now(timezone.utc)
                                total_seconds = max(0, tiempo_restante.total_seconds())
                                
                                if total_seconds < 3600:  # Menos de 1 hora
                                    minutos_restantes = int(total_seconds // 60)
                                    tiempo_texto = f"{minutos_restantes}min restantes"
                                else:
                                    horas = int(total_seconds // 3600)
                                    minutos = int((total_seconds % 3600) // 60)
                                    if minutos > 0:
                                        tiempo_texto = f"{horas}h {minutos}min restantes"
                                    else:
                                        tiempo_texto = f"{horas}h restantes"
                            except:
                                tiempo_texto = "0min restantes"
                            
                            # Calcular descuento
                            precio_original = promo.get('precio_original', 0)
                            precio_promo = promo.get('precio_promocion', 0)
                            descuento = int(promo.get('descuento_porcentaje', 0))
                            
                            # Botón de promoción con estilo especial
                            promo_text = f"🎉 **{promo.get('nombre_producto', 'Promo')}**\n💥 -{descuento}% OFF\n💰 ${precio_promo:.2f} ~~${precio_original:.2f}~~\n⏰ {tiempo_texto}"
                            
                            if st.button(
                                promo_text,
                                key=f"promo_bar_{promo['_id']}",
                                help=f"Promoción: {promo.get('nombre_promocion', '')}",
                                use_container_width=True
                            ):
                                # Crear "plato" temporal para el desplegable con datos de la promoción
                                plato_promo = {
                                    '_id': promo.get('plato_id', ''),
                                    'descripcion': f"🎉 {promo.get('nombre_producto', 'Promoción')} (OFERTA)",
                                    'precio_normal': precio_original,
                                    'precio_oferta': precio_promo,
                                    'es_promocion': True,
                                    'promocion_id': promo['_id'],
                                    'promocion_nombre': promo.get('nombre_promocion', '')
                                }
                                
                                if st.session_state.plato_desplegado == promo['_id']:
                                    # Si ya está desplegado, lo cerramos
                                    st.session_state.plato_desplegado = None
                                else:
                                    # Desplegamos esta promoción
                                    st.session_state.plato_desplegado = promo['_id']
                                    st.session_state.plato_seleccionado = plato_promo
                                    st.session_state.cantidad_desplegado = 1
                                    st.session_state.comentarios_desplegado = ""
                                st.rerun()
                    
                    st.markdown("---")
                
                st.markdown("### 🍽️ **COMIDA**")
                
                # Comida en una sola fila
                comida_menus = [m for m in menus if m.get('nombre', '').lower() in ['comida mexicana', 'platos fuertes', 'boquitas']]
                
                if comida_menus:
                    cols_comida = st.columns(min(len(comida_menus), 3))
                    for idx, menu in enumerate(comida_menus):
                        with cols_comida[idx % 3]:
                            color = get_menu_color(menu.get('nombre', ''))
                            
                            # Botón de categoría de comida
                            if st.button(
                                f"🍽️ **{menu.get('nombre', 'Sin nombre')}**",
                                key=f"menu_comida_{menu['_id']}",
                                help=f"Ver platos de {menu.get('nombre', '')}",
                                use_container_width=True
                            ):
                                # Cerrar todos los otros menús antes de abrir el seleccionado
                                for all_menu in menus:
                                    if all_menu['_id'] != menu['_id']:
                                        st.session_state[f"show_menu_{all_menu['_id']}"] = False
                                
                                # Toggle del menú seleccionado
                                st.session_state[f"show_menu_{menu['_id']}"] = not st.session_state.get(f"show_menu_{menu['_id']}", False)
                    
                    # Mostrar platos de comida seleccionadas
                    for menu in comida_menus:
                        if st.session_state.get(f"show_menu_{menu['_id']}", False):
                            platos_menu = platos_por_menu.get(menu['_id'], [])
                            if platos_menu:
                                st.markdown(f"**🍽️ {menu.get('nombre', '')}:**")
                                cols_platos = st.columns(4)
                                
                                for j, plato in enumerate(platos_menu):
                                    with cols_platos[j % 4]:
                                        precio_normal = plato.get('precio_normal', 0)
                                        precio_oferta = plato.get('precio_oferta')
                                        
                                        precio_final = precio_oferta if precio_oferta and precio_oferta < precio_normal else precio_normal
                                        color = get_menu_color(menu.get('nombre', ''))
                                        
                                        # Botón de plato con desplegable
                                        if st.button(
                                            f"**{plato.get('descripcion', 'Sin nombre')}**\n💰 ${precio_final:.2f}",
                                            key=f"plato_comida_{plato['_id']}",
                                            help=f"Seleccionar {plato.get('descripcion', '')}",
                                            use_container_width=True
                                        ):
                                            if st.session_state.plato_desplegado == plato['_id']:
                                                # Si ya está desplegado, lo cerramos
                                                st.session_state.plato_desplegado = None
                                            else:
                                                # Desplegamos este plato
                                                st.session_state.plato_desplegado = plato['_id']
                                                st.session_state.plato_seleccionado = plato
                                                st.session_state.cantidad_desplegado = 1
                                                st.session_state.comentarios_desplegado = ""
                                            st.rerun()
                
                # Mostrar desplegable de plato seleccionado (COMIDA)
                comida_platos_ids = []
                for menu in comida_menus:
                    if menu['_id'] in platos_por_menu:
                        comida_platos_ids.extend([p['_id'] for p in platos_por_menu[menu['_id']]])
                
                if (st.session_state.plato_desplegado and 
                    st.session_state.plato_seleccionado and
                    not st.session_state.plato_seleccionado.get('es_promocion', False) and
                    st.session_state.plato_desplegado in comida_platos_ids):
                    
                    plato_actual = st.session_state.plato_seleccionado
                    
                    with st.container():
                        st.markdown("### 🍽️ Agregar al Carrito")
                        
                        # Crear tarjeta visual del plato
                        precio_normal = plato_actual.get('precio_normal', 0)
                        precio_oferta = plato_actual.get('precio_oferta')
                        precio_final = precio_oferta if precio_oferta and precio_oferta < precio_normal else precio_normal
                        
                        st.markdown(f"""
                        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 10px; border: 2px solid #00b894; margin: 10px 0;">
                            <h4 style="color: #2c3e50; margin: 0;">🍽️ {plato_actual.get('descripcion', 'Plato')}</h4>
                            <p style="color: #00b894; font-size: 1.1em; font-weight: bold; margin: 5px 0;">💰 ${precio_final:.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Controles
                        col_qty, col_total = st.columns([2, 1])
                        
                        with col_qty:
                            st.session_state.cantidad_desplegado = st.number_input(
                                "Cantidad:", 
                                min_value=1, 
                                value=st.session_state.cantidad_desplegado, 
                                step=1, 
                                key="comida_qty_control"
                            )
                            
                            st.session_state.comentarios_desplegado = st.text_input(
                                "Comentarios/Notas:",
                                value=st.session_state.comentarios_desplegado,
                                key="comida_comments_control"
                            )
                        
                        with col_total:
                            total_item = precio_final * st.session_state.cantidad_desplegado
                            st.metric("Total", f"${total_item:.2f}")
                        
                        # Botones de acción
                        col_add, col_cancel = st.columns(2)
                        
                        with col_add:
                            if st.button("✅ Agregar al Carrito", type="primary", key="add_comida_desplegado"):
                                tipo_precio = 'Oferta' if precio_oferta and precio_oferta < precio_normal else 'Normal'
                                
                                nuevo_item = {
                                    'plato_id': plato_actual['_id'],
                                    'nombre': plato_actual.get('descripcion', 'Plato'),
                                    'precio_unitario': precio_final,
                                    'cantidad': st.session_state.cantidad_desplegado,
                                    'comentarios': st.session_state.comentarios_desplegado,
                                    'tipo_precio': tipo_precio
                                }
                                
                                # Agregar al carrito correcto
                                if st.session_state.orden_editar:
                                    st.session_state.orden_editar['items'].append(nuevo_item)
                                    st.session_state.orden_editar['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_editar['items'])
                                else:
                                    st.session_state.orden_actual['items'].append(nuevo_item)
                                    st.session_state.orden_actual['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_actual['items'])
                                
                                # Limpiar desplegable
                                st.session_state.plato_desplegado = None
                                st.session_state.plato_seleccionado = None
                                st.session_state.cantidad_desplegado = 1
                                st.session_state.comentarios_desplegado = ""
                                
                                st.success(f"✅ {nuevo_item['nombre']} agregado al carrito!")
                                st.rerun()
                        
                        with col_cancel:
                            if st.button("❌ Cancelar", key="cancel_comida_desplegado"):
                                st.session_state.plato_desplegado = None
                                st.session_state.plato_seleccionado = None
                                st.session_state.cantidad_desplegado = 1
                                st.session_state.comentarios_desplegado = ""
                                st.rerun()
                        
                        st.markdown("---")
                
                # === SECCION DE PROMOCIONES COCINA ===
                # Solo mostrar promociones para meseros (rol 3) y admins (rol 1)
                if user_role in [1, 3]:
                    promociones_cocina = obtener_promociones_activas('promoCocina')
                else:
                    promociones_cocina = []
                
                if promociones_cocina:
                    st.markdown("---")
                    st.markdown("### 🍳 **PROMOCIONES COCINA** ⭐")
                    
                    # Mostrar promociones en grid
                    cols_promo_cocina = st.columns(min(len(promociones_cocina), 4))
                    
                    for idx, promo in enumerate(promociones_cocina):
                        with cols_promo_cocina[idx % 4]:
                            # Calcular tiempo restante
                            try:
                                from datetime import datetime, timezone
                                fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                                tiempo_restante = fecha_fin - datetime.now(timezone.utc)
                                total_seconds = max(0, tiempo_restante.total_seconds())
                                
                                if total_seconds < 3600:  # Menos de 1 hora
                                    minutos_restantes = int(total_seconds // 60)
                                    tiempo_texto = f"{minutos_restantes}min restantes"
                                else:
                                    horas = int(total_seconds // 3600)
                                    minutos = int((total_seconds % 3600) // 60)
                                    if minutos > 0:
                                        tiempo_texto = f"{horas}h {minutos}min restantes"
                                    else:
                                        tiempo_texto = f"{horas}h restantes"
                            except:
                                tiempo_texto = "0min restantes"
                            
                            # Calcular descuento
                            precio_original = promo.get('precio_original', 0)
                            precio_promo = promo.get('precio_promocion', 0)
                            descuento = int(promo.get('descuento_porcentaje', 0))
                            
                            # Botón de promoción con estilo especial
                            promo_text = f"🍳 **{promo.get('nombre_producto', 'Promo')}**\n💥 -{descuento}% OFF\n💰 ${precio_promo:.2f} ~~${precio_original:.2f}~~\n⏰ {tiempo_texto}"
                            
                            if st.button(
                                promo_text,
                                key=f"promo_cocina_{promo['_id']}",
                                help=f"Promoción: {promo.get('nombre_promocion', '')}",
                                use_container_width=True
                            ):
                                # Crear "plato" temporal para el desplegable con datos de la promoción
                                plato_promo = {
                                    '_id': promo.get('plato_id', ''),
                                    'descripcion': f"🍳 {promo.get('nombre_producto', 'Promoción')} (OFERTA)",
                                    'precio_normal': precio_original,
                                    'precio_oferta': precio_promo,
                                    'es_promocion': True,
                                    'promocion_id': promo['_id'],
                                    'promocion_nombre': promo.get('nombre_promocion', '')
                                }
                                
                                if st.session_state.plato_desplegado == promo['_id']:
                                    # Si ya está desplegado, lo cerramos
                                    st.session_state.plato_desplegado = None
                                else:
                                    # Desplegamos esta promoción
                                    st.session_state.plato_desplegado = promo['_id']
                                    st.session_state.plato_seleccionado = plato_promo
                                    st.session_state.cantidad_desplegado = 1
                                    st.session_state.comentarios_desplegado = ""
                                st.rerun()
            
            # Mostrar desplegable de promoción seleccionada (BAR/COCINA)
            if (st.session_state.plato_desplegado and 
                st.session_state.plato_seleccionado and
                st.session_state.plato_seleccionado.get('es_promocion', False)):
                
                promo_actual = st.session_state.plato_seleccionado
                
                with st.container():
                    st.markdown("### 🎉 Agregar Promoción al Carrito")
                    
                    # Crear tarjeta visual de la promoción
                    precio_normal = promo_actual.get('precio_normal', 0)
                    precio_final = promo_actual.get('precio_oferta', 0)
                    
                    # Calcular descuento
                    if precio_normal > 0:
                        descuento = int(((precio_normal - precio_final) / precio_normal) * 100)
                    else:
                        descuento = 0
                    
                    st.markdown(f"""
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 10px; border: 2px solid #ffc107; margin: 10px 0;">
                        <h4 style="color: #2c3e50; margin: 0;">🎉 {promo_actual.get('descripcion', 'Promoción')}</h4>
                        <p style="color: #ff6b35; font-size: 1.2em; font-weight: bold; margin: 5px 0;">💥 -{descuento}% OFF</p>
                        <p style="color: #28a745; font-size: 1.1em; font-weight: bold; margin: 5px 0;">💰 ${precio_final:.2f} <s style="color: #dc3545;">${precio_normal:.2f}</s></p>
                        <p style="color: #6c757d; font-size: 0.9em; margin: 5px 0;">🏷️ {promo_actual.get('promocion_nombre', 'Oferta especial')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Controles
                    col_qty, col_total = st.columns([2, 1])
                    
                    with col_qty:
                        st.session_state.cantidad_desplegado = st.number_input(
                            "Cantidad:", 
                            min_value=1, 
                            value=st.session_state.cantidad_desplegado, 
                            step=1, 
                            key="promo_qty_control"
                        )
                        
                        st.session_state.comentarios_desplegado = st.text_input(
                            "Comentarios/Notas:",
                            value=st.session_state.comentarios_desplegado,
                            key="promo_comments_control"
                        )
                    
                    with col_total:
                        total_item = precio_final * st.session_state.cantidad_desplegado
                        ahorro_total = (precio_normal - precio_final) * st.session_state.cantidad_desplegado
                        st.metric("Total", f"${total_item:.2f}")
                        st.success(f"💰 Ahorras: ${ahorro_total:.2f}")
                    
                    # Botones de acción
                    col_add, col_cancel = st.columns(2)
                    
                    with col_add:
                        if st.button("✅ Agregar al Carrito", type="primary", key="add_promo_desplegado"):
                            nuevo_item = {
                                'plato_id': promo_actual['_id'],
                                'nombre': promo_actual.get('descripcion', 'Promoción'),
                                'precio_unitario': precio_final,
                                'cantidad': st.session_state.cantidad_desplegado,
                                'comentarios': st.session_state.comentarios_desplegado,
                                'tipo_precio': 'Promoción',
                                'promocion_id': promo_actual.get('promocion_id', ''),
                                'promocion_nombre': promo_actual.get('promocion_nombre', ''),
                                'precio_original': precio_normal
                            }
                            
                            # Agregar al carrito correcto
                            if st.session_state.orden_editar:
                                st.session_state.orden_editar['items'].append(nuevo_item)
                                st.session_state.orden_editar['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_editar['items'])
                            else:
                                st.session_state.orden_actual['items'].append(nuevo_item)
                                st.session_state.orden_actual['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_actual['items'])
                            
                            # Limpiar desplegable
                            st.session_state.plato_desplegado = None
                            st.session_state.plato_seleccionado = None
                            st.session_state.cantidad_desplegado = 1
                            st.session_state.comentarios_desplegado = ""
                            
                            st.success(f"🎉 ¡{nuevo_item['nombre']} agregado con descuento!")
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("❌ Cancelar", key="cancel_promo_desplegado"):
                            st.session_state.plato_desplegado = None
                            st.session_state.plato_seleccionado = None
                            st.session_state.cantidad_desplegado = 1
                            st.session_state.comentarios_desplegado = ""
                            st.rerun()
                    
                    st.markdown("---")
            
            # --- Modal para Selección de Cantidad y Comentarios ---
            if st.session_state.get('show_modal', False) and st.session_state.get('plato_modal'):
                plato_modal = st.session_state.plato_modal
                
                with st.container():
                    st.markdown("---")
                    
                    # Verificar si es una promoción
                    es_promocion = plato_modal.get('es_promocion', False)
                    
                    if es_promocion:
                        st.subheader(f"🎉 {plato_modal.get('descripcion', 'Promoción Seleccionada')}")
                        st.success(f"🔥 **¡OFERTA ESPECIAL!** - {plato_modal.get('promocion_nombre', 'Promoción limitada')}")
                    else:
                        st.subheader(f"🍽️ {plato_modal.get('descripcion', 'Plato Seleccionado')}")
                    
                    precio_normal = plato_modal.get('precio_normal', 0)
                    precio_oferta = plato_modal.get('precio_oferta')
                    precio_final = precio_oferta if precio_oferta and precio_oferta < precio_normal else precio_normal
                    
                    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                    
                    with col_btn1:
                        cantidad = st.number_input("Cantidad:", min_value=1, value=1, step=1, key="modal_quantity")
                    
                    with col_btn2:
                        comentarios = st.text_input("Comentarios/Notas:", key="modal_comments")
                        
                        if st.button("✅ Agregar al Carrito", type="primary", key="add_to_cart_modal"):
                            # Determinar tipo de precio y datos del item
                            if es_promocion:
                                tipo_precio = 'Promoción'
                                # Para promociones, usar el plato_id original, no el de la promoción
                                plato_id_real = plato_modal.get('_id', '')
                                nombre_item = plato_modal.get('descripcion', 'Promoción')
                                precio_a_usar = precio_final
                            else:
                                tipo_precio = 'Oferta' if precio_oferta and precio_oferta < precio_normal else 'Normal'
                                plato_id_real = plato_modal['_id']
                                nombre_item = plato_modal.get('descripcion', 'Plato')
                                precio_a_usar = precio_final
                            
                            nuevo_item = {
                                'plato_id': plato_id_real,
                                'nombre': nombre_item,
                                'precio_unitario': precio_a_usar,
                                'cantidad': cantidad,
                                'comentarios': comentarios,
                                'tipo_precio': tipo_precio
                            }
                            
                            # Agregar información adicional si es promoción
                            if es_promocion:
                                nuevo_item['promocion_id'] = plato_modal.get('promocion_id', '')
                                nuevo_item['promocion_nombre'] = plato_modal.get('promocion_nombre', '')
                                nuevo_item['precio_original'] = precio_normal
                            
                            # Add to the correct order (either editing or new)
                            if st.session_state.orden_editar:
                                st.session_state.orden_editar['items'].append(nuevo_item)
                                st.session_state.orden_editar['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_editar['items'])
                            else:
                                st.session_state.orden_actual['items'].append(nuevo_item)
                                st.session_state.orden_actual['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in st.session_state.orden_actual['items'])
                            
                            st.session_state.show_modal = False
                            st.session_state.plato_modal = None
                            st.success(f"✅ {nuevo_item['nombre']} agregado al carrito!")
                            st.rerun()
                        
                        if st.button("❌ Cancelar", key="cancel_modal"):
                            st.session_state.show_modal = False
                            st.session_state.plato_modal = None
                            st.rerun()
                        
                    with col_btn3:
                        total_modal = precio_final * cantidad
                        st.metric("Total", f"${total_modal:.2f}")
                    
                    st.markdown("---")

        # --- Cart Section (Right Column) ---
        with col_cart:
            st.subheader("🛒 Carrito de Compras")
            
            # Determinar qué items mostrar
            if st.session_state.orden_editar:
                items_to_display = st.session_state.orden_editar['items']
                order_total_key = 'orden_editar'
                current_order_display = st.session_state.orden_editar
                st.info(f"📝 Editando Orden #{current_order_display.get('numero_orden', 'N/A')}")
            else:
                items_to_display = st.session_state.orden_actual['items']
                order_total_key = 'orden_actual'
                current_order_display = st.session_state.orden_actual
                st.info(f"🆕 Nueva Orden #{current_order_display.get('numero_orden', 'N/A')}")
            
            # Definir mesas para uso en la sección del carrito
            mesas_cart = {m['_id']: m for m in couchdb_utils.get_documents_by_partition(db, "mesas")}
            
            if not items_to_display:
                st.info("El carrito está vacío. Selecciona platos del menú para agregar.")
            else:
                # Mostrar items en el carrito
                for idx, item in enumerate(items_to_display):
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; margin: 5px 0; background-color: #f9f9f9;">
                            <strong>{item['nombre']}</strong><br>
                            <small>💰 ${item['precio_unitario']:.2f} x {item['cantidad']} = ${item['precio_unitario'] * item['cantidad']:.2f}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if item.get('comentarios'):
                            st.caption(f"💬 {item['comentarios']}")
                        
                        # Botones de cantidad y eliminar
                        col_qty, col_remove = st.columns([2, 1])
                        with col_qty:
                            new_quantity = st.number_input(
                                "Cant.", 
                                min_value=1, 
                                value=item['cantidad'], 
                                key=f"qty_{order_total_key}_{idx}",
                                label_visibility="collapsed"
                            )
                            if new_quantity != item['cantidad']:
                                items_to_display[idx]['cantidad'] = new_quantity
                                # Actualizar total
                                if st.session_state.orden_editar:
                                    st.session_state.orden_editar['total'] = sum(i['precio_unitario'] * i['cantidad'] for i in st.session_state.orden_editar['items'])
                                else:
                                    st.session_state.orden_actual['total'] = sum(i['precio_unitario'] * i['cantidad'] for i in st.session_state.orden_actual['items'])
                                st.rerun()
                        
                        with col_remove:
                            if st.button("🗑️", key=f"remove_{order_total_key}_{idx}", help="Eliminar item"):
                                items_to_display.pop(idx)
                                # Actualizar total después de eliminar
                                if st.session_state.orden_editar:
                                    st.session_state.orden_editar['total'] = sum(i['precio_unitario'] * i['cantidad'] for i in st.session_state.orden_editar['items'])
                                else:
                                    st.session_state.orden_actual['total'] = sum(i['precio_unitario'] * i['cantidad'] for i in st.session_state.orden_actual['items'])
                                st.rerun()
                
                st.markdown("---")
                
                # Resumen del pedido
                current_subtotal = sum(item['precio_unitario'] * item['cantidad'] for item in items_to_display)
                current_total_items = sum(item['cantidad'] for item in items_to_display)
                
                st.markdown(f"""
                <div style="background-color: #e8f4f8; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <h4>📊 Resumen</h4>
                    <p><strong>Items:</strong> {current_total_items}</p>
                    <p><strong>Total:</strong> ${current_subtotal:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Comentarios generales
                current_comments = st.text_area(
                    "💬 Comentarios generales:", 
                    value=current_order_display.get('comentarios', ''),
                    key=f"order_comments_{order_total_key}",
                    height=80
                )
                current_order_display['comentarios'] = current_comments
                
                # Botones de acción
                if st.button("🚀 Guardar y Enviar Orden", type="primary", use_container_width=True, key=f"send_order_{order_total_key}"):
                    if not items_to_display:
                        st.error("¡El carrito está vacío!")
                    else:
                        # Validar mesa y mesero
                        if st.session_state.orden_editar:
                            mesa_valida = current_order_display.get('mesa_id') is not None
                            mesero_valido = current_order_display.get('mesero_id') is not None
                        else:
                            mesa_valida = current_order_display.get('mesa') is not None
                            mesero_valido = current_order_display.get('mesero') is not None
                        
                        if not mesa_valida or not mesero_valido:
                            st.error("Debes seleccionar mesa y mesero.")
                        else:
                            if st.session_state.orden_editar:
                                # Actualizar orden existente
                                order_to_save = st.session_state.orden_editar
                                order_to_save['items'] = items_to_display
                                order_to_save['comentarios'] = current_comments
                                order_to_save['total'] = current_subtotal
                                order_to_save['fecha_ultima_modificacion'] = datetime.now(timezone.utc).isoformat()
                                message_success = f"✅ Orden #{order_to_save['numero_orden']} actualizada!"
                            else:
                                # Crear nueva orden
                                order_to_save = {
                                    "_id": f"ordenes:{str(uuid.uuid4())}",
                                    "type": "ordenes",
                                    "numero_orden": st.session_state.orden_actual['numero_orden'],
                                    "mesa_id": st.session_state.orden_actual['mesa'],
                                    "mesero_id": st.session_state.orden_actual['mesero'],
                                    "items": items_to_display,
                                    "comentarios": current_comments,
                                    "estado": "pendiente",
                                    "fecha_creacion": datetime.now(timezone.utc).isoformat(),
                                    "total": current_subtotal
                                }
                                message_success = f"✅ Orden #{order_to_save['numero_orden']} enviada!"
                            
                            try:
                                db.save(order_to_save)
                                st.success(message_success)
                                logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                couchdb_utils.log_action(db, logged_in_user, f"Orden #{order_to_save['numero_orden']} guardada")
                                
                                # Reset and redirect
                                if st.session_state.orden_editar:
                                    # If we were editing, go back to ordenes_activas
                                    st.session_state.orden_editar = None
                                    st.session_state.plato_seleccionado = None
                                    st.balloons()
                                    st.switch_page("pages/ordenes_activas.py")
                                else:
                                    # If it was a new order, reset everything
                                    st.session_state.orden_actual = {
                                        'mesa': None,
                                        'mesero': None,
                                        'items': [],
                                        'comentarios': '',
                                        'numero_orden': couchdb_utils.get_next_order_number(db)
                                    }
                                    st.session_state.orden_editar = None
                                    st.session_state.plato_seleccionado = None
                                    st.balloons()
                                    st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                # Botones adicionales
                col_cancel, col_clear = st.columns(2)
                with col_cancel:
                    if st.session_state.orden_editar:
                        if st.button("↩️ Cancelar Edición", use_container_width=True):
                            st.session_state.orden_editar = None
                            st.switch_page("pages/ordenes_activas.py")
                
                with col_clear:
                    if not st.session_state.orden_editar:
                        if st.button("♻️ Limpiar Carrito", use_container_width=True):
                            st.session_state.orden_actual['items'] = []
                            st.session_state.orden_actual['comentarios'] = ''
                            st.session_state.orden_actual['total'] = 0
                            st.rerun()
            
            # --- Quick Link ---
            st.markdown("---")
            st.page_link("pages/ordenes_activas.py", label="📋 Ver Órdenes Activas", icon="🍽️")

    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesión para acceder a esta página.")
