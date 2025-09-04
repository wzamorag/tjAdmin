# pages/cierre.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone
import uuid
import base64
from fpdf import FPDF

# Configuracion basica
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)
st.set_page_config(layout="wide", page_title="Cierre Z", page_icon="../assets/LOGO.png")

# Estilos CSS
st.markdown("""
<style>
    .cierre-card {
        border: 2px solid #2c3e50;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #f8f9fa;
    }
    .total-ventas {
        font-size: 2em;
        font-weight: bold;
        color: #27ae60;
        text-align: center;
    }
    .ticket-list {
        background-color: #ecf0f1;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def get_ventas_del_dia(db, fecha_objetivo=None):
    """
    Obtiene todas las ventas (tickets pagados) del dia especificado.
    Si no se especifica fecha, usa la fecha actual.
    """
    if fecha_objetivo is None:
        fecha_objetivo = datetime.now(timezone.utc).date()
    
    # Obtener todos los tickets pagados
    tickets = couchdb_utils.get_documents_by_partition(db, "tickets")
    tickets_pagados = [t for t in tickets if t.get('estado') == 'pagado']
    
    # Filtrar por fecha
    ventas_del_dia = []
    for ticket in tickets_pagados:
        fecha_pago = ticket.get('fecha_pago')
        if fecha_pago:
            try:
                # Convertir fecha de pago a fecha simple
                fecha_pago_date = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00')).date()
                if fecha_pago_date == fecha_objetivo:
                    ventas_del_dia.append(ticket)
            except:
                continue
    
    return ventas_del_dia

def get_next_ticket_z_number(db):
    """
    Obtiene el siguiente numero correlativo para el ticket Z
    """
    # Buscar el ultimo numero de orden usado
    ordenes = couchdb_utils.get_documents_by_partition(db, "ordenes")
    tickets = couchdb_utils.get_documents_by_partition(db, "tickets")
    cierres_z = couchdb_utils.get_documents_by_partition(db, "cierres_z")
    
    max_numero = 0
    
    # Revisar ordenes
    for orden in ordenes:
        numero = orden.get('numero_orden', 0)
        if isinstance(numero, int) and numero > max_numero:
            max_numero = numero
    
    # Revisar tickets
    for ticket in tickets:
        numero = ticket.get('numero_orden', 0)
        if isinstance(numero, int) and numero > max_numero:
            max_numero = numero
    
    # Revisar cierres Z anteriores
    for cierre in cierres_z:
        numero = cierre.get('numero_cierre_z', 0)
        if isinstance(numero, int) and numero > max_numero:
            max_numero = numero
    
    return max_numero + 1

def generar_ticket_z_pdf(ventas_del_dia, numero_cierre_z, fecha):
    """
    Genera el PDF del ticket de Cierre Z
    """
    pdf = FPDF('P', 'mm', (80, 200))  # Ancho de ticket de 80mm
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Logo
    try:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'LOGO.png')
        if os.path.exists(logo_path):
            # Centrar el logo en la página de 80mm de ancho
            pdf.image(logo_path, 20, 8, 40)  # x=20 para centrar en 80mm, width=40
            pdf.set_y(pdf.get_y() + 25)  # Espacio después del logo
    except:
        pass
    
    # Titulo
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'CIERRE Z', 0, 1, 'C')
    pdf.set_font('Arial', '', 8)
    pdf.cell(0, 4, f'Ticket Z #{numero_cierre_z:04d}', 0, 1, 'C')
    pdf.cell(0, 4, f'Fecha: {fecha.strftime("%d/%m/%Y")}', 0, 1, 'C')
    pdf.cell(0, 4, f'Hora: {datetime.now().strftime("%H:%M:%S")}', 0, 1, 'C')
    pdf.ln(3)
    
    # Linea separadora
    pdf.cell(0, 1, '_' * 35, 0, 1, 'C')
    pdf.ln(2)
    
    # Resumen de ventas
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, 'RESUMEN DE VENTAS DEL DIA', 0, 1, 'C')
    pdf.ln(2)
    
    # Detalles de tickets
    pdf.set_font('Arial', '', 7)
    total_ventas = 0
    ticket_count = 0
    
    if ventas_del_dia:
        pdf.cell(20, 4, 'Ticket', 1, 0, 'C')
        pdf.cell(25, 4, 'Hora', 1, 0, 'C')
        pdf.cell(20, 4, 'Total', 1, 1, 'C')
        
        for venta in ventas_del_dia:
            ticket_count += 1
            numero_ticket = venta.get('numero_orden', 'N/A')
            total = venta.get('total', 0)
            total_ventas += total
            
            # Obtener hora de pago
            fecha_pago = venta.get('fecha_pago', '')
            try:
                hora_pago = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00')).strftime('%H:%M')
            except:
                hora_pago = 'N/A'
            
            pdf.cell(20, 4, f'#{numero_ticket}', 1, 0, 'C')
            pdf.cell(25, 4, hora_pago, 1, 0, 'C')
            pdf.cell(20, 4, f'${total:.2f}', 1, 1, 'R')
    else:
        pdf.cell(0, 5, 'No hay ventas en este dia', 0, 1, 'C')
    
    pdf.ln(3)
    
    # Totales
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 1, '_' * 35, 0, 1, 'C')
    pdf.ln(2)
    pdf.cell(0, 5, f'TOTAL TICKETS: {ticket_count}', 0, 1, 'L')
    pdf.cell(0, 5, f'TOTAL VENTAS: ${total_ventas:.2f}', 0, 1, 'L')
    pdf.ln(3)
    
    # Informacion adicional
    pdf.set_font('Arial', '', 7)
    pdf.cell(0, 4, 'Periodo: 00:00 - 23:59', 0, 1, 'C')
    pdf.cell(0, 4, f'Usuario: {st.session_state.get("user_data", {}).get("usuario", "N/A")}', 0, 1, 'C')
    pdf.ln(5)
    
    # Pie
    pdf.cell(0, 1, '_' * 35, 0, 1, 'C')
    pdf.ln(2)
    pdf.cell(0, 4, 'CIERRE DIARIO COMPLETO', 0, 1, 'C')
    pdf.cell(0, 4, 'Gracias por su preferencia', 0, 1, 'C')
    
    return bytes(pdf.output(dest='S'))

def get_cierres_z_history(db):
    """
    Obtiene el historial de cierres Z generados
    """
    cierres_z = couchdb_utils.get_documents_by_partition(db, "cierres_z")
    
    # Ordenar por fecha de generacion (mas reciente primero)
    cierres_ordenados = sorted(cierres_z, 
                             key=lambda x: x.get('fecha_generacion', ''), 
                             reverse=True)
    
    return cierres_ordenados

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        st.title("🔒 Cierre Z - Resumen Diario de Ventas")
        st.markdown("---")
        
        # Seccion principal dividida en dos columnas
        col_main, col_history = st.columns([2, 1])
        
        with col_main:
            # Informacion del dia actual
            fecha_hoy = datetime.now(timezone.utc).date()
            st.info(f"📅 **Fecha del cierre:** {fecha_hoy.strftime('%d/%m/%Y')}")
            
            # Obtener ventas del dia
            ventas_del_dia = get_ventas_del_dia(db, fecha_hoy)
            
            # Mostrar resumen
            col1, col2, col3 = st.columns(3)
            
            total_ventas = sum(venta.get('total', 0) for venta in ventas_del_dia)
        
            with col1:
                st.metric("🎫 Total Tickets", len(ventas_del_dia))
            with col2:
                st.metric("💰 Total Ventas", f"${total_ventas:.2f}")
            with col3:
                st.metric("📊 Promedio por Ticket", f"${total_ventas/len(ventas_del_dia):.2f}" if ventas_del_dia else "$0.00")
            
            st.markdown("---")
            
            # Mostrar detalles de tickets
            if ventas_del_dia:
                st.subheader("📋 Detalle de Tickets del Dia")
                
                with st.container():
                    st.markdown('<div class="ticket-list">', unsafe_allow_html=True)
                    
                    for i, venta in enumerate(ventas_del_dia, 1):
                        col_num, col_hora, col_total = st.columns([1, 2, 1])
                        
                        with col_num:
                            st.write(f"**Ticket #{venta.get('numero_orden', 'N/A')}**")
                        with col_hora:
                            fecha_pago = venta.get('fecha_pago', '')
                            try:
                                hora_pago = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00')).strftime('%H:%M:%S')
                                st.write(f"🕐 {hora_pago}")
                            except:
                                st.write("🕐 N/A")
                        with col_total:
                            st.write(f"**${venta.get('total', 0):.2f}**")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("ℹ️ No hay ventas registradas para el dia de hoy.")
            
            st.markdown("---")
            
            # Boton de Cierre Z
            st.subheader("🔒 Generar Cierre Z")
            st.warning("⚠️ **Importante:** El cierre Z genera un reporte definitivo de las ventas del dia. Asegurate de que todas las ventas esten registradas.")
            
            if st.button("🎫 Generar Cierre Z", type="primary", use_container_width=True):
                if ventas_del_dia:
                    try:
                        # Obtener numero correlativo
                        numero_cierre_z = get_next_ticket_z_number(db)
                        
                        # Crear documento de cierre Z
                        cierre_doc = {
                            "_id": f"cierres_z:{str(uuid.uuid4())}",
                            "type": "cierres_z",
                            "numero_cierre_z": numero_cierre_z,
                            "fecha_cierre": fecha_hoy.isoformat(),
                            "fecha_generacion": datetime.now(timezone.utc).isoformat(),
                            "usuario": st.session_state.get('user_data', {}).get('usuario', 'Desconocido'),
                            "total_tickets": len(ventas_del_dia),
                            "total_ventas": total_ventas,
                            "tickets_incluidos": [v.get('numero_orden') for v in ventas_del_dia]
                        }
                        
                        # Guardar en base de datos
                        db.save(cierre_doc)
                        
                        # Generar PDF
                        pdf_data = generar_ticket_z_pdf(ventas_del_dia, numero_cierre_z, fecha_hoy)
                        
                        # Mostrar PDF
                        st.success(f"✅ Cierre Z #{numero_cierre_z:04d} generado exitosamente!")
                        
                        # Boton de descarga
                        st.download_button(
                            label="📄 Descargar Cierre Z",
                            data=pdf_data,
                            file_name=f"Cierre_Z_{numero_cierre_z:04d}_{fecha_hoy.strftime('%Y%m%d')}.pdf",
                            mime="application/pdf"
                        )
                        
                        # Mostrar PDF en linea
                        base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border: none;"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                        
                        # Log de la accion
                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        couchdb_utils.log_action(db, logged_in_user, f"Genero Cierre Z #{numero_cierre_z:04d} con {len(ventas_del_dia)} tickets por ${total_ventas:.2f}")
                        
                    except Exception as e:
                        st.error(f"❌ Error al generar el Cierre Z: {str(e)}")
                else:
                    st.error("❌ No hay ventas para generar un Cierre Z.")
        
        with col_history:
            st.subheader("📋 Historial de Cierres Z")
            
            # Obtener historial de cierres Z
            cierres_history = get_cierres_z_history(db)
            
            if cierres_history:
                st.write(f"**Total de cierres:** {len(cierres_history)}")
                st.markdown("---")
                
                # Mostrar los ultimos 10 cierres
                for cierre in cierres_history[:10]:
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px 0;">
                            <strong>Cierre Z #{cierre.get('numero_cierre_z', 'N/A'):04d}</strong><br>
                            📅 {datetime.fromisoformat(cierre.get('fecha_cierre', '')).strftime('%d/%m/%Y') if cierre.get('fecha_cierre') else 'N/A'}<br>
                            🎫 {cierre.get('total_tickets', 0)} tickets<br>
                            💰 ${cierre.get('total_ventas', 0):.2f}
                        </div>
                        """, unsafe_allow_html=True)
                
                if len(cierres_history) > 10:
                    st.info(f"Mostrando los últimos 10 de {len(cierres_history)} cierres totales")
            else:
                st.info("No hay cierres Z registrados")
    
    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesion para acceder a esta pagina.")