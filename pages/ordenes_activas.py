# pages/ordenes_activas.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone
import uuid
import base64

# Configuración básica
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
CURRENT_PARTITION_KEY = "ordenes"
couchdb_utils.generarLogin(archivo_actual_relativo)
st.set_page_config(layout="wide", page_title="Órdenes Activas", page_icon="../assets/LOGO.png")

# Estilos CSS
st.markdown("""
<style>
    .order-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #f9f9f9;
    }
    .item-row {
        border-bottom: 1px solid #eee;
        padding: 8px 0;
    }
    .action-button {
        margin: 5px;
    }
    .notification-badge {
        background-color: #dc3545;
        color: white;
        padding: 4px 8px;
        border-radius: 50%;
        font-weight: bold;
        margin-left: 5px;
    }
    .beverage-ready {
        background-color: #d4edda;
        border: 1px solid #28a745;
        border-radius: 5px;
        padding: 8px;
        margin: 5px 0;
        color: #155724;
    }
    .beverage-process {
        background-color: #fff3cd;
        border: 1px solid #fd7e14;
        border-radius: 5px;
        padding: 8px;
        margin: 5px 0;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # Limpieza automática de estados inconsistentes
        if 'orden_editar' in st.session_state and st.session_state.orden_editar is None:
            del st.session_state.orden_editar
        # --- Funciones para detectar tipos de items ---
        def obtener_bebidas_ids():
            platos = couchdb_utils.get_documents_by_partition(db, "platos")
            menus = couchdb_utils.get_documents_by_partition(db, "menu")
            
            # Encontrar el menú "bar"
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
                
                # Detectar por menú "bar" (PRIORITARIO)
                es_bebida_menu = False
                if menu_bar and menu_id == menu_bar.get('_id'):
                    es_bebida_menu = True
                
                # Detectar por categoría
                es_bebida_categoria = any(cat in categoria.lower() for cat in ['bar', 'bebida', 'bebidas', 'drink'])
                
                # Detectar por palabras clave (fallback)
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
                
                if es_bebida_menu or es_bebida_categoria or es_bebida_keyword:
                    bebidas_ids.append(plato['_id'])
            
            return bebidas_ids

        def obtener_platos_cocina_ids():
            platos = couchdb_utils.get_documents_by_partition(db, "platos")
            menus = couchdb_utils.get_documents_by_partition(db, "menu")
            
            # Encontrar el menú "cocina"
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
                
                # Detectar por menú "cocina" (PRIORITARIO)
                es_plato_menu = False
                if menu_cocina and menu_id == menu_cocina.get('_id'):
                    es_plato_menu = True
                
                # Detectar por categoría
                es_plato_categoria = any(cat in categoria.lower() for cat in ['cocina', 'comida', 'platos', 'food'])
                
                # Detectar por palabras clave (fallback)
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

        bebidas_ids = obtener_bebidas_ids()
        platos_cocina_ids = obtener_platos_cocina_ids()

        # --- Obtener información del usuario logueado ---
        user_data = st.session_state.get('user_data', {})
        user_role = user_data.get('id_rol')
        user_id = user_data.get('_id')

        # --- Obtener datos ---
        todas_ordenes = couchdb_utils.get_documents_by_partition(db, "ordenes")
        
        # Filtrar ordenes segun el rol del usuario
        orden_editar_id = st.session_state.get('orden_editar', {}).get('_id') if st.session_state.get('orden_editar') else None
        
        if user_role == 3:
            # Para meseros (rol 3): solo mostrar sus propias ordenes
            ordenes_pendientes = [doc for doc in todas_ordenes 
                                if doc.get('estado') == 'pendiente' and 
                                doc.get('mesero_id') == user_id and
                                (not orden_editar_id or doc['_id'] != orden_editar_id)]
        else:
            # Para otros roles: mostrar todas las ordenes pendientes
            ordenes_pendientes = [doc for doc in todas_ordenes 
                                if doc.get('estado') == 'pendiente' and 
                                (not orden_editar_id or doc['_id'] != orden_editar_id)]
        
        # Obtener datos necesarios
        mesas = {m['_id']: m for m in couchdb_utils.get_documents_by_partition(db, "mesas")}
        # Obtener todos los usuarios y filtrar meseros (rol 3)
        todos_usuarios = couchdb_utils.get_documents_by_partition(db, "Usuario")
        meseros = {m['_id']: m for m in todos_usuarios if m.get('id_rol') == 3}
        
        # --- Display PDF and Download Button if a ticket was just processed ---
        if st.session_state.get('just_processed_ticket_display') is not None:
            info = st.session_state.pop('just_processed_ticket_display')
            st.success(info['message'])
            
            st.download_button(
                label="📄 Descargar Orden en PDF",
                data=info['pdf_data'],
                file_name=info['file_name'],
                mime="application/pdf"
            )
            
            # Optional: Display PDF directly using base64
            base64_pdf = base64.b64encode(info['pdf_data']).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border: none;"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            st.markdown("---") # Add a separator after displaying PDF

        # --- Encabezado ---
        col_title, col_refresh = st.columns([3, 1])
        with col_title:
            st.title("🍽️ Órdenes Activas")
        with col_refresh:
            if st.button("🔄 Actualizar", type="primary", use_container_width=True, help="Actualizar estado de órdenes"):
                st.rerun()
        
        # Mostrar información del filtrado para meseros
        if user_role == 3:
            st.info(f"📋 Mostrando solo tus órdenes ({len(ordenes_pendientes)} órdenes activas)")
        
        st.markdown("---")
        
        # --- Verificar si hay órdenes ---
        if not ordenes_pendientes:
            if user_role == 3:
                st.info("No tienes órdenes activas en este momento.")
            else:
                st.info("No hay órdenes activas en este momento.")
        else:
            # Calcular total de bebidas y platos listos para notificación global
            total_bebidas_listas = 0
            total_platos_listos = 0
            
            for orden in ordenes_pendientes:
                for item in orden.get('items', []):
                    if item.get('plato_id') in bebidas_ids and item.get('despachado_bar', False):
                        total_bebidas_listas += item.get('cantidad', 1)
                    if item.get('plato_id') in platos_cocina_ids and item.get('despachado_cocina', False):
                        total_platos_listos += item.get('cantidad', 1)
            
            # Notificaciones separadas para bebidas y platos
            if total_bebidas_listas > 0:
                st.markdown(f"""
                <div style="background-color: #d4edda; border: 2px solid #28a745; border-radius: 10px; padding: 15px; margin: 10px 0; text-align: center;">
                    <h3>🚨 ATENCIÓN: <span class="notification-badge">{total_bebidas_listas}</span> BEBIDA(S) LISTA(S) PARA RETIRAR</h3>
                    <p>Revisa las órdenes activas para ver qué bebidas están listas</p>
                </div>
                """, unsafe_allow_html=True)
            
            if total_platos_listos > 0:
                st.markdown(f"""
                <div style="background-color: #fff3cd; border: 2px solid #fd7e14; border-radius: 10px; padding: 15px; margin: 10px 0; text-align: center;">
                    <h3>🚨 ATENCIÓN: <span class="notification-badge">{total_platos_listos}</span> PLATO(S) LISTO(S) PARA SERVIR</h3>
                    <p>Revisa las órdenes activas para ver qué platos están listos</p>
                </div>
                """, unsafe_allow_html=True)
            
            # --- Mostrar órdenes en 2 columnas ---
            # Ordenar por fecha de creación para determinar orden de llegada
            ordenes_pendientes.sort(key=lambda x: x.get('fecha_creacion', ''))
            
            # Mostrar en grid de 2 columnas
            for i in range(0, len(ordenes_pendientes), 2):
                col_orden1, col_orden2 = st.columns(2)
                
                for j, col_orden in enumerate([col_orden1, col_orden2]):
                    if i + j < len(ordenes_pendientes):
                        orden = ordenes_pendientes[i + j]
                        numero_llegada = i + j + 1  # Número correlativo de llegada
                        
                        with col_orden:
                            # Contar bebidas y platos listos en esta orden específica
                            bebidas_listas_orden = 0
                            platos_listos_orden = 0
                            
                            for item in orden.get('items', []):
                                if item.get('plato_id') in bebidas_ids and item.get('despachado_bar', False):
                                    bebidas_listas_orden += item.get('cantidad', 1)
                                if item.get('plato_id') in platos_cocina_ids and item.get('despachado_cocina', False):
                                    platos_listos_orden += item.get('cantidad', 1)
                            
                            # Crear badge de notificación para la orden
                            items_listos_total = bebidas_listas_orden + platos_listos_orden
                            
                            # Crear título con número de llegada grande
                            mesa_nombre = mesas.get(orden.get('mesa_id'), {}).get('descripcion', 'Desconocida')
                            
                            # Número grande de orden de llegada con estilo similar a bar/cocina
                            orden_color = "#28a745" if items_listos_total > 0 else "#6c757d"
                            
                            # Construir el HTML completo de manera más limpia
                            html_content = f'<div style="border: 2px solid {orden_color}; border-radius: 10px; padding: 10px; margin: 10px 0; background-color: #f8f9fa;">'
                            html_content += '<div style="display: flex; align-items: center; margin-bottom: 10px;">'
                            html_content += f'<div style="display: flex; align-items: center; justify-content: center; width: 60px; height: 60px; background: {orden_color}; border-radius: 10px; margin-right: 15px;">'
                            html_content += f'<span style="font-size: 32px; font-weight: bold; color: white;">{numero_llegada}</span>'
                            html_content += '</div>'
                            html_content += '<div style="flex: 1;">'
                            html_content += f'<h4 style="margin: 0; color: #333;">Orden #{orden.get("numero_orden", "S/N")}</h4>'
                            html_content += f'<p style="margin: 0; color: #666;">Mesa: {mesa_nombre}</p>'
                            if items_listos_total > 0:
                                html_content += f'<p style="margin: 0; color: #28a745; font-weight: bold;">🚨 ITEMS LISTOS: {items_listos_total}</p>'
                            html_content += '</div>'
                            html_content += '</div>'
                            html_content += '</div>'
                            
                            st.markdown(html_content, unsafe_allow_html=True)
                            
                            expandir_por_defecto = items_listos_total > 0
                            titulo_orden = f"Ver Detalles - Orden #{orden.get('numero_orden', 'S/N')}"
                            
                            with st.expander(titulo_orden, expanded=expandir_por_defecto):
                                st.write(f"**Mesero:** {meseros.get(orden.get('mesero_id'), {}).get('nombre', 'Desconocido')}")
                                st.write(f"**Total:** ${orden.get('total', 0):.2f}")
                                
                                if orden.get('items'):
                                    st.write("**Items:**")
                                    for idx, item in enumerate(orden['items']):
                                        # Verificar si es una bebida o plato de cocina
                                        es_bebida = item.get('plato_id') in bebidas_ids
                                        es_plato_cocina = item.get('plato_id') in platos_cocina_ids
                                        
                                        # Crear el texto del item
                                        item_text = f"• {item['cantidad']}x {item['nombre']} - ${item['precio_unitario']:.2f}"
                                        
                                        # Verificar si el item está anulado
                                        if item.get('anulado', False):
                                            # Mostrar item anulado con estilo tachado
                                            fecha_anulacion = item.get('fecha_anulacion', '')
                                            usuario_anula = item.get('usuario_anula', 'N/A')
                                            
                                            st.markdown(f"""
                                            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 8px; margin: 5px 0; color: #721c24;">
                                                ❌ <s>{item_text}</s> <strong>ANULADO</strong>
                                                <br><small>🕐 Anulado por: {usuario_anula}</small>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            continue  # Saltar el resto de la lógica para este item
                                        
                                        # Verificar si el item está en proceso de anulación
                                        elif item.get('en_proceso_anulacion', False):
                                            # Mostrar item en proceso de anulación
                                            usuario_solicita = item.get('usuario_solicita_anulacion', 'N/A')
                                            motivo_solicitud = item.get('motivo_solicitud_anulacion', 'Sin motivo especificado')
                                            
                                            st.markdown(f"""
                                            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 8px; margin: 5px 0; color: #856404;">
                                                ⏳ {item_text} <strong>EN PROCESO DE ANULACIÓN</strong>
                                                <br><small>🔔 Solicitado por: {usuario_solicita}</small>
                                                <br><small>💬 Motivo: {motivo_solicitud}</small>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                            if item.get('comentarios'):
                                                st.caption(f"   💬 Notas: {item['comentarios']}")
                                            
                                            # Mostrar botones de aprobación/rechazo para administradores y operativos
                                            user_role = st.session_state.get('user_data', {}).get('id_rol', 0)
                                            if user_role in [1, 6]:  # Admin y Operativo
                                                col_aprobar, col_rechazar = st.columns(2)
                                                
                                                with col_aprobar:
                                                    if st.button("✅ Aprobar", key=f"approve_item_{orden['_id']}_{idx}", type="primary", use_container_width=True):
                                                        # Aprobar anulación
                                                        usuario_admin = st.session_state.get('user_data', {}).get('usuario', 'Administrador')
                                                        success, message = couchdb_utils.aprobar_anulacion(
                                                            db, item.get('solicitud_anulacion_id'), usuario_admin
                                                        )
                                                        
                                                        if success:
                                                            st.success("✅ Anulación aprobada exitosamente")
                                                            st.rerun()
                                                        else:
                                                            st.error(f"❌ Error al aprobar: {message}")
                                                
                                                with col_rechazar:
                                                    if st.button("❌ Rechazar", key=f"reject_item_{orden['_id']}_{idx}", type="secondary", use_container_width=True):
                                                        st.session_state[f"show_reject_form_{orden['_id']}_{idx}"] = True
                                                        st.rerun()
                                                
                                                # Formulario de rechazo
                                                if st.session_state.get(f"show_reject_form_{orden['_id']}_{idx}", False):
                                                    with st.container():
                                                        st.markdown("**Motivo del Rechazo:**")
                                                        motivo_rechazo = st.text_area(
                                                            "¿Por qué se rechaza esta anulación?",
                                                            key=f"reject_reason_{orden['_id']}_{idx}",
                                                            placeholder="Ej: Producto ya está en preparación, no se puede anular..."
                                                        )
                                                        
                                                        col_confirmar, col_cancelar = st.columns(2)
                                                        with col_confirmar:
                                                            if st.button("🚫 Confirmar Rechazo", key=f"confirm_reject_{orden['_id']}_{idx}", type="primary"):
                                                                if motivo_rechazo.strip():
                                                                    usuario_admin = st.session_state.get('user_data', {}).get('usuario', 'Administrador')
                                                                    success, message = couchdb_utils.rechazar_anulacion(
                                                                        db, item.get('solicitud_anulacion_id'), motivo_rechazo.strip(), usuario_admin
                                                                    )
                                                                    
                                                                    if success:
                                                                        st.success("🚫 Anulación rechazada")
                                                                        del st.session_state[f"show_reject_form_{orden['_id']}_{idx}"]
                                                                        st.rerun()
                                                                    else:
                                                                        st.error(f"❌ Error al rechazar: {message}")
                                                                else:
                                                                    st.warning("⚠️ Debes especificar un motivo de rechazo")
                                                        
                                                        with col_cancelar:
                                                            if st.button("🔙 Cancelar", key=f"cancel_reject_{orden['_id']}_{idx}"):
                                                                del st.session_state[f"show_reject_form_{orden['_id']}_{idx}"]
                                                                st.rerun()
                                            
                                            continue  # Saltar el resto de la lógica para este item
                                        
                                        # Verificar si la anulación fue rechazada
                                        elif item.get('anulacion_rechazada', False):
                                            # Mostrar el producto normal pero con notificación de rechazo
                                            pass  # Continuar con la lógica normal para mostrar el producto
                                        
                                        if es_bebida:
                                            # Verificar estado de despacho de bebida
                                            if item.get('despachado_bar', False):
                                                # Bebida despachada - lista para retirar
                                                st.markdown(f"""
                                                <div class="beverage-ready">
                                                    🍹 {item_text} <strong>✅ LISTO PARA RETIRAR</strong>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                                # Mostrar información adicional de despacho
                                                fecha_despacho = item.get('fecha_despacho_bar', '')
                                                usuario_despacho = item.get('usuario_despacho_bar', 'N/A')
                                                
                                                if fecha_despacho:
                                                    try:
                                                        fecha_dt = datetime.fromisoformat(fecha_despacho.replace('Z', '+00:00'))
                                                        # Convertir de UTC a hora local del sistema
                                                        fecha_local = fecha_dt.astimezone()
                                                        hora_despacho = fecha_local.strftime('%H:%M:%S')
                                                        st.caption(f"   🕐 Despachado a las {hora_despacho} por {usuario_despacho}")
                                                    except:
                                                        st.caption(f"   👤 Despachado por: {usuario_despacho}")
                                            else:
                                                # Bebida en proceso
                                                st.markdown(f"""
                                                <div class="beverage-process">
                                                    🍹 {item_text} <strong>⏳ EN PROCESO</strong>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                st.caption(f"   📍 Enviado al bar para preparación")
                                        
                                        elif es_plato_cocina:
                                            # Verificar estado de despacho de plato
                                            if item.get('despachado_cocina', False):
                                                # Plato servido - listo para entregar
                                                st.markdown(f"""
                                                <div class="beverage-ready">
                                                    🍽️ {item_text} <strong>✅ LISTO PARA SERVIR</strong>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                
                                                # Mostrar información adicional de servido
                                                fecha_despacho = item.get('fecha_despacho_cocina', '')
                                                usuario_despacho = item.get('usuario_despacho_cocina', 'N/A')
                                                
                                                if fecha_despacho:
                                                    try:
                                                        fecha_dt = datetime.fromisoformat(fecha_despacho.replace('Z', '+00:00'))
                                                        # Convertir de UTC a hora local del sistema
                                                        fecha_local = fecha_dt.astimezone()
                                                        hora_despacho = fecha_local.strftime('%H:%M:%S')
                                                        st.caption(f"   🕐 Servido a las {hora_despacho} por {usuario_despacho}")
                                                    except:
                                                        st.caption(f"   👤 Servido por: {usuario_despacho}")
                                            else:
                                                # Plato en preparación
                                                st.markdown(f"""
                                                <div class="beverage-process">
                                                    🍽️ {item_text} <strong>⏳ EN PREPARACIÓN</strong>
                                                </div>
                                                """, unsafe_allow_html=True)
                                                st.caption(f"   📍 Enviado a cocina para preparación")
                                        
                                        else:
                                            # No es bebida ni plato de cocina, mostrar normal
                                            st.write(item_text)
                                        
                                        if item.get('comentarios'):
                                            st.caption(f"   💬 Notas: {item['comentarios']}")
                                        
                                        # Mostrar notificación de anulación rechazada
                                        if item.get('anulacion_rechazada', False):
                                            usuario_rechaza = item.get('usuario_rechaza_anulacion', 'Administrador')
                                            motivo_rechazo = item.get('motivo_rechazo_anulacion', 'Sin motivo especificado')
                                            solicitud_original = item.get('solicitud_original_anulacion', 'Sin detalle')
                                            
                                            st.markdown(f"""
                                            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 10px; margin: 8px 0; color: #721c24;">
                                                <strong>❌ SOLICITUD DE ANULACIÓN RECHAZADA</strong><br>
                                                <small><strong>👤 Rechazada por:</strong> {usuario_rechaza}</small><br>
                                                <small><strong>💭 Su solicitud:</strong> "{solicitud_original}"</small><br>
                                                <small><strong>📝 Motivo del rechazo:</strong> "{motivo_rechazo}"</small>
                                            </div>
                                            """, unsafe_allow_html=True)
                                            
                                            # Botón para marcar como visto
                                            if st.button("✅ Entendido", key=f"dismiss_rejection_{orden['_id']}_{idx}", help="Marcar notificación como vista"):
                                                usuario_actual = st.session_state.get('user_data', {}).get('usuario', 'Usuario')
                                                success, message = couchdb_utils.marcar_rechazo_como_visto(
                                                    db, orden['_id'], idx, usuario_actual
                                                )
                                                
                                                if success:
                                                    st.success("✅ Notificación marcada como vista")
                                                    st.rerun()
                                                else:
                                                    st.error(f"❌ Error: {message}")
                                        
                                        # Botón para solicitar anulación (para meseros, admins y operativos, y si no está ya en proceso, anulado, rechazado, o listo para retirar)
                                        user_role = st.session_state.get('user_data', {}).get('id_rol', 0)
                                        esta_listo_pickup = item.get('despachado_bar', False) or item.get('despachado_cocina', False)
                                        puede_anular = (
                                            user_role in [1, 3, 6] and  # Admin, Mesero y Operativo 
                                            not item.get('anulado', False) and 
                                            not item.get('en_proceso_anulacion', False) and 
                                            not item.get('anulacion_rechazada', False) and
                                            not esta_listo_pickup
                                        )
                                        if puede_anular:  # Admin, Mesero u Operativo
                                            with st.container():
                                                col_anular = st.columns([3, 1])
                                                with col_anular[1]:
                                                    if st.button("🗑️ Anular", key=f"request_cancel_{orden['_id']}_{idx}", help="Solicitar anulación"):
                                                        st.session_state[f"show_cancel_form_{orden['_id']}_{idx}"] = True
                                                        st.rerun()
                                        
                                        # Mostrar formulario de solicitud de anulación si está activo
                                        if st.session_state.get(f"show_cancel_form_{orden['_id']}_{idx}", False):
                                            with st.container():
                                                st.markdown("**Solicitar Anulación**")
                                                motivo = st.text_area(
                                                    "Motivo de la anulación:", 
                                                    key=f"cancel_reason_{orden['_id']}_{idx}",
                                                    placeholder="Ej: Cliente ya no desea el producto, cambio de pedido, etc."
                                                )
                                                
                                                col_form = st.columns([1, 1])
                                                with col_form[0]:
                                                    if st.button("✅ Enviar Solicitud", key=f"send_cancel_{orden['_id']}_{idx}"):
                                                        if motivo.strip():
                                                            # Crear solicitud de anulación
                                                            usuario_actual = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                                            success, result = couchdb_utils.crear_solicitud_anulacion(
                                                                db, orden['_id'], idx, motivo.strip(), usuario_actual
                                                            )
                                                            
                                                            if success:
                                                                st.success("✅ Solicitud de anulación enviada al administrador")
                                                                # Limpiar el formulario
                                                                del st.session_state[f"show_cancel_form_{orden['_id']}_{idx}"]
                                                                st.rerun()
                                                            else:
                                                                st.error(f"❌ Error al crear solicitud: {result}")
                                                        else:
                                                            st.error("❌ Debes proporcionar un motivo")
                                                
                                                with col_form[1]:
                                                    if st.button("❌ Cancelar", key=f"cancel_cancel_{orden['_id']}_{idx}"):
                                                        del st.session_state[f"show_cancel_form_{orden['_id']}_{idx}"]
                                                        st.rerun()
                                                
                                                st.markdown("---")
                                
                                st.subheader("Acciones")
                                col_active_buttons = st.columns(3)
                                with col_active_buttons[0]:
                                    if st.button("➕ Agregar Productos", key=f"add_active_{orden['_id']}", use_container_width=True):
                                        # Load this order into the editing state and redirect to restaurant_main
                                        st.session_state.orden_editar = orden
                                        st.session_state.plato_seleccionado = None
                                        st.switch_page("pages/restaurant_main.py")
                                with col_active_buttons[1]:
                                    if st.button("💵 Enviar a Cobro", key=f"pay_active_{orden['_id']}", use_container_width=True):
                                        try:
                                            # 1. Filter out cancelled products and recalculate total
                                            items_activos = [item for item in orden.get('items', []) if not item.get('anulado', False)]
                                            total_activo = sum(item.get('cantidad', 0) * item.get('precio_unitario', 0) for item in items_activos)
                                            
                                            # Verificar que haya productos activos para enviar a cobro
                                            if not items_activos:
                                                st.error("❌ No se puede enviar a cobro: todos los productos han sido anulados.")
                                            else:
                                                # 2. Prepare ticket document with only active items
                                                ticket_doc = {
                                                    "_id": f"tickets:{str(uuid.uuid4())}",
                                                    "type": "tickets",
                                                    "orden_id": orden['_id'],
                                                    "numero_orden": orden.get('numero_orden'),
                                                    "mesa_id": orden.get('mesa_id'),
                                                    "mesero_id": orden.get('mesero_id'),
                                                    "total": total_activo,
                                                    "items": items_activos,
                                                    "fecha_creacion": datetime.now(timezone.utc).isoformat(),
                                                    "estado": "pendiente_pago"
                                                }
                                                
                                                # 3. Save ticket to database
                                                db.save(ticket_doc)
                                                
                                                # 4. Update order status to "enviado_cobro"
                                                orden['estado'] = 'enviado_cobro'
                                                db.save(orden)
                                                
                                                # 5. Generate PDF and store in session state for display
                                                mesa = mesas.get(ticket_doc['mesa_id'], {})
                                                mesero = meseros.get(ticket_doc['mesero_id'], {})
                                                pdf_data = couchdb_utils.generar_orden_pdf(ticket_doc, orden, mesa, mesero)
                                                file_name = f"orden_{ticket_doc.get('numero_orden', 'SN')}.pdf"
                                                
                                                st.session_state['just_processed_ticket_display'] = {
                                                    'message': f"✅ Orden #{orden.get('numero_orden')} enviada a cobro exitosamente!",
                                                    'pdf_data': pdf_data,
                                                    'file_name': file_name
                                                }
                                                
                                                logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                                couchdb_utils.log_action(db, logged_in_user, f"Envió Orden #{orden.get('numero_orden')} a cobro")
                                                
                                                st.balloons()
                                                st.rerun() # Rerun to remove from active orders and display PDF
                                        
                                        except Exception as e:
                                            st.error(f"Ocurrió un error al enviar a cobro: {str(e)}")
                                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                            couchdb_utils.log_action(db, logged_in_user, f"Fallo al enviar Orden #{orden.get('numero_orden')} a cobro: {str(e)}")
                                
                                with col_active_buttons[2]:
                                    # Botón de anular orden completa (para meseros, admins y operativos)
                                    user_role = st.session_state.get('user_data', {}).get('id_rol', 0)
                                    puede_anular_orden = user_role in [1, 3, 6]  # Admin, Mesero y Operativo
                                    
                                    # Verificar si ya hay una solicitud pendiente o rechazada
                                    tiene_solicitud_pendiente = orden.get('solicitud_anulacion_completa_pendiente', False)
                                    tiene_rechazo_orden = orden.get('anulacion_completa_rechazada', False)
                                    
                                    if puede_anular_orden and not tiene_solicitud_pendiente:
                                        if st.button("🗑️ Anular Orden", key=f"cancel_order_{orden['_id']}", use_container_width=True, help="Solicitar anulación completa de la orden"):
                                            st.session_state[f"show_cancel_order_form_{orden['_id']}"] = True
                                            st.rerun()
                                    elif tiene_solicitud_pendiente:
                                        st.markdown("⏳ **Solicitud de anulación completa pendiente**")
                                        motivo_solicitud = orden.get('motivo_solicitud_anulacion_completa', 'Sin motivo especificado')
                                        usuario_solicita = orden.get('usuario_solicita_anulacion_completa', 'N/A')
                                        
                                        st.info(f"📝 Motivo: {motivo_solicitud}")
                                        st.caption(f"🔔 Solicitado por: {usuario_solicita}")
                                        
                                        # Botones de aprobación/rechazo para administradores y operativos
                                        if user_role in [1, 6]:  # Admin y Operativo
                                            col_aprobar_orden, col_rechazar_orden = st.columns(2)
                                            
                                            with col_aprobar_orden:
                                                if st.button("✅ Aprobar Anulación", key=f"approve_order_{orden['_id']}", type="primary", use_container_width=True):
                                                    # Aprobar anulación completa
                                                    usuario_admin = st.session_state.get('user_data', {}).get('usuario', 'Administrador')
                                                    success, message = couchdb_utils.aprobar_anulacion_orden_completa(
                                                        db, orden['_id'], usuario_admin
                                                    )
                                                    
                                                    if success:
                                                        st.success("✅ Anulación completa aprobada exitosamente")
                                                        st.rerun()
                                                    else:
                                                        st.error(f"❌ Error al aprobar: {message}")
                                            
                                            with col_rechazar_orden:
                                                if st.button("❌ Rechazar Anulación", key=f"reject_order_{orden['_id']}", type="secondary", use_container_width=True):
                                                    st.session_state[f"show_reject_order_form_{orden['_id']}"] = True
                                                    st.rerun()
                                            
                                            # Formulario de rechazo de orden completa
                                            if st.session_state.get(f"show_reject_order_form_{orden['_id']}", False):
                                                with st.container():
                                                    st.markdown("**Motivo del Rechazo de Anulación Completa:**")
                                                    motivo_rechazo_orden = st.text_area(
                                                        "¿Por qué se rechaza esta anulación completa?",
                                                        key=f"reject_order_reason_{orden['_id']}",
                                                        placeholder="Ej: La orden ya está muy avanzada, no se puede anular completamente..."
                                                    )
                                                    
                                                    col_confirmar_orden, col_cancelar_orden = st.columns(2)
                                                    with col_confirmar_orden:
                                                        if st.button("🚫 Confirmar Rechazo", key=f"confirm_reject_order_{orden['_id']}", type="primary"):
                                                            if motivo_rechazo_orden.strip():
                                                                usuario_admin = st.session_state.get('user_data', {}).get('usuario', 'Administrador')
                                                                success, message = couchdb_utils.rechazar_anulacion_orden_completa(
                                                                    db, orden['_id'], motivo_rechazo_orden.strip(), usuario_admin
                                                                )
                                                                
                                                                if success:
                                                                    st.success("🚫 Anulación completa rechazada")
                                                                    del st.session_state[f"show_reject_order_form_{orden['_id']}"]
                                                                    st.rerun()
                                                                else:
                                                                    st.error(f"❌ Error al rechazar: {message}")
                                                            else:
                                                                st.warning("⚠️ Debes especificar un motivo de rechazo")
                                                    
                                                    with col_cancelar_orden:
                                                        if st.button("🔙 Cancelar", key=f"cancel_reject_order_{orden['_id']}"):
                                                            del st.session_state[f"show_reject_order_form_{orden['_id']}"]
                                                            st.rerun()
                                    
                                    # Mostrar notificación de rechazo de anulación completa
                                    if tiene_rechazo_orden:
                                        usuario_rechaza = orden.get('usuario_rechaza_anulacion_completa', 'Administrador')
                                        motivo_rechazo = orden.get('motivo_rechazo_anulacion_completa', 'Sin motivo especificado')
                                        solicitud_original = orden.get('motivo_solicitud_anulacion_completa', 'Sin detalle')
                                        
                                        st.markdown(f"""
                                        <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 10px; margin: 8px 0; color: #721c24;">
                                            <strong>❌ SOLICITUD DE ANULACIÓN COMPLETA RECHAZADA</strong><br>
                                            <small><strong>👤 Rechazada por:</strong> {usuario_rechaza}</small><br>
                                            <small><strong>💭 Su solicitud:</strong> "{solicitud_original}"</small><br>
                                            <small><strong>📝 Motivo del rechazo:</strong> "{motivo_rechazo}"</small>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        # Botón para marcar como visto
                                        if st.button("✅ Entendido", key=f"dismiss_order_rejection_{orden['_id']}", help="Marcar notificación como vista"):
                                            usuario_actual = st.session_state.get('user_data', {}).get('usuario', 'Usuario')
                                            success, message = couchdb_utils.marcar_rechazo_anulacion_completa_como_visto(
                                                db, orden['_id'], usuario_actual
                                            )
                                            
                                            if success:
                                                st.success("✅ Notificación marcada como vista")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Error: {message}")
                                
                                # Mostrar formulario de solicitud de anulación completa si está activo
                                if st.session_state.get(f"show_cancel_order_form_{orden['_id']}", False):
                                    with st.container():
                                        st.markdown("**Solicitar Anulación Completa de la Orden**")
                                        st.warning("⚠️ Esta acción solicitará la anulación de TODA la orden y requiere aprobación administrativa.")
                                        
                                        motivo_orden = st.text_area(
                                            "Motivo de la anulación completa:", 
                                            key=f"cancel_order_reason_{orden['_id']}",
                                            placeholder="Ej: Cliente se retiró del restaurante, mesa cancelada, etc."
                                        )
                                        
                                        col_form_orden = st.columns([1, 1])
                                        with col_form_orden[0]:
                                            if st.button("✅ Enviar Solicitud de Anulación", key=f"send_cancel_order_{orden['_id']}"):
                                                if motivo_orden.strip():
                                                    # Crear solicitud de anulación completa
                                                    usuario_actual = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                                    success, result = couchdb_utils.crear_solicitud_anulacion_orden_completa(
                                                        db, orden['_id'], motivo_orden.strip(), usuario_actual
                                                    )
                                                    
                                                    if success:
                                                        st.success("✅ Solicitud de anulación completa enviada al administrador")
                                                        # Limpiar el formulario
                                                        del st.session_state[f"show_cancel_order_form_{orden['_id']}"]
                                                        st.rerun()
                                                    else:
                                                        st.error(f"❌ Error al crear solicitud: {result}")
                                                else:
                                                    st.error("❌ Debes proporcionar un motivo para la anulación")
                                        
                                        with col_form_orden[1]:
                                            if st.button("❌ Cancelar", key=f"cancel_cancel_order_{orden['_id']}"):
                                                del st.session_state[f"show_cancel_order_form_{orden['_id']}"]
                                                st.rerun()
                                        
                                        st.markdown("---")

        # --- Modo edición de orden ---
        if st.session_state.get('orden_editar'):
            orden_a_editar = st.session_state.orden_editar
            
            # Validación de seguridad: verificar que la orden existe y no es None
            if not orden_a_editar or not isinstance(orden_a_editar, dict):
                st.error("⚠️ La orden a editar no es válida. Regresando a la vista principal.")
                st.session_state.orden_editar = None
                st.rerun()
            
            # Verificar que la orden aún existe en la base de datos
            try:
                orden_verificada = db.get(orden_a_editar['_id'])
                if not orden_verificada or orden_verificada.get('estado') != 'pendiente':
                    st.error("⚠️ La orden ya no está disponible para edición.")
                    st.session_state.orden_editar = None
                    st.rerun()
            except Exception:
                st.error("⚠️ Error al verificar la orden. Regresando a la vista principal.")
                st.session_state.orden_editar = None
                st.rerun()
            
            # Cargar datos frescos para la edición
            platos = {p['_id']: p for p in couchdb_utils.get_documents_by_partition(db, "platos")}
            platos_disponibles = [p for p in platos.values() if p.get('activo', 0) == 1]
            
            st.markdown("---")
            st.title(f"Editando Orden #{orden_a_editar.get('numero_orden', 'N/A')}")
            
            # Mostrar productos actuales
            st.subheader("Productos actuales")
            total_actual = 0
            items_actuales = orden_a_editar.get('items', []) if orden_a_editar else []
            
            if not items_actuales:
                st.info("No hay productos en esta orden.")
            else:
                for item in items_actuales:
                    if item and isinstance(item, dict):
                        cantidad = item.get('cantidad', 0)
                        precio = item.get('precio_unitario', 0)
                        nombre = item.get('nombre', 'Producto sin nombre')
                        st.markdown(f"- {cantidad}x {nombre} (${precio:.2f})")
                        total_actual += cantidad * precio
                st.markdown(f"**Total actual: ${total_actual:.2f}**")

            st.markdown("---")
            
            # Agregar nuevos productos
            st.subheader("Agregar nuevos productos")
            
            plato_opciones = {p['_id']: f"{p.get('descripcion', 'N/A')} - ${p.get('precio_normal', 0):.2f}" for p in platos_disponibles}
            
            plato_id_seleccionado = st.selectbox(
                "Seleccionar Plato:",
                options=list(plato_opciones.keys()),
                format_func=lambda x: plato_opciones[x]
            )
            
            if plato_id_seleccionado:
                plato_obj = platos[plato_id_seleccionado]
                
                col_cant, col_precio, col_com = st.columns([1, 1, 2])
                with col_cant:
                    cantidad = st.number_input("Cantidad:", min_value=1, value=1, step=1)
                with col_precio:
                    precio = st.number_input("Precio:", value=plato_obj.get('precio_normal', 0.0), min_value=0.0, step=0.01)
                with col_com:
                    comentarios = st.text_input("Comentarios/Notas:")

                if st.button("Agregar a la Orden"):
                    nuevo_item = {
                        'plato_id': plato_obj['_id'],
                        'nombre': plato_obj.get('descripcion', 'Plato'),
                        'precio_unitario': precio,
                        'cantidad': cantidad,
                        'comentarios': comentarios,
                        'tipo_precio': 'Normal'
                    }
                    
                    orden_a_editar['items'].append(nuevo_item)
                    orden_a_editar['total'] = sum(item['precio_unitario'] * item['cantidad'] for item in orden_a_editar['items'])
                    
                    try:
                        db.save(orden_a_editar)
                        st.success("Producto agregado a la orden!")
                        # No necesitamos borrar la sesión aquí, solo refrescar para ver el item añadido
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar orden: {str(e)}")
            
            st.markdown("---")
            # Botón para terminar edición
            if st.button("✔️ Terminar Edición y Volver"):
                del st.session_state.orden_editar
                st.rerun()
    else:
        st.error("No se pudo conectar a la base de datos")