# pages/menu_clientes.py
import streamlit as st
import couchdb_utils
from datetime import datetime, timezone

# --- Configuración Inicial ---
st.set_page_config(layout="wide", page_title="Menú Tia Juana - Para Clientes", page_icon="../assets/LOGO.png")

# --- Estilos CSS Atractivos para Clientes ---
st.markdown("""
<style>
    /* Fondo general */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Título principal */
    .main-title {
        text-align: center;
        background: linear-gradient(45deg, #ff6b9d, #ffa726);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3.5em !important;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    /* Subtítulos de sección */
    .section-title {
        background: linear-gradient(45deg, #ff9500, #ffb347);
        color: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        font-size: 1.8em;
        font-weight: bold;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(255, 149, 0, 0.3);
    }
    
    /* Tarjetas de categoría */
    .category-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 20px;
        margin: 15px 5px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: 2px solid transparent;
        transition: all 0.3s ease;
        color: #333;
    }
    
    .category-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.2);
    }
    
    /* Tarjetas de platos */
    .dish-card {
        background: linear-gradient(145deg, #ffffff, #f0f0f0);
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        border-left: 5px solid #ff9500;
        transition: all 0.3s ease;
        color: #333;
    }
    
    .dish-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        border-left-color: #ff6b9d;
    }
    
    /* Nombres de platos */
    .dish-name {
        font-size: 1.3em;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    
    /* Precios */
    .dish-price {
        font-size: 1.5em;
        font-weight: bold;
        color: #27ae60;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .dish-price-offer {
        font-size: 1.5em;
        font-weight: bold;
        color: #e74c3c;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .dish-price-original {
        font-size: 1.1em;
        color: #95a5a6;
        text-decoration: line-through;
        margin-left: 10px;
    }
    
    /* Promociones especiales */
    .promo-card {
        background: linear-gradient(135deg, #ff6b9d 0%, #ff8a9b 100%);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 5px;
        box-shadow: 0 8px 25px rgba(255, 107, 157, 0.4);
        color: white;
        text-align: center;
        animation: promo-pulse 2s ease-in-out infinite alternate;
        position: relative;
        overflow: hidden;
    }
    
    .promo-card::before {
        content: '🎉';
        position: absolute;
        top: 10px;
        right: 15px;
        font-size: 2em;
        opacity: 0.7;
    }
    
    @keyframes promo-pulse {
        0% { 
            transform: scale(1);
            box-shadow: 0 8px 25px rgba(255, 107, 157, 0.4);
        }
        100% { 
            transform: scale(1.02);
            box-shadow: 0 12px 35px rgba(255, 107, 157, 0.6);
        }
    }
    
    /* Tiempo restante de promoción */
    .promo-time {
        background: rgba(255, 255, 255, 0.2);
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: bold;
        margin-top: 10px;
        display: inline-block;
    }
    
    /* Botones de categoría */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 15px 25px !important;
        font-size: 1.1em !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Ocultar elementos innecesarios */
    .stDeployButton {display:none;}
    footer {display:none;}
    .stDecoration {display:none;}
</style>
""", unsafe_allow_html=True)

# --- Funciones auxiliares ---
def get_activos(docs):
    """Filtra documentos activos"""
    return [doc for doc in docs if doc.get('activo', 0) == 1]

def get_menu_color(menu_name):
    """Obtiene color por categoría de menú"""
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

def obtener_promociones_activas_clientes():
    """Obtiene promociones activas para mostrar a clientes"""
    try:
        db = couchdb_utils.get_database_instance()
        if not db:
            return []
            
        promociones = couchdb_utils.get_documents_by_partition(db, "promociones")
        ahora = datetime.now(timezone.utc)
        
        promociones_activas = []
        for promo in promociones:
            if (promo.get('estado') == 'activa' and 
                promo.get('activo', True)):
                
                # Verificar que aún esté dentro del tiempo válido
                try:
                    fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                    if ahora <= fecha_fin:
                        promociones_activas.append(promo)
                except:
                    continue
        
        return promociones_activas
    except Exception:
        return []

def verificar_promocion_activa(plato_id):
    """Verifica si el plato tiene una promoción temporal activa y devuelve info completa"""
    try:
        db = couchdb_utils.get_database_instance()
        if not db:
            return None
            
        promociones = couchdb_utils.get_documents_by_partition(db, "promociones")
        platos = couchdb_utils.get_documents_by_partition(db, "platos")
        ahora = datetime.now(timezone.utc)
        
        # Buscar el plato para obtener información adicional
        plato_actual = None
        for plato in platos:
            if plato['_id'] == plato_id:
                plato_actual = plato
                break
        
        if not plato_actual:
            return None
        
        # 1. Verificar si el plato tiene fecha de fin de oferta directamente
        if plato_actual.get('fecha_fin_oferta'):
            try:
                fecha_fin = datetime.fromisoformat(plato_actual.get('fecha_fin_oferta', '').replace('Z', '+00:00'))
                if ahora <= fecha_fin:
                    tiempo_restante = fecha_fin - ahora
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
                    
                    precio_promo = plato_actual.get('precio_oferta', 0)
                    return {
                        "tiene_promocion": True, 
                        "tiempo_restante": tiempo_texto,
                        "precio_promocion": precio_promo
                    }
            except:
                pass
        
        # 2. Buscar en promociones por diferentes criterios
        plato_nombre = plato_actual.get('descripcion', '')
        
        for promo in promociones:
            if (promo.get('estado') == 'activa' and 
                promo.get('activo', True)):
                
                # Verificar múltiples criterios de coincidencia
                coincide = False
                
                # Por plato_id directo
                if promo.get('plato_id') == plato_id:
                    coincide = True
                # Por nombre_producto exacto
                elif promo.get('nombre_producto', '').lower() == plato_nombre.lower():
                    coincide = True
                # Por nombre_producto que contenga el nombre del plato
                elif plato_nombre and plato_nombre.lower() in promo.get('nombre_producto', '').lower():
                    coincide = True
                # Por plato_id que contenga parte del ID
                elif plato_id and str(plato_id) in str(promo.get('plato_id', '')):
                    coincide = True
                
                if coincide:
                    try:
                        fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                        if ahora <= fecha_fin:
                            tiempo_restante = fecha_fin - ahora
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
                            
                            # Usar el precio de la promoción, no del plato
                            precio_promo = promo.get('precio_promocion', 0)
                            return {
                                "tiene_promocion": True, 
                                "tiempo_restante": tiempo_texto,
                                "precio_promocion": precio_promo
                            }
                    except:
                        continue
        
        return {"tiene_promocion": False, "tiempo_restante": None, "precio_promocion": None}
    except Exception:
        return {"tiene_promocion": False, "tiempo_restante": None, "precio_promocion": None}

# --- Encabezado Principal ---
st.markdown('<h1 class="main-title">🍽️ Menú Tia Juana</h1>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; font-size: 1.3em; margin-bottom: 30px; color: #ffffff; font-weight: bold; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);">¡Descubre nuestros deliciosos platos y bebidas!</div>', unsafe_allow_html=True)

# --- Conectar a la base de datos (sin necesidad de login) ---
try:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # --- Obtener datos del menú ---
        todos_menus = get_activos(couchdb_utils.get_documents_by_partition(db, "menus"))
        platos = get_activos(couchdb_utils.get_documents_by_partition(db, "platos"))
        
        if not todos_menus or not platos:
            st.error("🚫 No hay menús disponibles en este momento.")
        else:
            # Crear diccionarios para acceso rápido
            menu_dict = {menu['_id']: menu for menu in todos_menus}
            
            # Organizar platos por menú
            platos_por_menu = {}
            for plato in platos:
                menu_id = plato.get('id_menu')
                if menu_id in menu_dict:
                    if menu_id not in platos_por_menu:
                        platos_por_menu[menu_id] = []
                    platos_por_menu[menu_id].append(plato)
            
            # --- Mostrar promociones especiales primero ---
            promociones_activas = obtener_promociones_activas_clientes()
            
            if promociones_activas:
                st.markdown('<div class="section-title">🎉 ¡PROMOCIONES ESPECIALES! ⭐</div>', unsafe_allow_html=True)
                
                # Mostrar promociones en grid
                cols_promo = st.columns(min(len(promociones_activas), 3))
                
                for idx, promo in enumerate(promociones_activas):
                    with cols_promo[idx % 3]:
                        # Calcular tiempo restante
                        try:
                            fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                            tiempo_restante = fecha_fin - datetime.now(timezone.utc)
                            total_seconds = max(0, tiempo_restante.total_seconds())
                            
                            if total_seconds < 3600:  # Menos de 1 hora
                                minutos_restantes = int(total_seconds // 60)
                                tiempo_texto = f"{minutos_restantes} min restantes"
                            else:
                                horas = int(total_seconds // 3600)
                                minutos = int((total_seconds % 3600) // 60)
                                if minutos > 0:
                                    tiempo_texto = f"{horas}h {minutos}min restantes"
                                else:
                                    tiempo_texto = f"{horas}h restantes"
                        except:
                            tiempo_texto = "¡Por tiempo limitado!"
                        
                        # Calcular descuento
                        precio_original = promo.get('precio_original', 0)
                        precio_promo = promo.get('precio_promocion', 0)
                        descuento = int(promo.get('descuento_porcentaje', 0))
                        
                        st.markdown(f"""
                        <div class="promo-card">
                            <h3 style="margin: 0; font-size: 1.4em;">{promo.get('nombre_producto', 'Promoción')}</h3>
                            <div style="font-size: 2em; font-weight: bold; margin: 10px 0;">-{descuento}% OFF</div>
                            <div style="font-size: 1.3em;">
                                <span style="color: #2ecc71; font-weight: bold;">${precio_promo:.2f}</span>
                                <span style="text-decoration: line-through; opacity: 0.7; margin-left: 10px;">${precio_original:.2f}</span>
                            </div>
                            <div class="promo-time">⏰ {tiempo_texto}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
            
            # --- Categorías de Bebidas ---
            st.markdown('<div class="section-title">🍹 BEBIDAS</div>', unsafe_allow_html=True)
            
            bebidas_menus = [m for m in todos_menus if m.get('nombre', '').lower() in 
                           ['cocteles', 'bebidas naturales', 'bebidas sin alcohol', 'cerveza', 'botellas', 'shots']]
            
            if bebidas_menus:
                # Botones de categorías de bebidas
                cols_bebidas = st.columns(min(len(bebidas_menus), 4))
                for idx, menu in enumerate(bebidas_menus):
                    with cols_bebidas[idx % 4]:
                        emoji_bebida = "🍹"
                        nombre_menu = menu.get('nombre', 'Sin nombre')
                        if st.button(
                            f"{emoji_bebida} {nombre_menu}",
                            key=f"menu_bebidas_cliente_{menu['_id']}",
                            help=f"Ver {nombre_menu}",
                            use_container_width=True
                        ):
                            # Cerrar todos los otros menús antes de abrir el seleccionado
                            for all_menu in todos_menus:
                                if all_menu['_id'] != menu['_id']:
                                    st.session_state[f"show_menu_cliente_{all_menu['_id']}"] = False
                            
                            # Toggle del menú seleccionado
                            st.session_state[f"show_menu_cliente_{menu['_id']}"] = not st.session_state.get(f"show_menu_cliente_{menu['_id']}", False)
                
                # Mostrar platos de bebidas
                for menu in bebidas_menus:
                    if st.session_state.get(f"show_menu_cliente_{menu['_id']}", False):
                        platos_menu = platos_por_menu.get(menu['_id'], [])
                        if platos_menu:
                            color = get_menu_color(menu.get('nombre', ''))
                            nombre_menu = menu.get('nombre', '').upper()
                            st.markdown(f"""
                            <div class="category-card">
                                <h3 style="text-align: center; color: {color}; margin-bottom: 20px;">
                                    🍹 {nombre_menu}
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            cols_platos = st.columns(3)
                            for j, plato in enumerate(platos_menu):
                                with cols_platos[j % 3]:
                                    precio_normal = plato.get('precio_normal', 0)
                                    precio_oferta = plato.get('precio_oferta')
                                    nombre_plato = plato.get('descripcion', 'Sin nombre')
                                    
                                    # Verificar si realmente tiene una promoción activa
                                    promo_info = verificar_promocion_activa(plato['_id'])
                                    
                                    # Solo mostrar precio relámpago si hay promoción activa
                                    if promo_info and promo_info.get('tiene_promocion', False):
                                        precio_promocion = promo_info.get('precio_promocion', 0)
                                        
                                        precio_html = '<div style="margin-bottom: 5px;">'
                                        precio_html += '<span style="font-size: 0.9em; color: #e74c3c; font-weight: bold;">⚡ Precio Relámpago:</span><br>'
                                        precio_html += f'<span class="dish-price-offer">${precio_promocion:.2f}</span>'
                                        
                                        # Agregar tiempo restante si existe
                                        if promo_info.get('tiempo_restante'):
                                            precio_html += f'<br><span style="font-size: 0.75em; color: #ff6b35; font-weight: bold;">⏰ {promo_info["tiempo_restante"]}</span>'
                                        
                                        precio_html += '</div>'
                                        precio_html += '<div>'
                                        precio_html += '<span style="font-size: 0.8em; color: #95a5a6;">Precio Normal:</span> '
                                        precio_html += f'<span class="dish-price-original">${precio_normal:.2f}</span>'
                                        precio_html += '</div>'
                                    else:
                                        # Mostrar solo precio normal si no hay promoción activa
                                        precio_actual = precio_oferta if precio_oferta and precio_oferta < precio_normal else precio_normal
                                        precio_html = '<div>'
                                        precio_html += '<span style="font-size: 0.9em; color: #27ae60; font-weight: bold;">💰 Precio Normal:</span><br>'
                                        precio_html += f'<span class="dish-price">${precio_actual:.2f}</span>'
                                        precio_html += '</div>'
                                    
                                    tarjeta_html = f'<div class="dish-card"><div class="dish-name">{nombre_plato}</div>{precio_html}</div>'
                                    st.markdown(tarjeta_html, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # --- Categorías de Comida ---
            st.markdown('<div class="section-title">🍽️ COMIDA</div>', unsafe_allow_html=True)
            
            comida_menus = [m for m in todos_menus if m.get('nombre', '').lower() in 
                          ['comida mexicana', 'platos fuertes', 'boquitas']]
            
            if comida_menus:
                # Botones de categorías de comida
                cols_comida = st.columns(min(len(comida_menus), 3))
                for idx, menu in enumerate(comida_menus):
                    with cols_comida[idx % 3]:
                        emoji_comida = "🍽️"
                        nombre_menu = menu.get('nombre', 'Sin nombre')
                        if st.button(
                            f"{emoji_comida} {nombre_menu}",
                            key=f"menu_comida_cliente_{menu['_id']}",
                            help=f"Ver {nombre_menu}",
                            use_container_width=True
                        ):
                            # Cerrar todos los otros menús antes de abrir el seleccionado
                            for all_menu in todos_menus:
                                if all_menu['_id'] != menu['_id']:
                                    st.session_state[f"show_menu_cliente_{all_menu['_id']}"] = False
                            
                            # Toggle del menú seleccionado
                            st.session_state[f"show_menu_cliente_{menu['_id']}"] = not st.session_state.get(f"show_menu_cliente_{menu['_id']}", False)
                
                # Mostrar platos de comida
                for menu in comida_menus:
                    if st.session_state.get(f"show_menu_cliente_{menu['_id']}", False):
                        platos_menu = platos_por_menu.get(menu['_id'], [])
                        if platos_menu:
                            color = get_menu_color(menu.get('nombre', ''))
                            nombre_menu = menu.get('nombre', '').upper()
                            st.markdown(f"""
                            <div class="category-card">
                                <h3 style="text-align: center; color: {color}; margin-bottom: 20px;">
                                    🍽️ {nombre_menu}
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            cols_platos = st.columns(3)
                            for j, plato in enumerate(platos_menu):
                                with cols_platos[j % 3]:
                                    precio_normal = plato.get('precio_normal', 0)
                                    precio_oferta = plato.get('precio_oferta')
                                    nombre_plato = plato.get('descripcion', 'Sin nombre')
                                    
                                    # Verificar si realmente tiene una promoción activa
                                    promo_info = verificar_promocion_activa(plato['_id'])
                                    
                                    # Solo mostrar precio relámpago si hay promoción activa
                                    if promo_info and promo_info.get('tiene_promocion', False):
                                        precio_promocion = promo_info.get('precio_promocion', 0)
                                        
                                        precio_html = '<div style="margin-bottom: 5px;">'
                                        precio_html += '<span style="font-size: 0.9em; color: #e74c3c; font-weight: bold;">⚡ Precio Relámpago:</span><br>'
                                        precio_html += f'<span class="dish-price-offer">${precio_promocion:.2f}</span>'
                                        
                                        # Agregar tiempo restante si existe
                                        if promo_info.get('tiempo_restante'):
                                            precio_html += f'<br><span style="font-size: 0.75em; color: #ff6b35; font-weight: bold;">⏰ {promo_info["tiempo_restante"]}</span>'
                                        
                                        precio_html += '</div>'
                                        precio_html += '<div>'
                                        precio_html += '<span style="font-size: 0.8em; color: #95a5a6;">Precio Normal:</span> '
                                        precio_html += f'<span class="dish-price-original">${precio_normal:.2f}</span>'
                                        precio_html += '</div>'
                                    else:
                                        # Mostrar solo precio normal si no hay promoción activa
                                        precio_actual = precio_oferta if precio_oferta and precio_oferta < precio_normal else precio_normal
                                        precio_html = '<div>'
                                        precio_html += '<span style="font-size: 0.9em; color: #27ae60; font-weight: bold;">💰 Precio Normal:</span><br>'
                                        precio_html += f'<span class="dish-price">${precio_actual:.2f}</span>'
                                        precio_html += '</div>'
                                    
                                    tarjeta_html = f'<div class="dish-card"><div class="dish-name">{nombre_plato}</div>{precio_html}</div>'
                                    st.markdown(tarjeta_html, unsafe_allow_html=True)
            
            # --- Pie de página ---
            st.markdown("---")
            st.markdown("""
            <div style="text-align: center; padding: 30px; background: rgba(255, 255, 255, 0.1); border-radius: 15px; margin: 20px 0;">
                <h3 style="color: #ecf0f1;">🏪 Tia Juana</h3>
                <p style="color: #bdc3c7; font-size: 1.1em;">¡Gracias por visitarnos!</p>
                <p style="color: #95a5a6;">Para realizar tu pedido, consulta con nuestros meseros</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.error("🚫 No se pudo conectar a la base de datos. Intenta más tarde.")
        
except Exception as e:
    st.error(f"🚫 Error al cargar el menú: {str(e)}")