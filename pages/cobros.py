import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import base64 # Import base64 for embedding PDF


# --- Configuración Inicial ---
st.set_page_config(layout="wide", page_title="Cobro de Tickets", page_icon="../assets/LOGO.png")
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)

# --- Clase para Generar PDF del Ticket (as provided in previous fix) ---
class PDF(FPDF):
    def header(self):
        # Logo
        try:
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'LOGO.png')
            if os.path.exists(logo_path):
                # Centrar el logo en la página de 80mm de ancho
                self.image(logo_path, 20, 8, 40)  # x=20 para centrar en 80mm, width=40
                self.set_y(self.get_y() + 25)  # Espacio después del logo
        except:
            pass
        
        self.set_font('Helvetica', 'B', 12) # Changed to Helvetica
        self.cell(0, 8, 'Tia Juana', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('Helvetica', '', 8) # Changed to Helvetica
        self.cell(0, 4, 'Elias, Salvador Alfonso', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'NIT: 0210-030563-104-1', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'IVA DL296', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'REG. 102166713', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'Giro: Restaurantes', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'Fecha Autorización: 11/12/2019', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_y(self.get_y() + 5)

    def footer(self):
        self.set_y(-30)
        self.set_font('Helvetica', 'B', 10) # Changed to Helvetica
        self.cell(0, 10, '!!!!! CANCELADO/PAGADO !!!!!', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('Helvetica', 'I', 8) # Changed to Helvetica
        self.cell(0, 5, 'GRACIAS POR TU COMPRA', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 5, 'REGRESA PRONTO', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

# --- Función para limpiar texto del PDF ---
def limpiar_texto_pdf(texto):
    """Limpia emojis y caracteres no compatibles con PDF"""
    if not texto:
        return "N/A"
    
    import re
    # Remover emojis y caracteres especiales
    texto_limpio = re.sub(r'[^\x00-\x7F]+', '', str(texto))  # Solo ASCII
    # Limpiar espacios extra y caracteres especiales comunes
    texto_limpio = re.sub(r'[🎉🍹🍽️💰🔥⭐💥⏰]', '', texto_limpio)
    # Limpiar caracteres de formato especial
    texto_limpio = texto_limpio.strip()
    
    return texto_limpio if texto_limpio else "Producto"

# --- Función para generar el PDF (as provided in previous fix) ---
def generar_ticket_pdf(ticket, orden, mesa, mesero):
    pdf = PDF('P', 'mm', (80, 200)) # Ancho de ticket de 80mm
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Helvetica', '', 9) # Changed to Helvetica

    # Info del Ticket
    pdf.cell(0, 5, f"Ticket #{ticket.get('numero_orden', 'N/A')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    fecha_pago = datetime.now(timezone.utc).astimezone().strftime('%d/%m/%Y %I:%M:%S %p')
    pdf.cell(0, 5, f"Fecha: {fecha_pago}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    mesa_nombre_limpio = limpiar_texto_pdf(mesa.get('descripcion', 'N/A'))
    pdf.cell(0, 5, f"Mesa: {mesa_nombre_limpio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    mesero_nombre_limpio = limpiar_texto_pdf(mesero.get('nombre', 'N/A'))
    pdf.cell(0, 5, f"Mesero: {mesero_nombre_limpio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    pdf.set_y(pdf.get_y() + 5)

    # Encabezados de productos
    pdf.set_font('Helvetica', 'B', 8) # Changed to Helvetica
    pdf.cell(10, 5, 'CANT.', new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
    pdf.cell(30, 5, 'PRODUCTO', new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
    pdf.cell(15, 5, 'PRECIO', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(15, 5, 'TOTAL', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 70, pdf.get_y())
    pdf.set_y(pdf.get_y() + 2)

    # Items
    pdf.set_font('Helvetica', '', 8) # Changed to Helvetica
    # Filtrar productos anulados
    items_activos = [item for item in orden.get('items', []) if not item.get('anulado', False)]
    subtotal = sum(item.get('cantidad', 0) * item.get('precio_unitario', 0) for item in items_activos)
    
    for item in items_activos:
        cantidad = item.get('cantidad', 0)
        precio = item.get('precio_unitario', 0)
        total_item = cantidad * precio
        
        y_before = pdf.get_y()
        pdf.cell(10, 5, str(cantidad), new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
        nombre_limpio = limpiar_texto_pdf(item.get('nombre', 'N/A'))
        pdf.multi_cell(30, 5, nombre_limpio, align='L')
        y_after = pdf.get_y()
        height_diff = y_after - y_before
        
        pdf.set_y(y_before)
        pdf.set_x(pdf.get_x() + 40)
        
        pdf.cell(15, height_diff, f"${precio:.2f}", new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
        pdf.cell(15, height_diff, f"${total_item:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    
    servicio = subtotal * 0.10
    total_final = subtotal + servicio
    
    # Totales
    pdf.set_y(pdf.get_y() + 3)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 70, pdf.get_y())
    pdf.set_y(pdf.get_y() + 2)
    pdf.set_font('Helvetica', 'B', 9) # Changed to Helvetica
    pdf.cell(40, 5, 'Subtotal:', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 5, f"${subtotal:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.cell(40, 5, 'Servicio (10%):', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 5, f"${servicio:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.set_font('Helvetica', 'B', 11) # Changed to Helvetica
    pdf.cell(40, 8, 'TOTAL:', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 8, f"${total_final:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

    return bytes(pdf.output())


# --- Lógica Principal de la Pantalla ---

# Initialize session state for processed ticket if not already present
if 'just_processed_ticket_display' not in st.session_state:
    st.session_state['just_processed_ticket_display'] = None

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        st.title("💰 Sistema de Cobros")
        
        # --- Display the PDF and button immediately if a ticket was just processed ---
        if st.session_state['just_processed_ticket_display'] is not None:
            info = st.session_state.pop('just_processed_ticket_display') # Pop to clear it after display
            st.success(info['message'])
            
            # Display the download button
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
            
            # No st.rerun() here. The next interaction will naturally rerun.
            # This ensures the user sees the button and PDF before the page potentially refreshes to show other tickets.
            st.markdown("---")

        # --- Cargar datos comunes para ambas pestañas ---
        mesas = {m['_id']: m for m in couchdb_utils.get_documents_by_partition(db, "mesas")}
        # Corregir partición de usuarios de "usuario" a "Usuario"
        todos_usuarios = couchdb_utils.get_documents_by_partition(db, "Usuario")
        meseros = {m['_id']: m for m in todos_usuarios if m.get('id_rol') == 3}
        ordenes = {o['_id']: o for o in couchdb_utils.get_documents_by_partition(db, "ordenes")}
        
        # --- Pestañas para Cobros Pendientes e Historial ---
        tab_pendientes, tab_historial = st.tabs(["🕒 Cobros Pendientes", "📋 Historial de Cobros"])
        
        with tab_pendientes:
            st.subheader("Tickets Pendientes de Cobro")
            
            # --- Rest of the payment processing logic ---
            tickets_pendientes = [doc for doc in couchdb_utils.get_documents_by_partition(db, "tickets") if doc.get('estado') == 'pendiente_pago']
        
            if not tickets_pendientes:
                st.info("✅ No hay cuentas pendientes de cobro.")
            else:
                # Ordenar tickets por fecha de creación (más viejo primero)
                tickets_pendientes.sort(key=lambda x: x.get('fecha_creacion', ''))

                for idx, ticket in enumerate(tickets_pendientes):
                    orden_id = ticket.get('orden_id')
                    orden = ordenes.get(orden_id, {})
                    
                    if not orden:
                        st.warning(f"No se encontró la orden ({orden_id}) para el ticket {ticket['_id']}. Omitiendo.")
                        continue
                
                mesa = mesas.get(ticket.get('mesa_id'), {})
                mesero = meseros.get(ticket.get('mesero_id'), {})
                total_a_pagar = ticket.get('total', 0)
                numero_orden = idx + 1  # Número correlativo (más viejo = 1)

                header = f"Mesa: **{mesa.get('descripcion', 'N/A')}** | Mesero: **{mesero.get('nombre', 'N/A')}** | Total: **${total_a_pagar:.2f}**"
                
                with st.expander(header, expanded=True):
                    col_numero, col_info, col_pago = st.columns([1, 2, 2])

                    with col_numero:
                        # Número grande que abarca toda la altura del recuadro
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; justify-content: center; height: 200px; background-color: #f0f2f6; border-radius: 10px; border: 2px solid #1f77b4;">
                            <span style="font-size: 80px; font-weight: bold; color: #1f77b4;">{numero_orden}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.caption(f"Orden #{ticket.get('numero_orden', 'N/A')}")

                    with col_info:
                        st.subheader("Productos Ordenados")
                        # Filtrar productos anulados
                        items_activos = [item for item in orden.get('items', []) if not item.get('anulado', False)]
                        for item in items_activos:
                            st.markdown(f"- **{item.get('cantidad')}x** {item.get('nombre')} (${item.get('precio_unitario'):.2f} c/u)")
                    
                    with col_pago:
                        st.subheader("Procesar Pago")
                        
                        # Selector de método de pago
                        metodo_pago = st.selectbox(
                            "Método de Pago:",
                            options=["Efectivo", "Tarjeta", "Pago Mixto", "Transferencia Bancaria", "Criptomoneda"],
                            key=f"metodo_{ticket['_id']}"
                        )
                        
                        pago_valido = False
                        pago_info = {}
                        
                        if metodo_pago == "Efectivo":
                            efectivo_recibido = st.number_input(
                                "Efectivo recibido ($)", 
                                min_value=0.0, 
                                value=total_a_pagar,
                                step=1.0,
                                key=f"cash_{ticket['_id']}"
                            )
                            
                            if efectivo_recibido >= total_a_pagar:
                                cambio = efectivo_recibido - total_a_pagar
                                st.metric("Cambio a entregar:", f"${cambio:.2f}")
                                pago_valido = True
                                pago_info = {
                                    'metodo': 'efectivo',
                                    'recibido': efectivo_recibido,
                                    'cambio': cambio
                                }
                            else:
                                st.warning("El efectivo recibido es menor que el total a pagar.")
                                
                        elif metodo_pago == "Tarjeta":
                            tipo_tarjeta = st.selectbox(
                                "Tipo de Tarjeta:",
                                options=["Débito", "Crédito"],
                                key=f"tipo_tarjeta_{ticket['_id']}"
                            )
                            ultimos_digitos = st.text_input(
                                "Últimos 4 dígitos de la tarjeta:",
                                max_chars=4,
                                key=f"digitos_{ticket['_id']}"
                            )
                            
                            if len(ultimos_digitos) == 4:
                                st.success(f"Pago con {tipo_tarjeta} por ${total_a_pagar:.2f}")
                                pago_valido = True
                                pago_info = {
                                    'metodo': 'tarjeta',
                                    'tipo_tarjeta': tipo_tarjeta.lower(),
                                    'ultimos_digitos': ultimos_digitos,
                                    'monto': total_a_pagar
                                }
                            else:
                                st.warning("Ingrese los últimos 4 dígitos de la tarjeta.")
                                
                        elif metodo_pago == "Pago Mixto":
                            monto_efectivo = st.number_input(
                                "Monto en Efectivo ($):",
                                min_value=0.0,
                                max_value=total_a_pagar,
                                value=0.0,
                                step=1.0,
                                key=f"mixto_efectivo_{ticket['_id']}"
                            )
                            
                            monto_tarjeta = total_a_pagar - monto_efectivo
                            st.metric("Monto en Tarjeta:", f"${monto_tarjeta:.2f}")
                            
                            if monto_tarjeta > 0:
                                tipo_tarjeta_mixto = st.selectbox(
                                    "Tipo de Tarjeta:",
                                    options=["Débito", "Crédito"],
                                    key=f"tipo_tarjeta_mixto_{ticket['_id']}"
                                )
                                digitos_mixto = st.text_input(
                                    "Últimos 4 dígitos (Tarjeta):",
                                    max_chars=4,
                                    key=f"digitos_mixto_{ticket['_id']}"
                                )
                                
                                if len(digitos_mixto) == 4:
                                    cambio_efectivo = 0
                                    if monto_efectivo > 0:
                                        efectivo_recibido_mixto = st.number_input(
                                            "Efectivo recibido ($):",
                                            min_value=monto_efectivo,
                                            value=monto_efectivo,
                                            step=1.0,
                                            key=f"efectivo_recibido_mixto_{ticket['_id']}"
                                        )
                                        cambio_efectivo = efectivo_recibido_mixto - monto_efectivo
                                        if cambio_efectivo > 0:
                                            st.metric("Cambio a entregar:", f"${cambio_efectivo:.2f}")
                                    
                                    st.success(f"Pago mixto: ${monto_efectivo:.2f} efectivo + ${monto_tarjeta:.2f} tarjeta")
                                    pago_valido = True
                                    pago_info = {
                                        'metodo': 'mixto',
                                        'monto_efectivo': monto_efectivo,
                                        'monto_tarjeta': monto_tarjeta,
                                        'cambio_efectivo': cambio_efectivo,
                                        'tipo_tarjeta': tipo_tarjeta_mixto.lower(),
                                        'ultimos_digitos': digitos_mixto
                                    }
                                else:
                                    st.warning("Ingrese los últimos 4 dígitos de la tarjeta.")
                            else:
                                if monto_efectivo >= total_a_pagar:
                                    efectivo_recibido_solo = st.number_input(
                                        "Efectivo recibido ($):",
                                        min_value=total_a_pagar,
                                        value=total_a_pagar,
                                        step=1.0,
                                        key=f"efectivo_solo_mixto_{ticket['_id']}"
                                    )
                                    cambio = efectivo_recibido_solo - total_a_pagar
                                    st.metric("Cambio a entregar:", f"${cambio:.2f}")
                                    pago_valido = True
                                    pago_info = {
                                        'metodo': 'efectivo',
                                        'recibido': efectivo_recibido_solo,
                                        'cambio': cambio
                                    }
                                    
                        elif metodo_pago == "Transferencia Bancaria":
                            numero_transferencia = st.text_input(
                                "Número de Transferencia:",
                                key=f"transfer_{ticket['_id']}"
                            )
                            banco_origen = st.selectbox(
                                "Banco de Origen:",
                                options=["BAC", "Banco Agrícola", "Davivienda", "Banco Cuscatlán", "Banco Promerica", "Otro"],
                                key=f"banco_{ticket['_id']}"
                            )
                            
                            if numero_transferencia:
                                st.success(f"Transferencia por ${total_a_pagar:.2f}")
                                pago_valido = True
                                pago_info = {
                                    'metodo': 'transferencia',
                                    'numero_transferencia': numero_transferencia,
                                    'banco_origen': banco_origen,
                                    'monto': total_a_pagar
                                }
                            else:
                                st.warning("Ingrese el número de transferencia.")
                                
                        elif metodo_pago == "Criptomoneda":
                            tipo_cripto = st.selectbox(
                                "Tipo de Criptomoneda:",
                                options=["Bitcoin (BTC)", "Ethereum (ETH)", "USDT", "USDC", "Otra"],
                                key=f"cripto_{ticket['_id']}"
                            )
                            hash_transaccion = st.text_input(
                                "Hash de la Transacción:",
                                key=f"hash_{ticket['_id']}"
                            )
                            wallet_origen = st.text_input(
                                "Wallet de Origen (últimos 6 caracteres):",
                                max_chars=6,
                                key=f"wallet_{ticket['_id']}"
                            )
                            
                            if hash_transaccion and wallet_origen:
                                st.success(f"Pago en {tipo_cripto} por ${total_a_pagar:.2f}")
                                pago_valido = True
                                pago_info = {
                                    'metodo': 'criptomoneda',
                                    'tipo_cripto': tipo_cripto,
                                    'hash_transaccion': hash_transaccion,
                                    'wallet_origen': wallet_origen,
                                    'monto': total_a_pagar
                                }
                            else:
                                st.warning("Complete todos los campos requeridos.")

                        if pago_valido and st.button("✅ Confirmar Pago y Generar Ticket", key=f"pay_{ticket['_id']}"):
                            try:
                                ticket_doc = db[ticket['_id']]
                                ticket_doc['estado'] = 'pagado'
                                ticket_doc['fecha_pago'] = datetime.now(timezone.utc).isoformat()
                                ticket_doc['pago_info'] = pago_info
                                db.save(ticket_doc)
                                
                                orden_doc = db[orden_id]
                                orden_doc['estado'] = 'pagada'
                                db.save(orden_doc)

                                # Registrar movimientos de inventario por cada item vendido (solo productos activos)
                                logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                items_activos_inventario = [item for item in orden_doc.get('items', []) if not item.get('anulado', False)]
                                for item in items_activos_inventario:
                                    # Buscar el plato_id en la base de datos por nombre del item
                                    platos = couchdb_utils.get_documents_by_partition(db, "platos")
                                    plato = next((p for p in platos if p.get('descripcion') == item.get('nombre')), None)
                                    if plato:
                                        couchdb_utils.registrar_movimiento_inventario(
                                            db, 
                                            plato['_id'], 
                                            item.get('cantidad', 1), 
                                            logged_in_user
                                        )

                                pdf_data_for_display = generar_ticket_pdf(ticket_doc, orden_doc, mesa, mesero)
                                
                                # Store info for display on the next run
                                st.session_state['just_processed_ticket_display'] = {
                                    'pdf_data': pdf_data_for_display,
                                    'file_name': f"Ticket_{ticket.get('numero_orden', 'N_A')}.pdf",
                                    'message': f"¡Pago registrado para la Mesa {mesa.get('descripcion')}!"
                                }
                                
                                # Trigger a rerun *after* storing the data
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error al procesar el pago: {e}")
        
        with tab_historial:
            st.subheader("Historial de Cobros Realizados")
            
            # Obtener tickets pagados
            tickets_pagados = [doc for doc in couchdb_utils.get_documents_by_partition(db, "tickets") if doc.get('estado') == 'pagado']
            
            if not tickets_pagados:
                st.info("📝 No hay cobros realizados en el historial.")
            else:
                # Ordenar por fecha de pago (más reciente primero)
                tickets_pagados.sort(key=lambda x: x.get('fecha_pago', ''), reverse=True)
                
                # Filtros
                col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                with col_filtro1:
                    filtro_mesa = st.selectbox(
                        "Filtrar por Mesa:",
                        options=["Todas"] + [f"Mesa {mesa.get('descripcion', 'N/A')}" for mesa in mesas.values()],
                        key="filtro_mesa_historial"
                    )
                
                with col_filtro2:
                    fecha_desde = st.date_input("Desde:", key="fecha_desde_historial")
                
                with col_filtro3:
                    fecha_hasta = st.date_input("Hasta:", key="fecha_hasta_historial")
                
                # Aplicar filtros
                tickets_filtrados = tickets_pagados
                if filtro_mesa != "Todas":
                    mesa_id_filtro = None
                    for mesa_id, mesa_data in mesas.items():
                        if f"Mesa {mesa_data.get('descripcion', 'N/A')}" == filtro_mesa:
                            mesa_id_filtro = mesa_id
                            break
                    if mesa_id_filtro:
                        tickets_filtrados = [t for t in tickets_filtrados if t.get('mesa_id') == mesa_id_filtro]
                
                # Mostrar estadísticas del historial
                total_cobrado = sum(ticket.get('total', 0) for ticket in tickets_filtrados)
                st.info(f"📊 Mostrando {len(tickets_filtrados)} cobro(s) - Total: ${total_cobrado:.2f}")
                
                # Mostrar tickets en el historial
                for ticket in tickets_filtrados:
                    orden_id = ticket.get('orden_id')
                    orden = ordenes.get(orden_id, {})
                    mesa = mesas.get(ticket.get('mesa_id'), {})
                    mesero = meseros.get(ticket.get('mesero_id'), {})
                    
                    # Convertir fecha de pago
                    fecha_pago = ticket.get('fecha_pago', '')
                    fecha_pago_str = 'N/A'
                    if fecha_pago:
                        try:
                            from datetime import datetime
                            fecha_dt = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00'))
                            fecha_local = fecha_dt.astimezone()
                            fecha_pago_str = fecha_local.strftime('%d/%m/%Y %H:%M:%S')
                        except:
                            fecha_pago_str = 'Fecha inválida'
                    
                    # Información del pago
                    pago_info = ticket.get('pago_info', {})
                    metodo_pago = pago_info.get('metodo', 'N/A').title()
                    
                    with st.expander(f"🧾 Ticket #{ticket.get('numero_orden', 'N/A')} - Mesa {mesa.get('descripcion', 'N/A')} - ${ticket.get('total', 0):.2f} ({fecha_pago_str})", expanded=False):
                        col_info, col_productos, col_reprint = st.columns([1, 2, 1])
                        
                        with col_info:
                            st.markdown("**Información del Cobro:**")
                            st.write(f"🏠 **Mesa:** {mesa.get('descripcion', 'N/A')}")
                            st.write(f"👤 **Mesero:** {mesero.get('nombre', 'N/A')}")
                            st.write(f"💳 **Método:** {metodo_pago}")
                            st.write(f"💰 **Total:** ${ticket.get('total', 0):.2f}")
                            st.write(f"📅 **Fecha:** {fecha_pago_str}")
                            
                            # Mostrar información adicional según el método de pago
                            if metodo_pago == 'Efectivo':
                                recibido = pago_info.get('recibido', 0)
                                cambio = pago_info.get('cambio', 0)
                                st.write(f"💵 **Recibido:** ${recibido:.2f}")
                                st.write(f"🔄 **Cambio:** ${cambio:.2f}")
                        
                        with col_productos:
                            st.markdown("**Productos Cobrados:**")
                            # Filtrar productos anulados en el historial también
                            items_activos_historial = [item for item in orden.get('items', []) if not item.get('anulado', False)]
                            for item in items_activos_historial:
                                st.markdown(f"• **{item.get('cantidad')}x** {item.get('nombre')} - ${item.get('precio_unitario', 0):.2f}")
                        
                        with col_reprint:
                            st.markdown("**Reimprimir:**")
                            if st.button(f"🖨️ Reimprimir Ticket", key=f"reprint_{ticket['_id']}", use_container_width=True):
                                # Generar PDF nuevamente
                                try:
                                    pdf_data_reprint = generar_ticket_pdf(ticket, orden, mesa, mesero)
                                    st.download_button(
                                        label="📄 Descargar Ticket (Reimpresión)",
                                        data=pdf_data_reprint,
                                        file_name=f"Reimpresion_Ticket_{ticket.get('numero_orden', 'N_A')}.pdf",
                                        mime="application/pdf",
                                        key=f"download_reprint_{ticket['_id']}"
                                    )
                                    st.success("✅ Ticket listo para reimprimir")
                                except Exception as e:
                                    st.error(f"❌ Error al generar reimpresión: {str(e)}")
    
    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesión para acceder a esta página.")
