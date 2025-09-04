# pages/monitor_ordenes.py
import streamlit as st
from datetime import datetime, timezone
import couchdb_utils
import os

# Obtener la ruta relativa de la pagina
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Llama a la funcion de login/menu/validacion
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Monitor de Ordenes - Administracion", page_icon="../assets/LOGO.png")

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    .order-container {
        border: 2px solid #007acc;
        border-radius: 15px;
        padding: 15px;
        margin: 15px 0;
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .drink-item {
        border: 2px solid #ff6b6b;
        border-radius: 10px;
        padding: 10px;
        margin: 8px 0;
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .drink-item-completed {
        border: 2px solid #4caf50;
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
    }
    
    .food-item {
        border: 2px solid #ff9800;
        border-radius: 10px;
        padding: 10px;
        margin: 8px 0;
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .food-item-completed {
        border: 2px solid #4caf50;
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
    }
    
    .urgent-item {
        border-color: #dc3545 !important;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
        animation: pulse-red 2s infinite;
    }
    
    @keyframes pulse-red {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    .time-counter {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .completed-section {
        background-color: #f1f8e9;
        border: 1px solid #8bc34a;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # Funcion para obtener bebidas (reutilizando logica de bar.py)
        def obtener_bebidas_ids():
            platos = couchdb_utils.get_documents_by_partition(db, "platos")
            menus = couchdb_utils.get_documents_by_partition(db, "menu")
            
            # Encontrar el menu "bar"
            menu_bar = None
            for menu in menus:
                if menu.get('descripcion', '').lower() == 'bar':
                    menu_bar = menu
                    break
            
            bebidas_ids = []
            
            for plato in platos:
                nombre = plato.get('descripcion', '')
                categoria = plato.get('categoria', '')
                menu_id = plato.get('menu_id', '')
                
                # Metodos de identificacion (en orden de prioridad):
                es_bebida_menu = menu_bar and menu_id == menu_bar.get('_id')
                es_bebida_categoria = any(cat in categoria.lower() for cat in ['bar', 'bebida', 'bebidas', 'drink'])
                
                keywords_bebidas = [
                    'bebida', 'jugo', 'agua', 'gaseosa', 'refresco', 'cocktail', 
                    'cerveza', 'licor', 'cafe', 'te', 'smoothie', 'cola', 'pepsi',
                    'cuba', 'libre', 'mojito', 'pina', 'colada', 'margarita',
                    'daiquiri', 'whisky', 'ron', 'vodka', 'tequila', 'ginebra',
                    'sangria', 'vino', 'champagne', 'limonada', 'naranjada',
                    'soda', 'sprite', 'fanta', 'cocacola', 'energetica', 'isotonica',
                    'pilsener', 'pilsen', 'beer', 'lager'
                ]
                es_bebida_keyword = any(keyword in nombre.lower() for keyword in keywords_bebidas)
                
                if es_bebida_menu or es_bebida_categoria or es_bebida_keyword:
                    bebidas_ids.append(plato['_id'])
            
            return bebidas_ids
        
        # Funcion para obtener platos de cocina (reutilizando logica de cocina.py)
        def obtener_platos_cocina_ids():
            platos = couchdb_utils.get_documents_by_partition(db, "platos")
            menus = couchdb_utils.get_documents_by_partition(db, "menu")
            
            # Encontrar el menu "cocina"
            menu_cocina = None
            for menu in menus:
                if menu.get('descripcion', '').lower() == 'cocina':
                    menu_cocina = menu
                    break
            
            platos_cocina_ids = []
            
            for plato in platos:
                nombre = plato.get('descripcion', '')
                categoria = plato.get('categoria', '')
                menu_id = plato.get('menu_id', '')
                
                # Metodos de identificacion (en orden de prioridad):
                es_plato_menu = menu_cocina and menu_id == menu_cocina.get('_id')
                es_plato_categoria = any(cat in categoria.lower() for cat in ['cocina', 'comida', 'platos', 'food'])
                
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
                
                if es_plato_menu or es_plato_categoria or es_plato_keyword:
                    platos_cocina_ids.append(plato['_id'])
            
            return platos_cocina_ids
        
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
        
        # TITULO PRINCIPAL
        st.title("📊 Monitor de Ordenes - Administracion")
        st.markdown("### Monitoreo simultaneo de bebidas y platos por orden")
        st.markdown("---")
        
        # Obtener todas las ordenes pendientes y en cobro
        ordenes = couchdb_utils.get_documents_by_partition(db, "ordenes")
        ordenes_activas = [orden for orden in ordenes if orden.get('estado') in ['pendiente', 'en_cobro']]
        
        # Obtener IDs de bebidas y platos
        bebidas_ids = obtener_bebidas_ids()
        platos_cocina_ids = obtener_platos_cocina_ids()
        
        # Procesar ordenes para separar en proceso y completadas
        ordenes_en_proceso = []
        ordenes_completadas = []
        
        for orden in ordenes_activas:
            bebidas_pendientes = []
            bebidas_despachadas = []
            platos_pendientes = []
            platos_despachados = []
            
            for idx, item in enumerate(orden.get('items', [])):
                # Saltar items anulados
                if item.get('anulado', False):
                    continue
                    
                plato_id = item.get('plato_id')
                
                # Clasificar bebidas
                if plato_id in bebidas_ids:
                    if item.get('despachado_bar', False):
                        bebidas_despachadas.append(item)
                    else:
                        bebidas_pendientes.append(item)
                
                # Clasificar platos de cocina
                if plato_id in platos_cocina_ids:
                    if item.get('despachado_cocina', False):
                        platos_despachados.append(item)
                    else:
                        platos_pendientes.append(item)
            
            # Determinar si la orden tiene items pendientes o ya esta completada
            total_pendientes = len(bebidas_pendientes) + len(platos_pendientes)
            total_despachados = len(bebidas_despachadas) + len(platos_despachados)
            
            if total_pendientes > 0:
                orden_data = {
                    'orden': orden,
                    'bebidas_pendientes': bebidas_pendientes,
                    'platos_pendientes': platos_pendientes,
                    'bebidas_despachadas': bebidas_despachadas,
                    'platos_despachados': platos_despachados
                }
                ordenes_en_proceso.append(orden_data)
            elif total_despachados > 0:
                orden_data = {
                    'orden': orden,
                    'bebidas_despachadas': bebidas_despachadas,
                    'platos_despachados': platos_despachados
                }
                ordenes_completadas.append(orden_data)
        
        # ESTADISTICAS GENERALES
        col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
        
        with col_stats1:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{len(ordenes_en_proceso)}</h3>
                <p>Ordenes en Proceso</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats2:
            total_bebidas_pendientes = sum(len(o['bebidas_pendientes']) for o in ordenes_en_proceso)
            st.markdown(f"""
            <div class="stats-card">
                <h3>{total_bebidas_pendientes}</h3>
                <p>Bebidas Pendientes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats3:
            total_platos_pendientes = sum(len(o['platos_pendientes']) for o in ordenes_en_proceso)
            st.markdown(f"""
            <div class="stats-card">
                <h3>{total_platos_pendientes}</h3>
                <p>Platos Pendientes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_stats4:
            st.markdown(f"""
            <div class="stats-card">
                <h3>{len(ordenes_completadas)}</h3>
                <p>Ordenes Completadas</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # SECCION: ORDENES EN PROCESO
        if ordenes_en_proceso:
            st.subheader("🔄 Ordenes en Proceso")
            
            # Ordenar por numero de orden
            ordenes_en_proceso.sort(key=lambda x: x['orden'].get('numero_orden', 0))
            
            for orden_data in ordenes_en_proceso:
                orden = orden_data['orden']
                tiempo_str, minutos = calcular_tiempo_transcurrido(orden.get('fecha_creacion', ''))
                
                # Extraer numero de mesa
                mesa_id = orden.get('mesa_id', 'N/A')
                mesa_num = mesa_id.split(':')[-1] if mesa_id and ':' in mesa_id else mesa_id
                
                st.markdown(f"""
                <div class="order-container">
                    <h3>🍽️ Orden #{orden.get('numero_orden', 'N/A')} - Mesa {mesa_num}</h3>
                    <div class="time-counter">⏱️ Tiempo Total: {tiempo_str}</div>
                    <p><strong>Total:</strong> ${orden.get('total', 0):.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Mostrar bebidas pendientes
                if orden_data['bebidas_pendientes']:
                    st.write("**🍹 Bebidas Pendientes:**")
                    col_drinks1, col_drinks2 = st.columns(2)
                    
                    for i, bebida in enumerate(orden_data['bebidas_pendientes']):
                        col = col_drinks1 if i % 2 == 0 else col_drinks2
                        with col:
                            # Determinar urgencia (mas de 15 minutos para bebidas)
                            es_urgente = minutos > 15
                            clase_urgencia = "urgent-item" if es_urgente else ""
                            
                            st.markdown(f"""
                            <div class="drink-item {clase_urgencia}">
                                <strong>🥤 {bebida.get('nombre', 'Bebida')}</strong><br>
                                <small>Cantidad: {bebida.get('cantidad', 1)}</small><br>
                                <span class="time-counter">⏱️ {tiempo_str}</span>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Mostrar bebidas despachadas
                if orden_data.get('bebidas_despachadas'):
                    st.write("**✅ Bebidas Despachadas:**")
                    col_drinks_done1, col_drinks_done2 = st.columns(2)
                    
                    for i, bebida in enumerate(orden_data['bebidas_despachadas']):
                        col = col_drinks_done1 if i % 2 == 0 else col_drinks_done2
                        with col:
                            fecha_despacho = bebida.get('fecha_despacho_bar', '')
                            if fecha_despacho:
                                try:
                                    fecha_dt = datetime.fromisoformat(fecha_despacho.replace('Z', '+00:00'))
                                    fecha_local = fecha_dt.astimezone()
                                    hora_str = fecha_local.strftime('%H:%M:%S')
                                except:
                                    hora_str = "N/A"
                            else:
                                hora_str = "N/A"
                            
                            st.markdown(f"""
                            <div class="drink-item drink-item-completed">
                                <strong>🥤 {bebida.get('nombre', 'Bebida')}</strong><br>
                                <small>Cantidad: {bebida.get('cantidad', 1)}</small><br>
                                <small>⏰ Despachada: {hora_str}</small>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Mostrar platos pendientes
                if orden_data['platos_pendientes']:
                    st.write("**🍳 Platos Pendientes:**")
                    col_food1, col_food2 = st.columns(2)
                    
                    for i, plato in enumerate(orden_data['platos_pendientes']):
                        col = col_food1 if i % 2 == 0 else col_food2
                        with col:
                            # Determinar urgencia (mas de 20 minutos para platos)
                            es_urgente = minutos > 20
                            clase_urgencia = "urgent-item" if es_urgente else ""
                            
                            st.markdown(f"""
                            <div class="food-item {clase_urgencia}">
                                <strong>🍽️ {plato.get('nombre', 'Plato')}</strong><br>
                                <small>Cantidad: {plato.get('cantidad', 1)}</small><br>
                                <span class="time-counter">⏱️ {tiempo_str}</span>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Mostrar platos servidos
                if orden_data.get('platos_despachados'):
                    st.write("**✅ Platos Servidos:**")
                    col_food_done1, col_food_done2 = st.columns(2)
                    
                    for i, plato in enumerate(orden_data['platos_despachados']):
                        col = col_food_done1 if i % 2 == 0 else col_food_done2
                        with col:
                            fecha_despacho = plato.get('fecha_despacho_cocina', '')
                            if fecha_despacho:
                                try:
                                    fecha_dt = datetime.fromisoformat(fecha_despacho.replace('Z', '+00:00'))
                                    fecha_local = fecha_dt.astimezone()
                                    hora_str = fecha_local.strftime('%H:%M:%S')
                                except:
                                    hora_str = "N/A"
                            else:
                                hora_str = "N/A"
                            
                            st.markdown(f"""
                            <div class="food-item food-item-completed">
                                <strong>🍽️ {plato.get('nombre', 'Plato')}</strong><br>
                                <small>Cantidad: {plato.get('cantidad', 1)}</small><br>
                                <small>⏰ Servido: {hora_str}</small>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
        
        else:
            st.info("🎉 ¡Excelente! No hay ordenes en proceso actualmente.")
        
        # SECCION: ORDENES COMPLETADAS
        if ordenes_completadas:
            st.markdown("---")
            st.subheader("✅ Ordenes Completadas Recientemente")
            
            with st.expander(f"Ver ordenes completadas ({len(ordenes_completadas)} ordenes)", expanded=False):
                # Ordenar por numero de orden
                ordenes_completadas.sort(key=lambda x: x['orden'].get('numero_orden', 0))
                
                for orden_data in ordenes_completadas:
                    orden = orden_data['orden']
                    mesa_id = orden.get('mesa_id', 'N/A')
                    mesa_num = mesa_id.split(':')[-1] if mesa_id and ':' in mesa_id else mesa_id
                    
                    st.markdown(f"""
                    <div class="completed-section">
                        <h4>🍽️ Orden #{orden.get('numero_orden', 'N/A')} - Mesa {mesa_num}</h4>
                        <p><strong>Total:</strong> ${orden.get('total', 0):.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Mostrar bebidas completadas
                    if orden_data.get('bebidas_despachadas'):
                        st.write("**🍹 Bebidas Despachadas:**")
                        for bebida in orden_data['bebidas_despachadas']:
                            fecha_despacho = bebida.get('fecha_despacho_bar', '')
                            usuario_despacho = bebida.get('usuario_despacho_bar', 'N/A')
                            if fecha_despacho:
                                try:
                                    fecha_dt = datetime.fromisoformat(fecha_despacho.replace('Z', '+00:00'))
                                    fecha_local = fecha_dt.astimezone()
                                    hora_str = fecha_local.strftime('%H:%M:%S')
                                    st.write(f"  • {bebida.get('nombre')} (x{bebida.get('cantidad', 1)}) - Despachada: {hora_str} por {usuario_despacho}")
                                except:
                                    st.write(f"  • {bebida.get('nombre')} (x{bebida.get('cantidad', 1)}) - Por: {usuario_despacho}")
                    
                    # Mostrar platos completados
                    if orden_data.get('platos_despachados'):
                        st.write("**🍽️ Platos Servidos:**")
                        for plato in orden_data['platos_despachados']:
                            fecha_despacho = plato.get('fecha_despacho_cocina', '')
                            usuario_despacho = plato.get('usuario_despacho_cocina', 'N/A')
                            if fecha_despacho:
                                try:
                                    fecha_dt = datetime.fromisoformat(fecha_despacho.replace('Z', '+00:00'))
                                    fecha_local = fecha_dt.astimezone()
                                    hora_str = fecha_local.strftime('%H:%M:%S')
                                    st.write(f"  • {plato.get('nombre')} (x{plato.get('cantidad', 1)}) - Servido: {hora_str} por {usuario_despacho}")
                                except:
                                    st.write(f"  • {plato.get('nombre')} (x{plato.get('cantidad', 1)}) - Por: {usuario_despacho}")
                    
                    st.markdown("---")
        
        # AUTO-REFRESH
        col_refresh, col_info = st.columns(2)
        with col_refresh:
            if st.button("🔄 Actualizar Monitor", help="Actualizar el estado de todas las ordenes"):
                st.rerun()
        
        with col_info:
            st.info("🔄 El monitor se actualiza automaticamente cada vez que se interactua")
        
        # Instrucciones
        with st.expander("📋 Informacion del Monitor"):
            st.markdown("""
            ### Monitor de Ordenes - Panel de Administracion
            
            **Funcionalidades:**
            - **Vista unificada** de bebidas (bar) y platos (cocina) por orden
            - **Tiempos de preparacion** desde la creacion de cada orden
            - **Estado de urgencia** visual (rojo) para items que exceden tiempo limite
            - **Estadisticas en tiempo real** de items pendientes y completados
            
            **Codigos de color:**
            - 🍹 **Bebidas pendientes**: Fondo rosa - Urgente despues de 15 minutos
            - 🍽️ **Platos pendientes**: Fondo naranja - Urgente despues de 20 minutos  
            - ✅ **Items completados**: Fondo verde con hora de finalizacion
            
            **Organizacion:**
            - **Ordenes en Proceso**: Muestran items pendientes y ya completados por orden
            - **Ordenes Completadas**: Solo ordenes donde todos los items han sido despachados/servidos
            
            **Para el Administrador:**
            - Monitoreo simultaneo sin necesidad de cambiar entre pantallas
            - Identificacion rapida de cuellos de botella en cocina o bar
            - Seguimiento de tiempos de servicio por estacion
            """)

    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesion para acceder al monitor de ordenes.")