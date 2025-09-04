# pages/configuracion.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone
import uuid

# Configuración básica
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)
st.set_page_config(layout="wide", page_title="Configuracion del Sistema", page_icon="../assets/LOGO.png")

# Estilos CSS
st.markdown("""
<style>
    .config-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #f8f9fa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-card {
        border-left: 5px solid #28a745;
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-card {
        border-left: 5px solid #ffc107;
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-card {
        border-left: 5px solid #17a2b8;
        background-color: #d1ecf1;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .stock-alert {
        border-left: 5px solid #dc3545;
        background-color: #f8d7da;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    # Verificar permisos de acceso
    user_role = st.session_state.get('user_data', {}).get('id_rol', 0)
    if user_role not in [1, 6]:  # Solo administradores y operativos
        st.error("❌ Acceso denegado. Solo los administradores y operativos pueden acceder a la configuración.")
        st.info("💡 Esta funcionalidad está reservada para usuarios con rol de administrador o operativo.")
        st.stop()
    
    if db:
        st.title("⚙️ Configuración del Sistema")
        
        # Funciones auxiliares
        def obtener_configuracion():
            """Obtiene la configuración actual del sistema"""
            try:
                config_docs = list(db.find({"selector": {"type": "configuracion"}}))
                if config_docs:
                    return config_docs[0]
                else:
                    # Crear configuración por defecto
                    config_default = {
                        "_id": f"configuracion:{str(uuid.uuid4())}",
                        "type": "configuracion",
                        "numero_orden_inicial": 1,
                        "numero_ticket_inicial": 1,
                        "alertas_stock": {},
                        "fecha_creacion": datetime.now(timezone.utc).isoformat(),
                        "ultima_modificacion": datetime.now(timezone.utc).isoformat()
                    }
                    db.save(config_default)
                    return config_default
            except Exception as e:
                st.error(f"Error al obtener configuración: {e}")
                return None

        def guardar_configuracion(config):
            """Guarda la configuración actualizada"""
            try:
                config["ultima_modificacion"] = datetime.now(timezone.utc).isoformat()
                db.save(config)
                return True
            except Exception as e:
                st.error(f"Error al guardar configuración: {e}")
                return False

        def obtener_ingredientes_activos():
            """Obtiene todos los ingredientes activos"""
            try:
                ingredientes = couchdb_utils.get_documents_by_partition(db, "ingredientes")
                return [i for i in ingredientes if i.get('activo', 0) == 1]
            except Exception as e:
                st.error(f"Error al obtener ingredientes: {e}")
                return []

        # Obtener configuración actual
        configuracion = obtener_configuracion()
        if not configuracion:
            st.error("No se pudo cargar la configuración del sistema.")
            st.stop()

        # Pestañas principales
        tab_numeracion, tab_stock_alerts = st.tabs(["🔢 Numeracion", "⚠️ Alertas de Stock"])

        # === TAB NUMERACIÓN ===
        with tab_numeracion:
            st.markdown("""
            <div class="config-card">
                <h3>🔢 Configuración de Numeración</h3>
                <p>Configure desde qué número desea que comiencen las órdenes y tickets en el sistema.</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🧾 Configuración de Órdenes")
                
                # Número inicial de órdenes
                numero_orden_inicial = st.number_input(
                    "Número inicial para órdenes:",
                    min_value=1,
                    max_value=999999,
                    value=configuracion.get('numero_orden_inicial', 1),
                    step=1,
                    help="El próximo número de orden será este valor o superior"
                )

                # Mostrar información actual
                try:
                    # Obtener el último número de orden usado
                    last_order = db.view('_design/orders/_view/by_order_number',
                                       limit=1,
                                       descending=True,
                                       partition="ordenes"
                                       ).rows
                    
                    ultimo_numero_orden = int(last_order[0].key) if last_order else 0
                    proximo_numero_orden = max(numero_orden_inicial, ultimo_numero_orden + 1)
                    
                    st.markdown(f"""
                    <div class="info-card">
                        <strong>📊 Estado Actual:</strong><br>
                        • Último número usado: <strong>{ultimo_numero_orden}</strong><br>
                        • Próximo número: <strong>{proximo_numero_orden}</strong><br>
                        • Configuración: <strong>{numero_orden_inicial}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.warning(f"No se pudo obtener información de órdenes: {e}")

            with col2:
                st.subheader("🎫 Configuración de Tickets")
                
                # Número inicial de tickets
                numero_ticket_inicial = st.number_input(
                    "Número inicial para tickets:",
                    min_value=1,
                    max_value=999999,
                    value=configuracion.get('numero_ticket_inicial', 1),
                    step=1,
                    help="El próximo número de ticket será este valor o superior"
                )

                # Mostrar información actual
                try:
                    # Obtener el último número de ticket usado
                    all_tickets = [doc for doc in db if doc.get('type') == 'tickets']
                    ultimo_numero_ticket = max([tkt.get('numero_ticket', 0) for tkt in all_tickets] or [0])
                    proximo_numero_ticket = max(numero_ticket_inicial, ultimo_numero_ticket + 1)
                    
                    st.markdown(f"""
                    <div class="info-card">
                        <strong>📊 Estado Actual:</strong><br>
                        • Último número usado: <strong>{ultimo_numero_ticket}</strong><br>
                        • Próximo número: <strong>{proximo_numero_ticket}</strong><br>
                        • Configuración: <strong>{numero_ticket_inicial}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.warning(f"No se pudo obtener información de tickets: {e}")

            # Botón para guardar configuración de numeración
            st.markdown("---")
            col_save, col_reset = st.columns([1, 1])
            
            with col_save:
                if st.button("💾 Guardar Configuración de Numeración", type="primary", use_container_width=True):
                    configuracion['numero_orden_inicial'] = numero_orden_inicial
                    configuracion['numero_ticket_inicial'] = numero_ticket_inicial
                    
                    if guardar_configuracion(configuracion):
                        st.success("✅ Configuración de numeración guardada exitosamente!")
                        couchdb_utils.log_action(
                            db, 
                            st.session_state.get('user_data', {}).get('usuario', 'Sistema'),
                            f"Configuración actualizada - Órdenes desde: {numero_orden_inicial}, Tickets desde: {numero_ticket_inicial}"
                        )
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar la configuración.")

            with col_reset:
                if st.button("🔄 Restablecer a Valores por Defecto", type="secondary", use_container_width=True):
                    configuracion['numero_orden_inicial'] = 1
                    configuracion['numero_ticket_inicial'] = 1
                    
                    if guardar_configuracion(configuracion):
                        st.success("✅ Configuración restablecida a valores por defecto!")
                        st.rerun()

            # Advertencias importantes
            st.markdown("""
            <div class="warning-card">
                <strong>⚠️ Importante:</strong><br>
                • Los números configurados solo afectan a las <strong>nuevas órdenes y tickets</strong><br>
                • Si configura un número menor al último usado, el sistema usará el siguiente disponible<br>
                • Esta configuración no afecta órdenes o tickets ya creados<br>
                • Los cambios se aplicarán inmediatamente después de guardar
            </div>
            """, unsafe_allow_html=True)

        # === TAB ALERTAS DE STOCK ===
        with tab_stock_alerts:
            st.markdown("""
            <div class="config-card">
                <h3>⚠️ Configuración de Alertas de Stock Bajo</h3>
                <p>Configure alertas personalizadas para cada producto cuando el stock esté bajo.</p>
            </div>
            """, unsafe_allow_html=True)

            # Obtener ingredientes
            ingredientes = obtener_ingredientes_activos()
            
            if not ingredientes:
                st.warning("No se encontraron ingredientes activos en el sistema.")
            else:
                st.subheader(f"📦 Configurar Alertas ({len(ingredientes)} productos)")
                
                # Obtener alertas actuales
                alertas_actuales = configuracion.get('alertas_stock', {})
                
                # Crear formulario para todas las alertas
                with st.form("form_alertas_stock"):
                    alertas_actualizadas = {}
                    
                    # Mostrar productos en columnas
                    num_cols = 3
                    cols = st.columns(num_cols)
                    
                    for idx, ingrediente in enumerate(ingredientes):
                        col_idx = idx % num_cols
                        ingrediente_id = ingrediente['_id']
                        nombre = ingrediente.get('descripcion', 'Sin nombre')
                        
                        with cols[col_idx]:
                            # Obtener stock actual si existe
                            stock_actual = ingrediente.get('cantidad', 0)
                            unidad = ingrediente.get('unidad', 'unidad')
                            
                            st.markdown(f"**{nombre}**")
                            st.caption(f"Stock actual: {stock_actual} {unidad}")
                            
                            # Input para la alerta
                            alerta_actual = alertas_actuales.get(ingrediente_id, {}).get('minimo', 10)
                            alerta_minima = st.number_input(
                                f"Stock mínimo:",
                                min_value=0,
                                max_value=9999,
                                value=alerta_actual,
                                step=1,
                                key=f"alerta_{ingrediente_id}",
                                help=f"Alerta cuando el stock de {nombre} esté por debajo de este número"
                            )
                            
                            alertas_actualizadas[ingrediente_id] = {
                                'nombre': nombre,
                                'minimo': alerta_minima,
                                'unidad': unidad,
                                'activo': True
                            }
                            
                            # Mostrar estado actual
                            if stock_actual <= alerta_minima and stock_actual > 0:
                                st.markdown('<div class="stock-alert">⚠️ STOCK BAJO</div>', unsafe_allow_html=True)
                            elif stock_actual == 0:
                                st.markdown('<div class="stock-alert">🚨 SIN STOCK</div>', unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    # Botón para guardar
                    col_guardar, col_reset_alerts = st.columns([1, 1])
                    
                    with col_guardar:
                        guardar_alertas = st.form_submit_button("💾 Guardar Alertas de Stock", type="primary", use_container_width=True)
                    
                    with col_reset_alerts:
                        reset_alertas = st.form_submit_button("🔄 Restablecer Alertas", type="secondary", use_container_width=True)
                    
                    if guardar_alertas:
                        configuracion['alertas_stock'] = alertas_actualizadas
                        
                        if guardar_configuracion(configuracion):
                            st.success("✅ Alertas de stock configuradas exitosamente!")
                            couchdb_utils.log_action(
                                db, 
                                st.session_state.get('user_data', {}).get('usuario', 'Sistema'),
                                f"Alertas de stock actualizadas para {len(alertas_actualizadas)} productos"
                            )
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar las alertas.")
                    
                    elif reset_alertas:
                        # Establecer alertas por defecto (10 para todos)
                        alertas_default = {}
                        for ingrediente in ingredientes:
                            ingrediente_id = ingrediente['_id']
                            alertas_default[ingrediente_id] = {
                                'nombre': ingrediente.get('descripcion', 'Sin nombre'),
                                'minimo': 10,
                                'unidad': ingrediente.get('unidad', 'unidad'),
                                'activo': True
                            }
                        
                        configuracion['alertas_stock'] = alertas_default
                        
                        if guardar_configuracion(configuracion):
                            st.success("✅ Alertas restablecidas a valores por defecto (10 unidades)!")
                            st.rerun()

                # === MOSTRAR ALERTAS ACTIVAS ===
                st.markdown("---")
                st.subheader("🚨 Alertas Activas de Stock Bajo")
                
                alertas_activas = []
                
                for ingrediente in ingredientes:
                    ingrediente_id = ingrediente['_id']
                    stock_actual = ingrediente.get('cantidad', 0)
                    
                    if ingrediente_id in alertas_actuales:
                        minimo = alertas_actuales[ingrediente_id].get('minimo', 10)
                        nombre = ingrediente.get('descripcion', 'Sin nombre')
                        unidad = ingrediente.get('unidad', 'unidad')
                        
                        if stock_actual <= minimo:
                            alertas_activas.append({
                                'nombre': nombre,
                                'stock_actual': stock_actual,
                                'stock_minimo': minimo,
                                'unidad': unidad,
                                'critico': stock_actual == 0
                            })

                if alertas_activas:
                    # Separar alertas críticas (stock 0) de las normales
                    alertas_criticas = [a for a in alertas_activas if a['critico']]
                    alertas_normales = [a for a in alertas_activas if not a['critico']]
                    
                    if alertas_criticas:
                        st.markdown("### 🚨 CRÍTICAS (Sin Stock)")
                        for alerta in alertas_criticas:
                            st.markdown(f"""
                            <div class="stock-alert">
                                <strong>🚨 {alerta['nombre']}</strong><br>
                                Stock actual: <strong>0 {alerta['unidad']}</strong> | 
                                Mínimo configurado: <strong>{alerta['stock_minimo']} {alerta['unidad']}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if alertas_normales:
                        st.markdown("### ⚠️ Stock Bajo")
                        for alerta in alertas_normales:
                            st.markdown(f"""
                            <div class="warning-card">
                                <strong>⚠️ {alerta['nombre']}</strong><br>
                                Stock actual: <strong>{alerta['stock_actual']} {alerta['unidad']}</strong> | 
                                Mínimo configurado: <strong>{alerta['stock_minimo']} {alerta['unidad']}</strong>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="success-card">
                        <strong>✅ Todos los productos tienen stock suficiente</strong><br>
                        No hay alertas activas en este momento.
                    </div>
                    """, unsafe_allow_html=True)

                # Información adicional
                st.markdown("""
                <div class="info-card">
                    <strong>💡 Información sobre las Alertas:</strong><br>
                    • Las alertas se verifican en tiempo real en todas las páginas del sistema<br>
                    • Los productos con stock 0 se marcan como <strong>CRÍTICOS</strong><br>
                    • Las alertas aparecen cuando el stock actual es igual o menor al mínimo configurado<br>
                    • Puede configurar diferentes límites para cada producto según sus necesidades<br>
                    • Las alertas solo aplican a ingredientes marcados como <strong>activos</strong>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.error("❌ No se pudo conectar a la base de datos.")

else:
    st.info("🔐 Por favor, inicia sesión para acceder a la configuración del sistema.")