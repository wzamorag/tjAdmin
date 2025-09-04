# pages/gestionar_anulaciones.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone

# --- Configuración Inicial ---
st.set_page_config(layout="wide", page_title="Gestión de Anulaciones", page_icon="../assets/LOGO.png")
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)

# --- Estilos CSS ---
st.markdown("""
<style>
    .solicitud-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .solicitud-pendiente {
        border-left: 5px solid #ffc107;
        background-color: #fff3cd;
    }
    .solicitud-aprobada {
        border-left: 5px solid #28a745;
        background-color: #d4edda;
    }
    .solicitud-rechazada {
        border-left: 5px solid #dc3545;
        background-color: #f8d7da;
    }
    .producto-info {
        background-color: #e9ecef;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .action-button {
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- Función para convertir tiempo UTC a local ---
def convert_to_local_time(utc_string):
    """Convierte una fecha UTC ISO a hora local"""
    try:
        if utc_string:
            dt = datetime.fromisoformat(utc_string.replace('Z', '+00:00'))
            return dt.astimezone()
    except Exception:
        pass
    return None

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    # Verificar que el usuario sea administrador o operativo
    user_role = st.session_state.get('user_data', {}).get('id_rol', 0)
    if user_role not in [1, 6]:  # Administradores y Operativos
        st.error("❌ Acceso denegado. Solo los administradores y operativos pueden gestionar anulaciones.")
        st.info("💡 Esta funcionalidad está reservada para usuarios con rol de administrador o operativo.")
        st.stop()
    
    if db:
        st.title("🗑️ Gestión de Anulaciones de Productos")
        
        # --- Obtener datos necesarios ---
        solicitudes = couchdb_utils.obtener_solicitudes_anulacion_pendientes(db)
        
        # Mostrar badge de notificación si hay solicitudes pendientes
        if solicitudes:
            st.markdown(f"""
            <div style="background-color: #ff6b6b; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
                🔔 <strong>{len(solicitudes)} solicitud(es) pendiente(s)</strong> requieren su atención inmediata
            </div>
            """, unsafe_allow_html=True)
        all_solicitudes = couchdb_utils.get_documents_by_partition(db, "anulaciones")
        ordenes = {o['_id']: o for o in couchdb_utils.get_documents_by_partition(db, "ordenes")}
        mesas = {m['_id']: m for m in couchdb_utils.get_documents_by_partition(db, "mesas")}
        meseros = {m['_id']: m for m in couchdb_utils.get_documents_by_partition(db, "Usuario") if m.get('id_rol') == 3}
        
        # --- Pestañas ---
        tab_pendientes, tab_ordenes, tab_historial = st.tabs(["🕒 Anulaciones Productos", "🗑️ Anulaciones Órdenes", "📋 Historial"])
        
        with tab_pendientes:
            st.subheader("Solicitudes Pendientes de Aprobación")
            
            if not solicitudes:
                st.info("✅ No hay solicitudes de anulación pendientes.")
            else:
                st.success(f"📋 {len(solicitudes)} solicitud(es) pendiente(s) de revisión")
                
                for solicitud in solicitudes:
                    orden_id = solicitud.get('orden_id')
                    item_index = solicitud.get('item_index', 0)
                    
                    # Obtener información de la orden
                    orden = ordenes.get(orden_id, {})
                    mesa = mesas.get(orden.get('mesa_id'), {})
                    mesero = meseros.get(orden.get('mesero_id'), {})
                    
                    # Obtener información del producto a anular
                    items = orden.get('items', [])
                    if item_index < len(items):
                        item = items[item_index]
                    else:
                        item = {'nombre': 'Producto no encontrado', 'cantidad': 0, 'precio_unitario': 0}
                    
                    # Convertir fecha de solicitud
                    fecha_solicitud = convert_to_local_time(solicitud.get('fecha_solicitud'))
                    fecha_str = fecha_solicitud.strftime('%d/%m/%Y %H:%M:%S') if fecha_solicitud else 'N/A'
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="solicitud-card solicitud-pendiente">
                            <h4>🔔 Solicitud de Anulación #{solicitud.get('_id', 'N/A')[-8:]}</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Información de la solicitud
                        col_info1, col_info2 = st.columns([1, 1])
                        
                        with col_info1:
                            st.markdown(f"""
                            **📋 Orden:** #{orden.get('numero_orden', 'N/A')}  
                            **🏠 Mesa:** {mesa.get('descripcion', 'N/A')}  
                            **👤 Mesero:** {mesero.get('nombre', 'N/A')}
                            """)
                        
                        with col_info2:
                            st.markdown(f"""
                            **🕐 Fecha Solicitud:** {fecha_str}  
                            **👤 Solicitado por:** {solicitud.get('usuario_solicita', 'N/A')}  
                            **💰 Total Orden:** ${orden.get('total', 0):.2f}
                            """)
                        
                        # Información del producto
                        st.markdown(f"""
                        <div class="producto-info">
                            <strong>🍽️ Producto a Anular:</strong><br>
                            {item.get('cantidad', 0)}x {item.get('nombre', 'N/A')} - ${item.get('precio_unitario', 0):.2f}
                            <br><strong>Total del producto:</strong> ${item.get('cantidad', 0) * item.get('precio_unitario', 0):.2f}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Motivo de la solicitud
                        st.markdown("**💬 Motivo de la Anulación:**")
                        st.info(solicitud.get('motivo', 'Sin motivo especificado'))
                        
                        # Acciones del administrador
                        st.markdown("**🔧 Acciones del Administrador:**")
                        
                        # Formulario para aprobar/rechazar
                        with st.form(f"form_{solicitud['_id']}"):
                            motivo_admin = st.text_area(
                                "Comentario del Administrador (opcional):",
                                key=f"admin_comment_{solicitud['_id']}",
                                placeholder="Ej: Aprobado por política de satisfacción al cliente, Rechazado - no cumple criterios, etc."
                            )
                            
                            col_actions = st.columns([1, 1, 2])
                            
                            with col_actions[0]:
                                aprobar = st.form_submit_button("✅ Aprobar", type="primary")
                            
                            with col_actions[1]:
                                rechazar = st.form_submit_button("❌ Rechazar", type="secondary")
                            
                            # Procesar decisión
                            if aprobar:
                                usuario_admin = st.session_state.get('user_data', {}).get('usuario', 'Admin')
                                success, message = couchdb_utils.procesar_solicitud_anulacion(
                                    db, solicitud['_id'], 'aprobada', usuario_admin, motivo_admin
                                )
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                            
                            elif rechazar:
                                usuario_admin = st.session_state.get('user_data', {}).get('usuario', 'Admin')
                                success, message = couchdb_utils.procesar_solicitud_anulacion(
                                    db, solicitud['_id'], 'rechazada', usuario_admin, motivo_admin
                                )
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                        
                        st.markdown("---")
        
        with tab_ordenes:
            st.subheader("🗑️ Solicitudes de Anulación de Órdenes Completas")
            
            # Obtener solicitudes de anulación completa
            solicitudes_ordenes = couchdb_utils.obtener_solicitudes_anulacion_completa_pendientes(db)
            
            # Mostrar badge de notificación si hay solicitudes pendientes
            if solicitudes_ordenes:
                st.markdown(f"""
                <div style="background-color: #ff6b6b; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
                    🔔 <strong>{len(solicitudes_ordenes)} solicitud(es) de anulación completa pendiente(s)</strong> requieren su atención inmediata
                </div>
                """, unsafe_allow_html=True)
            
            if not solicitudes_ordenes:
                st.info("✅ No hay solicitudes de anulación completa pendientes.")
            else:
                st.success(f"📋 {len(solicitudes_ordenes)} solicitud(es) de anulación completa pendiente(s) de revisión")
                
                for solicitud in solicitudes_ordenes:
                    orden_id = solicitud.get('orden_id')
                    
                    # Obtener información de la orden
                    orden = ordenes.get(orden_id, {})
                    mesa = mesas.get(orden.get('mesa_id'), {})
                    mesero = meseros.get(orden.get('mesero_id'), {})
                    
                    # Fechas
                    fecha_solicitud = convert_to_local_time(solicitud.get('fecha_solicitud'))
                    fecha_sol_str = fecha_solicitud.strftime('%d/%m/%Y %H:%M') if fecha_solicitud else 'N/A'
                    
                    # Calcular total de items activos
                    items_activos = [item for item in orden.get('items', []) if not item.get('anulado', False)]
                    total_activo = sum(item.get('cantidad', 0) * item.get('precio_unitario', 0) for item in items_activos)
                    
                    with st.expander(f"🗑️ ORDEN COMPLETA #{orden.get('numero_orden', 'N/A')} - {mesa.get('descripcion', 'Mesa N/A')} - ${total_activo:.2f}", expanded=True):
                        st.markdown(f"""
                        <div class="solicitud-card solicitud-pendiente">
                            <h5>🕒 SOLICITUD PENDIENTE DE ANULACIÓN COMPLETA</h5>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_orden1, col_orden2 = st.columns([2, 1])
                        
                        with col_orden1:
                            st.markdown(f"""
                            **📋 Información de la Orden:**
                            - **Número:** #{orden.get('numero_orden', 'N/A')}
                            - **🏠 Mesa:** {mesa.get('descripcion', 'N/A')}
                            - **👤 Mesero:** {mesero.get('nombre', 'N/A')}
                            - **💰 Total:** ${total_activo:.2f}
                            - **🍽️ Items activos:** {len(items_activos)}
                            - **🕐 Solicitud:** {fecha_sol_str}
                            - **👤 Solicitado por:** {solicitud.get('usuario_solicita', 'N/A')}
                            """)
                            
                            st.markdown("**💬 Motivo de la Anulación:**")
                            st.info(solicitud.get('motivo', 'Sin motivo especificado'))
                        
                        with col_orden2:
                            st.markdown("**🍽️ Items a Anular:**")
                            for idx, item in enumerate(items_activos):
                                st.markdown(f"• {item.get('cantidad', 0)}x {item.get('nombre', 'N/A')} - ${item.get('precio_unitario', 0):.2f}")
                        
                        st.markdown("---")
                        
                        # Sección de respuesta del administrador
                        st.markdown("**🔧 Respuesta del Administrador:**")
                        
                        motivo_admin_orden = st.text_area(
                            "Comentario/Motivo (opcional):",
                            key=f"motivo_admin_orden_{solicitud['_id']}",
                            placeholder="Comentario sobre la decisión tomada..."
                        )
                        
                        col_decision_orden = st.columns([1, 1, 2])
                        
                        with col_decision_orden[0]:
                            if st.button("✅ APROBAR", 
                                      key=f"aprobar_orden_{solicitud['_id']}", 
                                      type="primary",
                                      use_container_width=True):
                                usuario_admin = st.session_state.get('user_data', {}).get('usuario', 'Admin')
                                success, message = couchdb_utils.procesar_solicitud_anulacion_completa(
                                    db, solicitud['_id'], 'aprobar', usuario_admin, motivo_admin_orden
                                )
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"❌ Error: {message}")
                        
                        with col_decision_orden[1]:
                            if st.button("❌ RECHAZAR", 
                                      key=f"rechazar_orden_{solicitud['_id']}", 
                                      type="secondary",
                                      use_container_width=True):
                                if motivo_admin_orden.strip():
                                    usuario_admin = st.session_state.get('user_data', {}).get('usuario', 'Admin')
                                    success, message = couchdb_utils.procesar_solicitud_anulacion_completa(
                                        db, solicitud['_id'], 'rechazar', usuario_admin, motivo_admin_orden
                                    )
                                    
                                    if success:
                                        st.success(f"✅ {message}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Error: {message}")
                                else:
                                    st.error("❌ Debes proporcionar un motivo para rechazar la solicitud")
                        
                        with col_decision_orden[2]:
                            st.markdown("**⚠️ IMPORTANTE:**")
                            st.warning("La anulación completa revertirá TODOS los ingredientes al inventario y marcará la orden como anulada.")

        with tab_historial:
            st.subheader("Historial de Solicitudes de Anulación")
            
            # Filtros
            col_filtros = st.columns([1, 1, 1])
            with col_filtros[0]:
                filtro_estado = st.selectbox(
                    "Estado:",
                    options=["Todos", "Aprobadas", "Rechazadas"],
                    key="filtro_estado_historial"
                )
            
            with col_filtros[1]:
                fecha_desde = st.date_input("Desde:", key="fecha_desde_historial")
            
            with col_filtros[2]:
                fecha_hasta = st.date_input("Hasta:", key="fecha_hasta_historial")
            
            # Filtrar solicitudes del historial
            historial = [s for s in all_solicitudes if s.get('estado') != 'pendiente']
            
            if filtro_estado != "Todos":
                estado_filtro = 'aprobada' if filtro_estado == 'Aprobadas' else 'rechazada'
                historial = [s for s in historial if s.get('estado') == estado_filtro]
            
            if not historial:
                st.info("📝 No hay solicitudes en el historial con los filtros aplicados.")
            else:
                # Ordenar por fecha de procesamiento (más reciente primero)
                historial.sort(key=lambda x: x.get('fecha_procesamiento', ''), reverse=True)
                
                st.info(f"📋 Mostrando {len(historial)} solicitud(es) procesada(s)")
                
                for solicitud in historial:
                    orden_id = solicitud.get('orden_id')
                    item_index = solicitud.get('item_index', 0)
                    estado = solicitud.get('estado', '')
                    
                    # Obtener información de la orden
                    orden = ordenes.get(orden_id, {})
                    mesa = mesas.get(orden.get('mesa_id'), {})
                    mesero = meseros.get(orden.get('mesero_id'), {})
                    
                    # Obtener información del producto
                    items = orden.get('items', [])
                    if item_index < len(items):
                        item = items[item_index]
                    else:
                        item = {'nombre': 'Producto no encontrado', 'cantidad': 0, 'precio_unitario': 0}
                    
                    # Fechas
                    fecha_solicitud = convert_to_local_time(solicitud.get('fecha_solicitud'))
                    fecha_procesamiento = convert_to_local_time(solicitud.get('fecha_procesamiento'))
                    fecha_sol_str = fecha_solicitud.strftime('%d/%m/%Y %H:%M') if fecha_solicitud else 'N/A'
                    fecha_proc_str = fecha_procesamiento.strftime('%d/%m/%Y %H:%M') if fecha_procesamiento else 'N/A'
                    
                    # Determinar estilo CSS
                    css_class = "solicitud-aprobada" if estado == 'aprobada' else "solicitud-rechazada"
                    icono_estado = "✅ APROBADA" if estado == 'aprobada' else "❌ RECHAZADA"
                    
                    with st.expander(f"{icono_estado} - Orden #{orden.get('numero_orden', 'N/A')} - {item.get('nombre', 'N/A')} ({fecha_proc_str})"):
                        st.markdown(f"""
                        <div class="solicitud-card {css_class}">
                            <h5>Estado: {icono_estado}</h5>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_hist1, col_hist2 = st.columns([1, 1])
                        
                        with col_hist1:
                            st.markdown(f"""
                            **📋 Orden:** #{orden.get('numero_orden', 'N/A')}  
                            **🏠 Mesa:** {mesa.get('descripcion', 'N/A')}  
                            **👤 Mesero:** {mesero.get('nombre', 'N/A')}  
                            **🍽️ Producto:** {item.get('cantidad', 0)}x {item.get('nombre', 'N/A')} - ${item.get('precio_unitario', 0):.2f}
                            """)
                        
                        with col_hist2:
                            st.markdown(f"""
                            **🕐 Solicitud:** {fecha_sol_str}  
                            **⚡ Procesado:** {fecha_proc_str}  
                            **👤 Solicitado por:** {solicitud.get('usuario_solicita', 'N/A')}  
                            **🔧 Procesado por:** {solicitud.get('usuario_procesa', 'N/A')}
                            """)
                        
                        st.markdown("**💬 Motivo Original:**")
                        st.info(solicitud.get('motivo', 'Sin motivo especificado'))
                        
                        if solicitud.get('motivo_admin'):
                            st.markdown("**🔧 Comentario del Administrador:**")
                            st.success(solicitud.get('motivo_admin'))
    
    else:
        st.error("❌ No se pudo conectar a la base de datos.")
        
else:
    st.info("🔐 Por favor, inicia sesión para acceder a la gestión de anulaciones.")