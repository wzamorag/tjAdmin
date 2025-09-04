# pages/bar.py
import streamlit as st
from datetime import datetime, timezone
import couchdb_utils
import os
import time

# Obtener la ruta relativa de la página
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Llama a la función de login/menú/validación
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Sistema de Despacho de Bar", page_icon="../assets/LOGO.png")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    .drink-card {
        border: 2px solid #ff6b6b;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .urgent-card {
        border-color: #dc3545 !important;
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%) !important;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    @keyframes blink {
        0% { opacity: 1; background-color: #ffd700; transform: scale(1); }
        25% { opacity: 0.7; background-color: #ff6b6b; transform: scale(1.05); }
        50% { opacity: 1; background-color: #ffd700; transform: scale(1); }
        75% { opacity: 0.7; background-color: #ff6b6b; transform: scale(1.05); }
        100% { opacity: 1; background-color: #ffd700; transform: scale(1); }
    }
    
    .new-item {
        animation: blink 1s ease-in-out 4;
        border: 3px solid #ffd700 !important;
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.6) !important;
    }
    
    .time-counter {
        font-size: 1.5rem;
        font-weight: bold;
        color: #fff;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    .dispatch-btn {
        background: linear-gradient(45deg, #28a745, #20c997);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .dispatch-btn:hover {
        background: linear-gradient(45deg, #218838, #1ea672);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # Inicializar session state para auto-refresh y tracking de items nuevos
        if 'bar_last_refresh' not in st.session_state:
            st.session_state.bar_last_refresh = time.time()
        
        if 'bar_previous_items' not in st.session_state:
            st.session_state.bar_previous_items = set()
        
        if 'bar_new_items' not in st.session_state:
            st.session_state.bar_new_items = set()
        
        if 'bar_new_items_timestamp' not in st.session_state:
            st.session_state.bar_new_items_timestamp = {}
        
        # Auto-refresh cada 60 segundos
        current_time = time.time()
        if current_time - st.session_state.bar_last_refresh >= 60:
            st.session_state.bar_last_refresh = current_time
            st.rerun()
        # Función para obtener bebidas de los platos
        def obtener_bebidas():
            platos = couchdb_utils.get_documents_by_partition(db, "platos")
            menus = couchdb_utils.get_documents_by_partition(db, "menu")
            
            # Encontrar el menú "bar"
            menu_bar = None
            for menu in menus:
                if menu.get('descripcion', '').lower() == 'bar':
                    menu_bar = menu
                    break
            
            bebidas = []
            
            for plato in platos:
                nombre = plato.get('descripcion', '')
                categoria = plato.get('categoria', '')
                menu_id = plato.get('menu_id', '')
                
                # Métodos de identificación (en orden de prioridad):
                # 1. Por menú "bar" (PRIORITARIO)
                es_bebida_menu = False
                if menu_bar and menu_id == menu_bar.get('_id'):
                    es_bebida_menu = True
                
                # 2. Por categoría específica
                es_bebida_categoria = any(cat in categoria.lower() for cat in ['bar', 'bebida', 'bebidas', 'drink'])
                
                # 3. Por palabras clave (fallback)
                keywords_bebidas = [
                    'bebida', 'jugo', 'agua', 'gaseosa', 'refresco', 'cocktail', 
                    'cerveza', 'licor', 'café', 'té', 'smoothie', 'cola', 'pepsi',
                    'cuba', 'libre', 'mojito', 'piña', 'colada', 'margarita',
                    'daiquiri', 'whisky', 'ron', 'vodka', 'tequila', 'ginebra',
                    'sangria', 'vino', 'champagne', 'limonada', 'naranjada',
                    'soda', 'sprite', 'fanta', 'cocacola', 'energética', 'isotónica',
                    'pilsener', 'pilsen', 'beer', 'lager'
                ]
                es_bebida_keyword = any(keyword in nombre.lower() for keyword in keywords_bebidas)
                
                # Es bebida si cumple cualquiera de los criterios
                es_bebida = es_bebida_menu or es_bebida_categoria or es_bebida_keyword
                
                if es_bebida:
                    bebidas.append(plato['_id'])
                    
                    # Determinar método de detección
                    if es_bebida_menu:
                        metodo = 'Menú Bar'
                    elif es_bebida_categoria:
                        metodo = 'Categoría'
                    else:
                        metodo = 'Palabra clave'
                    
            
            return bebidas
        
        # Función para calcular tiempo transcurrido
        def calcular_tiempo_transcurrido(fecha_creacion):
            try:
                fecha_orden = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                ahora = datetime.now(timezone.utc)
                diferencia = ahora - fecha_orden
                
                minutos = int(diferencia.total_seconds() / 60)
                if minutos < 60:
                    return f"{minutos} min", minutos
                else:
                    horas = minutos // 60
                    min_restantes = minutos % 60
                    return f"{horas}h {min_restantes}m", minutos
            except:
                return "0 min", 0
        
        # Función para despachar bebida
        def despachar_bebida(orden_id, item_id):
            try:
                # Obtener la orden actual
                orden = db.get(orden_id)
                item_despachado = None
                
                # Buscar el item específico y marcarlo como despachado
                for idx, item in enumerate(orden.get('items', [])):
                    # Excluir productos anulados
                    if item.get('anulado', False):
                        continue
                        
                    # Crear ID temporal si no existe
                    temp_id = item.get('id') or f"{orden_id}_{idx}"
                    
                    if temp_id == item_id:
                        item['despachado_bar'] = True
                        item['fecha_despacho_bar'] = datetime.now(timezone.utc).isoformat()
                        item['usuario_despacho_bar'] = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        item['id'] = temp_id  # Asegurar que tenga ID
                        item_despachado = item
                        break
                
                if item_despachado is None:
                    st.error(f"No se encontró el item con ID: {item_id}")
                    return False
                
                # Guardar la orden actualizada
                db.save(orden)
                
                # Log de la acción
                logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                couchdb_utils.log_action(
                    db, 
                    logged_in_user, 
                    f"Bebida despachada - Orden #{orden.get('numero_orden')} - Item: {item_despachado.get('nombre', 'N/A')}"
                )
                
                return True
            except Exception as e:
                st.error(f"Error al despachar bebida: {str(e)}")
                return False
        
        # TÍTULO PRINCIPAL
        st.title("🍹 Sistema de Despacho de Bar")
        st.markdown("---")
        
        # Obtener todas las órdenes pendientes y en cobro
        ordenes = couchdb_utils.get_documents_by_partition(db, "ordenes")
        ordenes_activas = [orden for orden in ordenes if orden.get('estado') in ['pendiente', 'en_cobro']]
        
        # Obtener lista de IDs de bebidas
        bebidas_ids = obtener_bebidas()
        
        # Filtrar órdenes que tienen bebidas (pendientes y despachadas)
        ordenes_con_bebidas = []
        ordenes_con_bebidas_despachadas = []
        
        for orden in ordenes_activas:
            bebidas_pendientes = []
            bebidas_despachadas = []
            
            for idx, item in enumerate(orden.get('items', [])):
                # Excluir productos anulados del despacho de bar
                if item.get('anulado', False):
                    continue
                
                if item.get('plato_id') in bebidas_ids:
                    # Asegurar que el item tenga un ID único
                    if not item.get('id'):
                        item['id'] = f"{orden['_id']}_{idx}"
                    
                    if item.get('despachado_bar', False):
                        bebidas_despachadas.append(item)
                    else:
                        bebidas_pendientes.append(item)
            
            if bebidas_pendientes:
                orden['bebidas_pendientes'] = bebidas_pendientes
                ordenes_con_bebidas.append(orden)
                
            if bebidas_despachadas:
                orden['bebidas_despachadas'] = bebidas_despachadas
                ordenes_con_bebidas_despachadas.append(orden)
        
        # ESTADÍSTICAS EN TIEMPO REAL
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{len(ordenes_con_bebidas)}</h3>
                <p>Órdenes con Bebidas</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats2:
            total_bebidas = sum(len(orden['bebidas_pendientes']) for orden in ordenes_con_bebidas)
            st.markdown(f"""
            <div class="stats-card">
                <h3>{total_bebidas}</h3>
                <p>Bebidas Pendientes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats3:
            if ordenes_con_bebidas:
                tiempos = [calcular_tiempo_transcurrido(orden.get('fecha_creacion', ''))[1] for orden in ordenes_con_bebidas]
                tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
                st.markdown(f"""
                <div class="stats-card">
                    <h3>{int(tiempo_promedio)} min</h3>
                    <p>Tiempo Promedio</p>
                </div>
                """, unsafe_allow_html=True)
        
        
        st.markdown("---")
        
        # MOSTRAR ÓRDENES CON BEBIDAS
        if ordenes_con_bebidas:
            st.subheader("🥤 Bebidas Pendientes de Despacho")
            
            # Ordenar por tiempo de creación (más antiguas primero)
            ordenes_con_bebidas.sort(key=lambda x: x.get('fecha_creacion', ''))
            
            # Crear lista de todas las bebidas pendientes con número correlativo
            todas_las_bebidas = []
            current_items = set()
            
            for orden in ordenes_con_bebidas:
                for idx, bebida in enumerate(orden['bebidas_pendientes']):
                    # Crear un ID único para el item
                    item_id = bebida.get('id') or f"{orden['_id']}_{idx}"
                    bebida['id'] = item_id  # Asegurar que tenga ID
                    current_items.add(item_id)
                    
                    # Calcular tiempo para esta bebida específica
                    tiempo_str, minutos = calcular_tiempo_transcurrido(orden.get('fecha_creacion', ''))
                    es_urgente = minutos > 15
                    
                    # Extraer número de mesa
                    mesa_id = orden.get('mesa_id', 'N/A')
                    mesa_num = mesa_id.split(':')[-1] if mesa_id and ':' in mesa_id else mesa_id
                    
                    # Verificar si es un item nuevo
                    es_nuevo = item_id not in st.session_state.bar_previous_items
                    if es_nuevo:
                        st.session_state.bar_new_items.add(item_id)
                        st.session_state.bar_new_items_timestamp[item_id] = current_time
                    
                    # Remover items nuevos después de 4 parpadeos (4 segundos)
                    if item_id in st.session_state.bar_new_items_timestamp:
                        if current_time - st.session_state.bar_new_items_timestamp[item_id] > 4:
                            st.session_state.bar_new_items.discard(item_id)
                            st.session_state.bar_new_items_timestamp.pop(item_id, None)
                    
                    todas_las_bebidas.append({
                        'orden': orden,
                        'bebida': bebida,
                        'item_id': item_id,
                        'tiempo_str': tiempo_str,
                        'minutos': minutos,
                        'es_urgente': es_urgente,
                        'mesa_num': mesa_num,
                        'es_nuevo': item_id in st.session_state.bar_new_items
                    })
            
            # Actualizar items anteriores para la próxima comparación
            st.session_state.bar_previous_items = current_items.copy()
            
            # Mostrar bebidas en filas de 4 columnas
            for i in range(0, len(todas_las_bebidas), 4):
                cols = st.columns(4)
                for j in range(4):
                    if i + j < len(todas_las_bebidas):
                        item_data = todas_las_bebidas[i + j]
                        orden = item_data['orden']
                        bebida = item_data['bebida']
                        item_id = item_data['item_id']
                        tiempo_str = item_data['tiempo_str']
                        es_urgente = item_data['es_urgente']
                        mesa_num = item_data['mesa_num']
                        es_nuevo = item_data['es_nuevo']
                        
                        # Número correlativo de llegada
                        numero_llegada = i + j + 1
                        
                        # Determinar la clase CSS
                        if es_nuevo:
                            card_class = "drink-card new-item"
                        elif es_urgente:
                            card_class = "urgent-card"
                        else:
                            card_class = "drink-card"
                        
                        with cols[j]:
                            st.markdown(f"""
                            <div class="{card_class}">
                                <div style="display: flex; align-items: stretch; height: 120px;">
                                    <div style="display: flex; align-items: center; justify-content: center; width: 60px; background: rgba(255,255,255,0.2); border-radius: 10px 0 0 10px; margin-right: 15px;">
                                        <span style="font-size: 48px; font-weight: bold; color: #fff;">{numero_llegada}</span>
                                    </div>
                                    <div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                                        <div>
                                            <div style="font-size: 14px; color: #fff; margin-bottom: 5px;">
                                                🍽️ Orden #{orden.get('numero_orden', 'N/A')} - Mesa {mesa_num}
                                            </div>
                                            <div style="font-size: 16px; font-weight: bold; color: #fff; margin-bottom: 5px;">
                                                🥤 {bebida.get('nombre', 'Bebida')} (x{bebida.get('cantidad', 1)})
                                            </div>
                                        </div>
                                        <div style="font-size: 12px; color: #fff;">
                                            ⏱️ {tiempo_str}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Mostrar comentarios si existen
                            if bebida.get('comentarios'):
                                st.caption(f"💬 {bebida['comentarios']}")
                            
                            # Verificar si el producto tiene solicitud de anulación pendiente
                            tiene_anulacion_pendiente = bebida.get('en_proceso_anulacion', False)
                            
                            # Verificar si la orden completa está en proceso de anulación
                            tiene_anulacion_orden_pendiente = orden.get('solicitud_anulacion_completa_pendiente', False)
                            
                            if tiene_anulacion_pendiente or tiene_anulacion_orden_pendiente:
                                # Mostrar advertencia y deshabilitar despacho
                                if tiene_anulacion_orden_pendiente:
                                    st.warning("⚠️ ORDEN EN ANULACIÓN COMPLETA")
                                    st.caption("🚫 No despachar - Orden completa pendiente de anulación")
                                else:
                                    st.warning("⚠️ PRODUCTO EN ANULACIÓN")
                                    st.caption("🚫 No despachar - Producto pendiente de anulación")
                                st.button(
                                    "🚫 DESPACHO BLOQUEADO", 
                                    key=f"blocked_{orden['_id']}_{item_id}",
                                    help="El despacho está bloqueado por solicitud de anulación pendiente",
                                    disabled=True,
                                    use_container_width=True
                                )
                            else:
                                # Botón de despachar normal
                                if st.button(
                                    "✅ DESPACHAR", 
                                    key=f"dispatch_{orden['_id']}_{item_id}",
                                    help=f"Marcar como despachada: {bebida.get('nombre')}",
                                    type="primary",
                                    use_container_width=True
                                ):
                                    if despachar_bebida(orden['_id'], item_id):
                                        st.success(f"✅ {bebida.get('nombre')} despachada!")
                                        st.balloons()
                                        st.rerun()
            
            st.markdown("---")
        
        else:
            st.info("🎉 ¡Excelente! No hay bebidas pendientes de despacho.")
        
        # SECCIÓN DE BEBIDAS DESPACHADAS
        if ordenes_con_bebidas_despachadas:
            st.markdown("---")
            st.subheader("✅ Bebidas Despachadas Recientemente")
            
            with st.expander(f"Ver bebidas despachadas ({sum(len(orden['bebidas_despachadas']) for orden in ordenes_con_bebidas_despachadas)} bebidas)", expanded=False):
                for orden in ordenes_con_bebidas_despachadas:
                    st.write(f"**🍽️ Orden #{orden.get('numero_orden', 'N/A')} - Mesa {orden.get('mesa_id', 'N/A').split(':')[-1] if orden.get('mesa_id') and ':' in orden.get('mesa_id') else orden.get('mesa_id', 'N/A')}**")
                    
                    for bebida in orden['bebidas_despachadas']:
                        col_bebida, col_info = st.columns([2, 2])
                        
                        with col_bebida:
                            st.write(f"✅ **{bebida.get('nombre', 'Bebida')}** (Cantidad: {bebida.get('cantidad', 1)})")
                        
                        with col_info:
                            fecha_despacho = bebida.get('fecha_despacho_bar', '')
                            usuario_despacho = bebida.get('usuario_despacho_bar', 'N/A')
                            
                            if fecha_despacho:
                                try:
                                    fecha_dt = datetime.fromisoformat(fecha_despacho.replace('Z', '+00:00'))
                                    # Convertir de UTC a hora local del sistema
                                    fecha_local = fecha_dt.astimezone()
                                    fecha_str = fecha_local.strftime('%H:%M:%S')
                                    st.write(f"⏰ Despachada: {fecha_str} por {usuario_despacho}")
                                except:
                                    st.write(f"👤 Despachada por: {usuario_despacho}")
                    
                    st.markdown("---")
        
        # AUTO-REFRESH
        col_refresh, col_clear = st.columns(2)
        with col_refresh:
            if st.button("🔄 Actualizar", help="Actualizar la lista de bebidas pendientes"):
                st.rerun()
        
        with col_clear:
            if st.button("🧹 Limpiar Debug", help="Desmarcar opciones de debug"):
                st.rerun()
        
        # Mostrar instrucciones
        with st.expander("📋 Instrucciones de Uso"):
            st.markdown("""
            ### Cómo usar el sistema:
            
            1. **Visualización**: Las órdenes con bebidas pendientes aparecen automáticamente
            2. **Tiempo**: Cada orden muestra el tiempo transcurrido desde su creación
            3. **Urgencia**: Las órdenes de más de 15 minutos se marcan en rojo
            4. **Despacho**: Click en "✅ DESPACHAR" cuando la bebida esté lista
            5. **Registro**: Se guarda automáticamente quién y cuándo despachó cada bebida
            6. **Actualización**: La página se actualiza automáticamente tras cada despacho
            
            ### Estadísticas:
            - **Órdenes con Bebidas**: Total de órdenes que tienen bebidas pendientes
            - **Bebidas Pendientes**: Cantidad total de bebidas por preparar
            - **Tiempo Promedio**: Tiempo promedio que llevan las órdenes pendientes
            """)

    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesión para acceder al sistema de bar.")