# pages/cierreX.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timezone
import uuid
import base64
from fpdf import FPDF
import pandas as pd

# Configuracion basica
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)
st.set_page_config(layout="wide", page_title="Cierre X", page_icon="../assets/LOGO.png")

# Estilos CSS
st.markdown("""
<style>
    .cierre-x-card {
        border: 2px solid #e74c3c;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: #fdf2f2;
    }
    .total-parcial {
        font-size: 1.8em;
        font-weight: bold;
        color: #e74c3c;
        text-align: center;
    }
    .ticket-range {
        background-color: #fff5f5;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #e74c3c;
    }
    .cierre-history {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def get_ventas_por_rango_datetime(db, datetime_inicio, datetime_fin):
    """
    Obtiene todas las ventas (tickets pagados) en el rango de fecha-hora especificado.
    """
    # Obtener todos los tickets pagados
    tickets = couchdb_utils.get_documents_by_partition(db, "tickets")
    tickets_pagados = [t for t in tickets if t.get('estado') == 'pagado']
    
    # Filtrar por rango de fecha-hora
    ventas_rango = []
    for ticket in tickets_pagados:
        fecha_pago = ticket.get('fecha_pago')
        if fecha_pago:
            try:
                # Convertir fecha de pago a datetime completo
                fecha_pago_dt = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00')).replace(tzinfo=None)
                if datetime_inicio <= fecha_pago_dt <= datetime_fin:
                    ventas_rango.append(ticket)
            except:
                continue
    
    return ventas_rango

def get_next_ticket_x_number(db):
    """
    Obtiene el siguiente numero correlativo para el ticket X
    """
    cierres_x = couchdb_utils.get_documents_by_partition(db, "cierres_x")
    
    max_numero = 0
    for cierre in cierres_x:
        numero = cierre.get('numero_cierre_x', 0)
        if isinstance(numero, int) and numero > max_numero:
            max_numero = numero
    
    return max_numero + 1

def generar_ticket_x_pdf(ventas_rango, numero_cierre_x, datetime_inicio, datetime_fin):
    """
    Genera el PDF del ticket de Cierre X
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
    pdf.cell(0, 8, 'CIERRE X', 0, 1, 'C')
    pdf.set_font('Arial', '', 8)
    pdf.cell(0, 4, f'Ticket X #{numero_cierre_x:04d}', 0, 1, 'C')
    pdf.cell(0, 4, f'Del: {datetime_inicio.strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
    pdf.cell(0, 4, f'Al: {datetime_fin.strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
    pdf.cell(0, 4, f'Generado: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1, 'C')
    pdf.ln(3)
    
    # Linea separadora
    pdf.cell(0, 1, '_' * 35, 0, 1, 'C')
    pdf.ln(2)
    
    # Resumen de ventas
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 5, 'REPORTE PARCIAL DE VENTAS', 0, 1, 'C')
    pdf.ln(2)
    
    # Detalles de tickets
    pdf.set_font('Arial', '', 7)
    total_ventas = 0
    ticket_count = 0
    
    if ventas_rango:
        pdf.cell(15, 4, 'Tick', 1, 0, 'C')
        pdf.cell(20, 4, 'Fecha', 1, 0, 'C')
        pdf.cell(15, 4, 'Hora', 1, 0, 'C')
        pdf.cell(15, 4, 'Total', 1, 1, 'C')
        
        # Ordenar por fecha de pago
        ventas_ordenadas = sorted(ventas_rango, 
                                key=lambda x: x.get('fecha_pago', ''))
        
        for venta in ventas_ordenadas:
            ticket_count += 1
            numero_ticket = venta.get('numero_orden', 'N/A')
            total = venta.get('total', 0)
            total_ventas += total
            
            # Obtener fecha y hora de pago
            fecha_pago = venta.get('fecha_pago', '')
            try:
                dt_pago = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00'))
                fecha_str = dt_pago.strftime('%d/%m')
                hora_str = dt_pago.strftime('%H:%M')
            except:
                fecha_str = 'N/A'
                hora_str = 'N/A'
            
            pdf.cell(15, 4, f'{numero_ticket}', 1, 0, 'C')
            pdf.cell(20, 4, fecha_str, 1, 0, 'C')
            pdf.cell(15, 4, hora_str, 1, 0, 'C')
            pdf.cell(15, 4, f'${total:.2f}', 1, 1, 'R')
    else:
        pdf.cell(0, 5, 'No hay ventas en el rango', 0, 1, 'C')
    
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
    duracion = datetime_fin - datetime_inicio
    horas_total = round(duracion.total_seconds() / 3600, 1)
    pdf.cell(0, 4, f'Periodo: {horas_total} hora(s)', 0, 1, 'C')
    pdf.cell(0, 4, f'Usuario: {st.session_state.get("user_data", {}).get("usuario", "N/A")}', 0, 1, 'C')
    pdf.ln(5)
    
    # Pie
    pdf.cell(0, 1, '_' * 35, 0, 1, 'C')
    pdf.ln(2)
    pdf.cell(0, 4, 'REPORTE PARCIAL', 0, 1, 'C')
    pdf.cell(0, 4, 'Entrega de caja', 0, 1, 'C')
    
    return bytes(pdf.output(dest='S'))

def get_cierres_x_history(db):
    """
    Obtiene el historial de cierres X generados
    """
    cierres_x = couchdb_utils.get_documents_by_partition(db, "cierres_x")
    
    # Ordenar por fecha de generacion (mas reciente primero)
    cierres_ordenados = sorted(cierres_x, 
                             key=lambda x: x.get('fecha_generacion', ''), 
                             reverse=True)
    
    return cierres_ordenados

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        st.title("Cierre X - Reporte Parcial de Ventas")
        st.markdown("---")
        
        # Seccion principal dividida en dos columnas
        col_main, col_history = st.columns([2, 1])
        
        with col_main:
            st.subheader("Generar Nuevo Cierre X")
            
            # Inicializar valores por defecto en session state si no existen
            if 'cierre_x_hora_inicio' not in st.session_state:
                st.session_state.cierre_x_hora_inicio = datetime.now().replace(hour=0, minute=0, second=0).time()
            if 'cierre_x_hora_fin' not in st.session_state:
                st.session_state.cierre_x_hora_fin = datetime.now().replace(hour=23, minute=59, second=59).time()
            
            # Seleccion de rango de fechas y horas
            col_inicio, col_fin = st.columns(2)
            
            with col_inicio:
                st.markdown("**Fecha y Hora de Inicio**")
                fecha_inicio = st.date_input(
                    "Fecha de inicio:",
                    value=datetime.now().date(),
                    key="fecha_inicio_x"
                )
                hora_inicio = st.time_input(
                    "Hora de inicio:",
                    value=st.session_state.cierre_x_hora_inicio,
                    key="hora_inicio_x"
                )
                # Actualizar session state cuando cambie
                if hora_inicio != st.session_state.cierre_x_hora_inicio:
                    st.session_state.cierre_x_hora_inicio = hora_inicio
            
            with col_fin:
                st.markdown("**Fecha y Hora de Fin**")
                fecha_fin = st.date_input(
                    "Fecha de fin:",
                    value=datetime.now().date(),
                    key="fecha_fin_x"
                )
                hora_fin = st.time_input(
                    "Hora de fin:",
                    value=st.session_state.cierre_x_hora_fin,
                    key="hora_fin_x"
                )
                # Actualizar session state cuando cambie
                if hora_fin != st.session_state.cierre_x_hora_fin:
                    st.session_state.cierre_x_hora_fin = hora_fin
            
            # Combinar fechas con horas
            datetime_inicio = datetime.combine(fecha_inicio, hora_inicio)
            datetime_fin = datetime.combine(fecha_fin, hora_fin)
            
            # Validar rango de fechas y horas
            if datetime_inicio > datetime_fin:
                st.error("La fecha y hora de inicio no puede ser mayor que la fecha y hora de fin.")
            else:
                # Obtener ventas del rango
                ventas_rango = get_ventas_por_rango_datetime(db, datetime_inicio, datetime_fin)
                
                # Mostrar resumen del rango
                st.markdown("### Resumen del Periodo")
                
                col1, col2, col3, col4 = st.columns(4)
                
                total_ventas = sum(venta.get('total', 0) for venta in ventas_rango)
                # Calcular duracion del periodo
                duracion_periodo = datetime_fin - datetime_inicio
                horas_periodo = round(duracion_periodo.total_seconds() / 3600, 1)
                
                with col1:
                    st.metric("Total Tickets", len(ventas_rango))
                with col2:
                    st.metric("Total Ventas", f"${total_ventas:.2f}")
                with col3:
                    st.metric("Promedio/Ticket", f"${total_ventas/len(ventas_rango):.2f}" if ventas_rango else "$0.00")
                with col4:
                    st.metric("Horas", f"{horas_periodo}h")
                
                # Mostrar detalles si hay ventas
                if ventas_rango:
                    with st.expander(f"Ver detalle de {len(ventas_rango)} tickets", expanded=False):
                        # Crear dataframe para mostrar
                        ticket_data = []
                        for venta in sorted(ventas_rango, key=lambda x: x.get('fecha_pago', '')):
                            fecha_pago = venta.get('fecha_pago', '')
                            try:
                                dt_pago = datetime.fromisoformat(fecha_pago.replace('Z', '+00:00'))
                                fecha_formateada = dt_pago.strftime('%d/%m/%Y %H:%M')
                            except:
                                fecha_formateada = 'N/A'
                            
                            ticket_data.append({
                                'Ticket': f"#{venta.get('numero_orden', 'N/A')}",
                                'Fecha y Hora': fecha_formateada,
                                'Total': f"${venta.get('total', 0):.2f}"
                            })
                        
                        df_tickets = pd.DataFrame(ticket_data)
                        st.dataframe(df_tickets, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay ventas en el rango de fechas seleccionado.")
                
                st.markdown("---")
                
                # Boton para generar Cierre X
                st.markdown("### Generar Cierre X")
                st.info("**Cierre X:** Reporte parcial para entrega de caja entre fechas especificas.")
                
                if st.button("Generar Cierre X", type="primary", use_container_width=True):
                    if ventas_rango:
                        try:
                            # Obtener numero correlativo
                            numero_cierre_x = get_next_ticket_x_number(db)
                            
                            # Crear documento de cierre X
                            cierre_doc = {
                                "_id": f"cierres_x:{str(uuid.uuid4())}",
                                "type": "cierres_x",
                                "numero_cierre_x": numero_cierre_x,
                                "datetime_inicio": datetime_inicio.isoformat(),
                                "datetime_fin": datetime_fin.isoformat(),
                                "fecha_generacion": datetime.now(timezone.utc).isoformat(),
                                "usuario": st.session_state.get('user_data', {}).get('usuario', 'Desconocido'),
                                "total_tickets": len(ventas_rango),
                                "total_ventas": total_ventas,
                                "tickets_incluidos": [v.get('numero_orden') for v in ventas_rango],
                                "horas_periodo": horas_periodo
                            }
                            
                            # Guardar en base de datos
                            db.save(cierre_doc)
                            
                            # Generar PDF
                            pdf_data = generar_ticket_x_pdf(ventas_rango, numero_cierre_x, datetime_inicio, datetime_fin)
                            
                            # Mostrar exito
                            st.success(f"Cierre X #{numero_cierre_x:04d} generado exitosamente!")
                            
                            # Boton de descarga
                            st.download_button(
                                label="Descargar Cierre X",
                                data=pdf_data,
                                file_name=f"Cierre_X_{numero_cierre_x:04d}_{datetime_inicio.strftime('%Y%m%d_%H%M')}_{datetime_fin.strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf"
                            )
                            
                            # Mostrar PDF en linea
                            base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border: none;"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                            
                            # Log de la accion
                            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            couchdb_utils.log_action(db, logged_in_user, f"Genero Cierre X #{numero_cierre_x:04d} del {datetime_inicio.strftime('%d/%m/%Y %H:%M')} al {datetime_fin.strftime('%d/%m/%Y %H:%M')} con {len(ventas_rango)} tickets por ${total_ventas:.2f}")
                            
                            # Refrescar para mostrar en historial
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error al generar el Cierre X: {str(e)}")
                    else:
                        st.error("No hay ventas en el rango seleccionado para generar un Cierre X.")
        
        with col_history:
            st.subheader("Historial de Cierres X")
            
            # Obtener historial
            cierres_history = get_cierres_x_history(db)
            
            if cierres_history:
                for cierre in cierres_history[:10]:  # Mostrar los ultimos 10
                    with st.container():
                        st.markdown('<div class="cierre-history">', unsafe_allow_html=True)
                        
                        # Informacion del cierre
                        numero = cierre.get('numero_cierre_x', 0)
                        datetime_inicio_hist = cierre.get('datetime_inicio', cierre.get('fecha_inicio', ''))
                        datetime_fin_hist = cierre.get('datetime_fin', cierre.get('fecha_fin', ''))
                        usuario_hist = cierre.get('usuario', 'N/A')
                        total_hist = cierre.get('total_ventas', 0)
                        tickets_hist = cierre.get('total_tickets', 0)
                        horas_hist = cierre.get('horas_periodo', cierre.get('dias_periodo', 0))
                        
                        try:
                            fecha_gen = datetime.fromisoformat(cierre.get('fecha_generacion', '')).strftime('%d/%m/%Y %H:%M')
                        except:
                            fecha_gen = 'N/A'
                        
                        try:
                            if datetime_inicio_hist and datetime_fin_hist:
                                inicio_str = datetime.fromisoformat(datetime_inicio_hist).strftime('%d/%m %H:%M')
                                fin_str = datetime.fromisoformat(datetime_fin_hist).strftime('%d/%m %H:%M')
                                periodo_str = f"{inicio_str} - {fin_str}"
                            else:
                                periodo_str = 'N/A'
                        except:
                            periodo_str = 'N/A'
                        
                        st.write(f"**Cierre X #{numero:04d}**")
                        st.write(f"**Periodo:** {periodo_str}")
                        st.write(f"**Usuario:** {usuario_hist}")
                        st.write(f"**Total:** ${total_hist:.2f} ({tickets_hist} tickets)")
                        st.write(f"**Duracion:** {horas_hist}h")
                        st.write(f"**Generado:** {fecha_gen}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("---")
            else:
                st.info("No hay cierres X generados aun.")
    
    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesion para acceder a esta pagina.")