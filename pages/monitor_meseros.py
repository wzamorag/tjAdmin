# pages/monitor_meseros.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone, timedelta
import pandas as pd
import plotly.express as px

# --- Configuración Inicial ---
st.set_page_config(layout="wide", page_title="Monitor de Meseros", page_icon="../assets/LOGO.png")
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)

# --- Funciones auxiliares ---
def get_estado_color(estado):
    """Retorna color según el estado de la orden"""
    colors = {
        'pendiente': '#FFA500',      # Naranja
        'preparando': '#FFD700',     # Dorado
        'listo': '#32CD32',          # Verde lima  
        'entregado': '#4169E1',      # Azul real
        'pagando': '#9370DB',        # Violeta
        'pagada': '#28a745',         # Verde
        'cancelada': '#DC143C'       # Rojo
    }
    return colors.get(estado, '#6c757d')  # Gris por defecto

def get_estado_icon(estado):
    """Retorna icono según el estado"""
    icons = {
        'pendiente': '⏳',
        'preparando': '👨‍🍳',
        'listo': '✅',
        'entregado': '🍽️',
        'pagando': '💳',
        'pagada': '💰',
        'cancelada': '❌'
    }
    return icons.get(estado, '❓')

def get_tiempo_transcurrido(fecha_creacion):
    """Calcula tiempo transcurrido desde la creación"""
    try:
        if isinstance(fecha_creacion, str):
            fecha = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
        else:
            fecha = fecha_creacion
        
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        
        ahora = datetime.now(timezone.utc)
        delta = ahora - fecha
        
        if delta.total_seconds() < 3600:
            minutos = int(delta.total_seconds() / 60)
            return f"{minutos}m"
        else:
            horas = int(delta.total_seconds() / 3600)
            return f"{horas}h {int((delta.total_seconds() % 3600) / 60)}m"
    except:
        return "N/A"

def render_orden_card(orden, mesa, mesero):
    """Renderiza una tarjeta de orden individual"""
    estado = orden.get('estado', 'pendiente')
    color = get_estado_color(estado)
    icon = get_estado_icon(estado)
    tiempo = get_tiempo_transcurrido(orden.get('fecha_creacion'))
    
    # Número de mesa
    mesa_descripcion = mesa.get('descripcion', 'N/A') if mesa else 'N/A'
    mesa_numero = mesa_descripcion.split()[-1] if mesa_descripcion != 'N/A' else '?'
    
    # Crear contenido para items
    items = orden.get('items', [])
    items_content = ""
    for item in items[:6]:
        estado_plato = item.get('estado', 'preparando')
        icono_plato = '✅' if estado_plato == 'entregado' else '👨‍🍳'
        items_content += f"• {item.get('cantidad', 1)}x {item.get('nombre', 'Item')} {icono_plato}<br>"
    
    if len(items) > 6:
        items_content += f"... y {len(items) - 6} más"
    
    # Marca de agua para canceladas
    watermark = ""
    if estado == 'cancelada':
        watermark = '''
        <div style="position: absolute; top: 50%; left: 50%; 
                    transform: translate(-50%, -50%) rotate(-45deg);
                    font-size: 36px; color: rgba(220, 20, 60, 0.3); 
                    font-weight: bold; z-index: 10; pointer-events: none;">
            CANCELADA
        </div>
        '''
    
    # HTML de la tarjeta
    card_html = f'''
    <div style="position: relative; border: 3px solid {color}; border-radius: 15px; 
                padding: 15px; margin: 10px; background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1); min-height: 300px;">
        
        {watermark}
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div style="background: {color}; color: white; padding: 15px 25px; border-radius: 50px;
                        font-size: 32px; font-weight: bold; text-align: center; min-width: 70px;">
                {mesa_numero}
            </div>
            <div style="text-align: right;">
                <div style="font-size: 20px;">{icon}</div>
                <div style="font-size: 11px; color: #666;">#{orden.get('numero_orden', 'N/A')}</div>
            </div>
        </div>
        
        <div style="background: {color}; color: white; padding: 8px 15px; border-radius: 20px;
                    text-align: center; margin-bottom: 15px; font-weight: bold; font-size: 13px;">
            {estado.upper()} • {tiempo}
        </div>
        
        <div style="margin-bottom: 15px; font-size: 11px; color: #495057;">
            <strong>🏠 Mesa:</strong> {mesa_descripcion}<br>
            <strong>👨 Mesero:</strong> {mesero.get('nombre', 'N/A') if mesero else 'N/A'}
        </div>
        
        <div style="max-height: 100px; overflow-y: auto; font-size: 10px; margin-bottom: 15px;">
            <strong>🍽️ Platos:</strong><br>
            {items_content}
        </div>
        
        <div style="border-top: 2px solid {color}; padding-top: 10px; text-align: center; 
                    font-size: 16px; font-weight: bold; color: {color};">
            TOTAL: ${orden.get('total', 0):.2f}
        </div>
    </div>
    '''
    
    return card_html

# --- Lógica Principal ---
if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        st.title("📊 Monitor de Meseros y Órdenes")
        st.markdown("---")
        
        # Obtener datos
        ordenes = couchdb_utils.get_documents_by_partition(db, "ordenes")
        usuarios = couchdb_utils.get_documents_by_partition(db, "Usuario")
        mesas = couchdb_utils.get_documents_by_partition(db, "mesas")
        
        # Filtrar meseros (rol 3)
        meseros = {u['_id']: u for u in usuarios if u.get('id_rol') == 3}
        mesas_dict = {m['_id']: m for m in mesas}
        
        if not meseros:
            st.warning("No se encontraron meseros en el sistema.")
        else:
            # Filtros
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                meseros_nombres = list({m['nombre'] for m in meseros.values()})
                selected_mesero = st.selectbox("Filtrar por mesero:", ["Todos"] + meseros_nombres)
            
            with col2:
                estados = ['pendiente', 'preparando', 'listo', 'entregado', 'pagando', 'pagada', 'cancelada']
                selected_estado = st.selectbox("Filtrar por estado:", ["Todos"] + estados)
            
            with col3:
                periodo = st.selectbox("Período:", ["Último día", "Últimos 3 días", "Última semana", "Todo"])
            
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Actualizar", use_container_width=True):
                    st.rerun()
            
            
            # Filtrar órdenes
            ahora = datetime.now(timezone.utc)
            fecha_limite = None
            if periodo == "Último día":
                fecha_limite = ahora - timedelta(days=1)
            elif periodo == "Últimos 3 días":
                fecha_limite = ahora - timedelta(days=3)
            elif periodo == "Última semana":
                fecha_limite = ahora - timedelta(weeks=1)
            
            ordenes_filtradas = []
            for orden in ordenes:
                # Filtrar por fecha
                if fecha_limite:
                    try:
                        fecha = datetime.fromisoformat(orden.get('fecha_creacion', '').replace('Z', '+00:00'))
                        if fecha < fecha_limite:
                            continue
                    except:
                        continue
                
                # Filtrar por mesero
                if selected_mesero != "Todos":
                    mesero_id = next((mid for mid, m in meseros.items() if m['nombre'] == selected_mesero), None)
                    if orden.get('mesero_id') != mesero_id:
                        continue
                
                # Filtrar por estado
                if selected_estado != "Todos":
                    if orden.get('estado') != selected_estado:
                        continue
                
                ordenes_filtradas.append(orden)
            
            # Métricas
            col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
            
            with col_m1:
                st.metric("Total Órdenes", len(ordenes_filtradas))
            
            with col_m2:
                en_proceso = len([o for o in ordenes_filtradas if o.get('estado') in ['pendiente', 'preparando', 'listo']])
                st.metric("En Proceso", en_proceso)
            
            with col_m3:
                entregadas = len([o for o in ordenes_filtradas if o.get('estado') == 'entregado'])
                st.metric("Entregadas", entregadas)
            
            with col_m4:
                total = sum(orden.get('total', 0) for orden in ordenes_filtradas)
                st.metric("Total Ventas", f"${total:.2f}")
            
            with col_m5:
                meseros_activos = len(set(o.get('mesero_id') for o in ordenes_filtradas))
                st.metric("Meseros Activos", meseros_activos)
            
            st.markdown("---")
            
            # Mostrar órdenes por mesero (4 por fila)
            if ordenes_filtradas:
                st.subheader("🎯 Órdenes por Mesero")
                
                # Agrupar por mesero
                ordenes_por_mesero = {}
                for orden in ordenes_filtradas:
                    mesero_id = orden.get('mesero_id')
                    mesero = meseros.get(mesero_id, {'nombre': 'Desconocido'})
                    nombre = mesero.get('nombre', 'Desconocido')
                    
                    if nombre not in ordenes_por_mesero:
                        ordenes_por_mesero[nombre] = []
                    ordenes_por_mesero[nombre].append(orden)
                
                # Mostrar por mesero
                for mesero_nombre, ordenes_mesero in ordenes_por_mesero.items():
                    st.markdown(f"### 👤 {mesero_nombre} ({len(ordenes_mesero)} órdenes)")
                    
                    # Mostrar en grupos de 4
                    for i in range(0, len(ordenes_mesero), 4):
                        cols = st.columns(4)
                        
                        for j in range(4):
                            if i + j < len(ordenes_mesero):
                                orden = ordenes_mesero[i + j]
                                mesa = mesas_dict.get(orden.get('mesa_id'))
                                mesero_obj = meseros.get(orden.get('mesero_id'))
                                
                                with cols[j]:
                                    card_html = render_orden_card(orden, mesa, mesero_obj)
                                    st.html(card_html)
                                    
                                    # Botones de acción
                                    col_btn1, col_btn2 = st.columns(2)
                                    with col_btn1:
                                        if st.button("📝", key=f"det_{orden['_id']}", help="Ver detalles"):
                                            st.info(f"Orden #{orden.get('numero_orden')} - Mesa {mesa.get('descripcion') if mesa else 'N/A'}")
                                    with col_btn2:
                                        if st.button("⚡", key=f"act_{orden['_id']}", help="Acciones"):
                                            st.success("Funciones de acción próximamente")
                    
                    st.markdown("---")
            else:
                st.info("No hay órdenes que coincidan con los filtros.")
            
            # Estadísticas
            if ordenes_filtradas:
                st.subheader("📈 Estadísticas por Mesero")
                
                stats = {}
                for orden in ordenes_filtradas:
                    mesero_id = orden.get('mesero_id')
                    mesero = meseros.get(mesero_id, {'nombre': 'Desconocido'})
                    nombre = mesero.get('nombre', 'Desconocido')
                    
                    if nombre not in stats:
                        stats[nombre] = {'ordenes': 0, 'ventas': 0, 'estados': {}}
                    
                    stats[nombre]['ordenes'] += 1
                    stats[nombre]['ventas'] += orden.get('total', 0)
                    
                    estado = orden.get('estado', 'pendiente')
                    stats[nombre]['estados'][estado] = stats[nombre]['estados'].get(estado, 0) + 1
                
                # Gráficos
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    nombres = list(stats.keys())
                    ordenes_count = [stats[n]['ordenes'] for n in nombres]
                    
                    fig1 = px.bar(x=nombres, y=ordenes_count, title="Órdenes por Mesero")
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col_chart2:
                    ventas = [stats[n]['ventas'] for n in nombres]
                    
                    fig2 = px.bar(x=nombres, y=ventas, title="Ventas por Mesero ($)")
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Tabla resumen
                resumen = []
                for nombre, data in stats.items():
                    resumen.append({
                        'Mesero': nombre,
                        'Órdenes': data['ordenes'],
                        'Ventas': f"${data['ventas']:.2f}",
                        'Promedio': f"${data['ventas']/data['ordenes']:.2f}" if data['ordenes'] > 0 else "$0.00",
                        'En Proceso': sum(data['estados'].get(e, 0) for e in ['preparando', 'listo']),
                        'Entregadas': data['estados'].get('entregado', 0)
                    })
                
                df = pd.DataFrame(resumen)
                st.dataframe(df, use_container_width=True)
    
    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesión para acceder a esta página.")