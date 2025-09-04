# pages/cocina.py
import streamlit as st
from datetime import datetime, timezone
import couchdb_utils
import os
import time

# Obtener la ruta relativa de la pagina
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Llama a la funcion de login/menu/validacion
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Sistema de Despacho de Cocina", page_icon="../assets/LOGO.png")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    .dish-card {
        border: 2px solid #28a745;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(135deg, #d4f4dd 0%, #a8e6cf 50%, #88d8a3 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .urgent-card {
        border-color: #dc3545 !important;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
        animation: pulse-red 2s infinite;
    }
    
    @keyframes pulse-red {
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
        color: #155724;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .serve-btn {
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
    
    .serve-btn:hover {
        background: linear-gradient(45deg, #218838, #1ea672);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #fd7e14 0%, #e55353 100%);
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
        if 'cocina_last_refresh' not in st.session_state:
            st.session_state.cocina_last_refresh = time.time()
        
        if 'cocina_previous_items' not in st.session_state:
            st.session_state.cocina_previous_items = set()
        
        if 'cocina_new_items' not in st.session_state:
            st.session_state.cocina_new_items = set()
        
        if 'cocina_new_items_timestamp' not in st.session_state:
            st.session_state.cocina_new_items_timestamp = {}
        
        # Auto-refresh cada 60 segundos
        current_time = time.time()
        if current_time - st.session_state.cocina_last_refresh >= 60:
            st.session_state.cocina_last_refresh = current_time
            st.rerun()
        # Funcion para obtener platos de cocina
        def obtener_platos_cocina():
            platos = couchdb_utils.get_documents_by_partition(db, "platos")
            menus = couchdb_utils.get_documents_by_partition(db, "menu")
            
            # Encontrar el menu "cocina"
            menu_cocina = None
            for menu in menus:
                if menu.get('descripcion', '').lower() == 'cocina':
                    menu_cocina = menu
                    break
            
            platos_cocina = []
            
            for plato in platos:
                nombre = plato.get('descripcion', '')
                categoria = plato.get('categoria', '')
                menu_id = plato.get('menu_id', '')
                
                # Metodos de identificacion (en orden de prioridad):
                # 1. Por menu "cocina" (PRIORITARIO)
                es_plato_menu = False
                if menu_cocina and menu_id == menu_cocina.get('_id'):
                    es_plato_menu = True
                
                # 2. Por categoria especifica
                es_plato_categoria = any(cat in categoria.lower() for cat in ['cocina', 'comida', 'platos', 'food'])
                
                # 3. Por palabras clave (fallback)
                keywords_cocina = [
                    'pollo', 'carne', 'res', 'cerdo', 'pescado', 'mariscos',
                    'pasta', 'espagueti', 'lasagna', 'pizza', 'hamburguesa',
                    'ensalada', 'sopa', 'sancocho', 'arroz', 'frijoles',
                    'tacos', 'quesadilla', 'burrito', 'torta', 'sandwich',
                    'filete', 'chuleta', 'costilla', 'camarones', 'salmon',
                    'verduras', 'vegetales', 'guisado', 'estofado', 'asado',
                    'frito', 'grillado', 'hornado', 'empanada', 'pupusa',
                    'alitas', 'alita', 'wings', 'wing', 'nuggets', 'pechuga',
                    'muslo', 'comida', 'plato', 'almuerzo', 'cena', 'desayuno',
                    'carnita', 'carnitas', 'chicharron'
                ]
                es_plato_keyword = any(keyword in nombre.lower() for keyword in keywords_cocina)
                
                # Es plato de cocina si cumple cualquiera de los criterios
                es_plato_cocina = es_plato_menu or es_plato_categoria or es_plato_keyword
                
                if es_plato_cocina:
                    platos_cocina.append(plato['_id'])
                    
                    # Determinar metodo de deteccion
                    if es_plato_menu:
                        metodo = 'Menu Cocina'
                    elif es_plato_categoria:
                        metodo = 'Categoria'
                    else:
                        metodo = 'Palabra clave'
                    
            
            return platos_cocina
        
        # Funcion para calcular tiempo transcurrido
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
        
        # Funcion para despachar plato
        def despachar_plato(orden_id, item_id):
            try:
                # Obtener la orden actual
                orden = db.get(orden_id)
                item_despachado = None
                
                # Buscar el item especifico y marcarlo como despachado
                for idx, item in enumerate(orden.get('items', [])):
                    # Excluir productos anulados
                    if item.get('anulado', False):
                        continue
                        
                    # Crear ID temporal si no existe
                    temp_id = item.get('id') or f"{orden_id}_{idx}"
                    
                    if temp_id == item_id:
                        item['despachado_cocina'] = True
                        item['fecha_despacho_cocina'] = datetime.now(timezone.utc).isoformat()
                        item['usuario_despacho_cocina'] = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        item['id'] = temp_id  # Asegurar que tenga ID
                        item_despachado = item
                        break
                
                if item_despachado is None:
                    st.error(f"No se encontro el item con ID: {item_id}")
                    return False
                
                # Guardar la orden actualizada
                db.save(orden)
                
                # Log de la accion
                logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                couchdb_utils.log_action(
                    db, 
                    logged_in_user, 
                    f"Plato servido - Orden #{orden.get('numero_orden')} - Item: {item_despachado.get('nombre', 'N/A')}"
                )
                
                return True
            except Exception as e:
                st.error(f"Error al servir plato: {str(e)}")
                return False
        
        # TITULO PRINCIPAL
        st.title("🍽️ Sistema de Despacho de Cocina")
        st.markdown("---")
        
        # Obtener todas las ordenes pendientes y en cobro
        ordenes = couchdb_utils.get_documents_by_partition(db, "ordenes")
        ordenes_activas = [orden for orden in ordenes if orden.get('estado') in ['pendiente', 'en_cobro']]
        
        # Obtener lista de IDs de platos de cocina
        platos_cocina_ids = obtener_platos_cocina()
        
        # Filtrar ordenes que tienen platos de cocina (pendientes y despachados)
        ordenes_con_platos = []
        ordenes_con_platos_despachados = []
        
        for orden in ordenes_activas:
            platos_pendientes = []
            platos_despachados = []
            
            for idx, item in enumerate(orden.get('items', [])):
                # Excluir productos anulados del despacho de cocina
                if item.get('anulado', False):
                    continue
                
                if item.get('plato_id') in platos_cocina_ids:
                    # Asegurar que el item tenga un ID unico
                    if not item.get('id'):
                        item['id'] = f"{orden['_id']}_{idx}"
                    
                    if item.get('despachado_cocina', False):
                        platos_despachados.append(item)
                    else:
                        platos_pendientes.append(item)
            
            if platos_pendientes:
                orden['platos_pendientes'] = platos_pendientes
                ordenes_con_platos.append(orden)
                
            if platos_despachados:
                orden['platos_despachados'] = platos_despachados
                ordenes_con_platos_despachados.append(orden)
        
        # ESTADISTICAS EN TIEMPO REAL
        col_stats1, col_stats2, col_stats3 = st.columns(3)
        
        with col_stats1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{len(ordenes_con_platos)}</h3>
                <p>Ordenes con Platos</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats2:
            total_platos = sum(len(orden['platos_pendientes']) for orden in ordenes_con_platos)
            st.markdown(f"""
            <div class="stats-card">
                <h3>{total_platos}</h3>
                <p>Platos Pendientes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats3:
            if ordenes_con_platos:
                tiempos = [calcular_tiempo_transcurrido(orden.get('fecha_creacion', ''))[1] for orden in ordenes_con_platos]
                tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
                st.markdown(f"""
                <div class="stats-card">
                    <h3>{int(tiempo_promedio)} min</h3>
                    <p>Tiempo Promedio</p>
                </div>
                """, unsafe_allow_html=True)
        
        
        st.markdown("---")
        
        # MOSTRAR ORDENES CON PLATOS
        if ordenes_con_platos:
            st.subheader("🍳 Platos Pendientes de Preparacion")
            
            # Ordenar por tiempo de creacion (mas antiguas primero)
            ordenes_con_platos.sort(key=lambda x: x.get('fecha_creacion', ''))
            
            # Crear lista de todos los platos pendientes con número correlativo
            todos_los_platos = []
            current_items = set()
            
            for orden in ordenes_con_platos:
                for idx, plato in enumerate(orden['platos_pendientes']):
                    # Crear un ID unico para el item
                    item_id = plato.get('id') or f"{orden['_id']}_{idx}"
                    plato['id'] = item_id  # Asegurar que tenga ID
                    current_items.add(item_id)
                    
                    # Calcular tiempo para este plato específico
                    tiempo_str, minutos = calcular_tiempo_transcurrido(orden.get('fecha_creacion', ''))
                    es_urgente = minutos > 20
                    
                    # Extraer numero de mesa
                    mesa_id = orden.get('mesa_id', 'N/A')
                    mesa_num = mesa_id.split(':')[-1] if mesa_id and ':' in mesa_id else mesa_id
                    
                    # Verificar si es un item nuevo
                    es_nuevo = item_id not in st.session_state.cocina_previous_items
                    if es_nuevo:
                        st.session_state.cocina_new_items.add(item_id)
                        st.session_state.cocina_new_items_timestamp[item_id] = current_time
                    
                    # Remover items nuevos después de 4 parpadeos (4 segundos)
                    if item_id in st.session_state.cocina_new_items_timestamp:
                        if current_time - st.session_state.cocina_new_items_timestamp[item_id] > 4:
                            st.session_state.cocina_new_items.discard(item_id)
                            st.session_state.cocina_new_items_timestamp.pop(item_id, None)
                    
                    todos_los_platos.append({
                        'orden': orden,
                        'plato': plato,
                        'item_id': item_id,
                        'tiempo_str': tiempo_str,
                        'minutos': minutos,
                        'es_urgente': es_urgente,
                        'mesa_num': mesa_num,
                        'es_nuevo': item_id in st.session_state.cocina_new_items
                    })
            
            # Actualizar items anteriores para la próxima comparación
            st.session_state.cocina_previous_items = current_items.copy()
            
            # Mostrar platos en filas de 4 columnas
            for i in range(0, len(todos_los_platos), 4):
                cols = st.columns(4)
                for j in range(4):
                    if i + j < len(todos_los_platos):
                        item_data = todos_los_platos[i + j]
                        orden = item_data['orden']
                        plato = item_data['plato']
                        item_id = item_data['item_id']
                        tiempo_str = item_data['tiempo_str']
                        es_urgente = item_data['es_urgente']
                        mesa_num = item_data['mesa_num']
                        es_nuevo = item_data['es_nuevo']
                        
                        # Número correlativo de llegada
                        numero_llegada = i + j + 1
                        
                        # Determinar la clase CSS
                        if es_nuevo:
                            card_class = "dish-card new-item"
                        elif es_urgente:
                            card_class = "urgent-card"
                        else:
                            card_class = "dish-card"
                        
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
                                                🍳 {plato.get('nombre', 'Plato')} (x{plato.get('cantidad', 1)})
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
                            if plato.get('comentarios'):
                                st.caption(f"💬 {plato['comentarios']}")
                            
                            # Verificar si el producto tiene solicitud de anulación pendiente
                            tiene_anulacion_pendiente = plato.get('en_proceso_anulacion', False)
                            
                            # Verificar si la orden completa está en proceso de anulación
                            tiene_anulacion_orden_pendiente = orden.get('solicitud_anulacion_completa_pendiente', False)
                            
                            if tiene_anulacion_pendiente or tiene_anulacion_orden_pendiente:
                                # Mostrar advertencia y deshabilitar servicio
                                if tiene_anulacion_orden_pendiente:
                                    st.warning("⚠️ ORDEN EN ANULACIÓN COMPLETA")
                                    st.caption("🚫 No servir - Orden completa pendiente de anulación")
                                else:
                                    st.warning("⚠️ PRODUCTO EN ANULACIÓN")
                                    st.caption("🚫 No servir - Producto pendiente de anulación")
                                st.button(
                                    "🚫 SERVICIO BLOQUEADO", 
                                    key=f"blocked_{orden['_id']}_{item_id}",
                                    help="El servicio está bloqueado por solicitud de anulación pendiente",
                                    disabled=True,
                                    use_container_width=True
                                )
                            else:
                                # Botón de servir normal
                                if st.button(
                                    "✅ SERVIR", 
                                    key=f"serve_{orden['_id']}_{item_id}",
                                    help=f"Marcar como servido: {plato.get('nombre')}",
                                    type="primary",
                                    use_container_width=True
                                ):
                                    if despachar_plato(orden['_id'], item_id):
                                        st.success(f"✅ {plato.get('nombre')} servido!")
                                        st.balloons()
                                        st.rerun()
            
            st.markdown("---")
        
        else:
            st.info("🎉 ¡Excelente! No hay platos pendientes en cocina.")
        
        # SECCION DE PLATOS DESPACHADOS
        if ordenes_con_platos_despachados:
            st.markdown("---")
            st.subheader("✅ Platos Servidos Recientemente")
            
            with st.expander(f"Ver platos servidos ({sum(len(orden['platos_despachados']) for orden in ordenes_con_platos_despachados)} platos)", expanded=False):
                for orden in ordenes_con_platos_despachados:
                    mesa_id = orden.get('mesa_id', 'N/A')
                    mesa_num = mesa_id.split(':')[-1] if mesa_id and ':' in mesa_id else mesa_id
                    st.write(f"**🍽️ Orden #{orden.get('numero_orden', 'N/A')} - Mesa {mesa_num}**")
                    
                    for plato in orden['platos_despachados']:
                        col_plato, col_info = st.columns([2, 2])
                        
                        with col_plato:
                            st.write(f"✅ **{plato.get('nombre', 'Plato')}** (Cantidad: {plato.get('cantidad', 1)})")
                        
                        with col_info:
                            fecha_despacho = plato.get('fecha_despacho_cocina', '')
                            usuario_despacho = plato.get('usuario_despacho_cocina', 'N/A')
                            
                            if fecha_despacho:
                                try:
                                    fecha_dt = datetime.fromisoformat(fecha_despacho.replace('Z', '+00:00'))
                                    # Convertir de UTC a hora local del sistema
                                    fecha_local = fecha_dt.astimezone()
                                    fecha_str = fecha_local.strftime('%H:%M:%S')
                                    st.write(f"⏰ Servido: {fecha_str} por {usuario_despacho}")
                                except:
                                    st.write(f"👤 Servido por: {usuario_despacho}")
                    
                    st.markdown("---")
        
        # AUTO-REFRESH
        col_refresh, col_clear = st.columns(2)
        with col_refresh:
            if st.button("🔄 Actualizar", help="Actualizar la lista de platos pendientes"):
                st.rerun()
        
        with col_clear:
            if st.button("🧹 Limpiar Debug", help="Desmarcar opciones de debug"):
                st.rerun()
        
        # Mostrar instrucciones
        with st.expander("📋 Instrucciones de Uso"):
            st.markdown("""
            ### Como usar el sistema de cocina:
            
            1. **Visualizacion**: Las ordenes con platos pendientes aparecen automaticamente
            2. **Tiempo**: Cada orden muestra el tiempo transcurrido desde su creacion
            3. **Urgencia**: Las ordenes de mas de 20 minutos se marcan en rojo
            4. **Servir**: Click en "✅ SERVIR" cuando el plato este listo
            5. **Registro**: Se guarda automaticamente quien y cuando sirvio cada plato
            6. **Actualizacion**: La pagina se actualiza automaticamente tras cada servicio
            
            ### Estadisticas:
            - **Ordenes con Platos**: Total de ordenes que tienen platos pendientes
            - **Platos Pendientes**: Cantidad total de platos por preparar
            - **Tiempo Promedio**: Tiempo promedio que llevan las ordenes pendientes
            
            ### Diferencia con Bar:
            - **Cocina maneja platos** (comida) vs **Bar maneja bebidas**
            - **Tiempo urgente**: 20+ minutos (vs 15+ en bar)
            - **Terminologia**: "Servir" vs "Despachar"
            """)

    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesion para acceder al sistema de cocina.")