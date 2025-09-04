# pages/reportes.py
import streamlit as st
import couchdb_utils
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import os
from fpdf import FPDF
import io
import base64
import pytz

st.set_page_config(layout="wide", page_title="Reportes del Sistema", page_icon="../assets/LOGO.png")
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)

# --- Estilos CSS ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .report-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .filter-box {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def get_timezone():
    """Obtener zona horaria de El Salvador"""
    return pytz.timezone('America/El_Salvador')

def convert_to_local_time(utc_datetime):
    """Convertir datetime UTC a hora local de El Salvador"""
    if isinstance(utc_datetime, str):
        # Limpiar formato de fecha - remover múltiples zonas horarias
        date_str = utc_datetime
        if date_str.endswith('+00:00+00:00'):
            date_str = date_str.replace('+00:00+00:00', '+00:00')
        elif date_str.endswith('Z'):
            date_str = date_str.replace('Z', '+00:00')
        
        try:
            utc_datetime = datetime.fromisoformat(date_str)
        except ValueError:
            # Si falla, intentar parseado manual
            try:
                if 'T' in date_str:
                    date_part, time_part = date_str.split('T')
                    if '+' in time_part:
                        time_part = time_part.split('+')[0]
                    elif 'Z' in time_part:
                        time_part = time_part.replace('Z', '')
                    
                    utc_datetime = datetime.fromisoformat(f"{date_part}T{time_part}")
                    utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
                else:
                    utc_datetime = datetime.fromisoformat(date_str)
                    utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
            except:
                # Como último recurso, usar fecha actual
                utc_datetime = datetime.now(timezone.utc)
    
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    
    local_tz = get_timezone()
    return utc_datetime.astimezone(local_tz)

def format_currency(amount):
    """Formatear cantidad como moneda"""
    return f"${amount:,.2f}"

def create_pdf_report(title, data, columns):
    """Crear reporte PDF"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.ln(10)
    
    # Encabezados
    pdf.set_font('Arial', 'B', 10)
    for col in columns:
        pdf.cell(40, 8, str(col), 1, 0, 'C')
    pdf.ln()
    
    # Datos
    pdf.set_font('Arial', '', 9)
    for row in data:
        for item in row:
            pdf.cell(40, 8, str(item)[:15], 1, 0, 'C')
        pdf.ln()
    
    # Devolver bytes directamente
    pdf_output = pdf.output(dest='S')
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1')
    else:
        return bytes(pdf_output)

def export_to_excel(df):
    """Exportar DataFrame a Excel"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

def filter_by_date_range(data, start_date, end_date, date_field='fecha_creacion'):
    """Filtrar datos por rango de fechas"""
    filtered_data = []
    items_with_date = 0
    items_filtered = 0
    
    for item in data:
        if date_field in item and item[date_field]:
            items_with_date += 1
            try:
                # Manejo especial para fecha_compra que viene solo como fecha (YYYY-MM-DD)
                if date_field == 'fecha_compra' and '-' in str(item[date_field]) and 'T' not in str(item[date_field]):
                    # Es una fecha simple formato YYYY-MM-DD
                    from datetime import datetime
                    item_date = datetime.strptime(item[date_field], '%Y-%m-%d').date()
                else:
                    # Es una fecha con hora/zona horaria, usar conversión normal
                    item_date = convert_to_local_time(item[date_field]).date()
                
                if start_date <= item_date <= end_date:
                    filtered_data.append(item)
                    items_filtered += 1
            except Exception:
                # Agregar el item sin filtrar si no se puede convertir la fecha
                filtered_data.append(item)
                continue
        else:
            # Si no tiene fecha, incluirlo por defecto
            filtered_data.append(item)
    
    
    return filtered_data

def get_period_dates(period_type, custom_start=None, custom_end=None):
    """Obtener fechas según el periodo seleccionado"""
    local_tz = get_timezone()
    today = datetime.now(local_tz).date()
    
    if period_type == "Día" or period_type == "Dia":
        return today, today
    elif period_type == "Semana":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        return start_date, end_date
    elif period_type == "Mes":
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month - timedelta(days=next_month.day)
        return start_date, end_date
    elif period_type == "Personalizado":
        return custom_start, custom_end
    else:
        # Fallback por defecto - día actual
        return today, today

# --- P�gina Principal ---
if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        st.markdown('<div class="report-header"><h1> Sistema de Reportes Avanzados</h1></div>', unsafe_allow_html=True)
        
        # Men� de reportes
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📊 Ventas", "💰 Márgenes", "👨‍🍳 Meseros", "💵 Propinas", 
            "📦 Compras", "📋 Inventario", "👥 Usuarios"
        ])
        
        # --- TAB 1: REPORTE DE VENTAS ---
        with tab1:
            st.header("📊 Reporte de Ventas")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="filter-box">', unsafe_allow_html=True)
                st.subheader("Filtros de Fecha")
                period_type = st.selectbox("Periodo", ["Día", "Semana", "Mes", "Personalizado"])
                
                if period_type == "Personalizado":
                    start_date = st.date_input("Fecha de inicio", value=datetime.now().date() - timedelta(days=30))
                    end_date = st.date_input("Fecha de fin", value=datetime.now().date())
                else:
                    start_date, end_date = get_period_dates(period_type)
                    st.info(f"Periodo: {start_date} al {end_date}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="filter-box">', unsafe_allow_html=True)
                st.subheader("Opciones")
                show_details = st.checkbox("Mostrar detalles de productos", value=True)
                group_by_ticket = st.checkbox("Agrupar por ticket", value=False)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Obtener datos de base de datos
            all_orders = couchdb_utils.get_documents_by_partition(db, "ordenes")
            all_mesas = couchdb_utils.get_documents_by_partition(db, "mesas")
            all_meseros = couchdb_utils.get_documents_by_partition(db, "Usuario")
            all_tickets = couchdb_utils.get_documents_by_partition(db, "tickets")
            
            # Crear diccionarios de mapeo
            mesas_dict = {mesa['_id']: mesa for mesa in all_mesas}
            meseros_dict = {mesero['_id']: mesero for mesero in all_meseros if mesero.get('id_rol') == 3}
            
            # Filtrar solo órdenes pagadas del período seleccionado
            filtered_orders = []
            for orden in all_orders:
                if orden.get('estado') == 'pagada':
                    # Usar fecha_pago si existe, sino fecha_creacion
                    date_to_check_str = orden.get('fecha_pago', orden.get('fecha_creacion'))
                    if date_to_check_str:
                        try:
                            local_dt = convert_to_local_time(date_to_check_str)
                            if local_dt:
                                order_date = local_dt.date()
                                if start_date <= order_date <= end_date:
                                    filtered_orders.append(orden)
                        except:
                            continue
            
            if filtered_orders:
                # M�tricas generales
                st.subheader("📈 Resumen General")
                col1, col2, col3, col4 = st.columns(4)
                
                total_sales = sum(float(order.get('total', 0)) for order in filtered_orders)
                total_tickets = len(filtered_orders)
                avg_ticket = total_sales / total_tickets if total_tickets > 0 else 0
                # Contar solo items no anulados
                total_items = sum(sum(1 for item in order.get('items', []) if not item.get('anulado', False)) for order in filtered_orders)
                
                col1.metric("💰 Ventas Totales", format_currency(total_sales))
                col2.metric("🎫 Total Tickets", total_tickets)
                col3.metric("📊 Ticket Promedio", format_currency(avg_ticket))
                col4.metric("🍽️ Items Vendidos", total_items)
                
                # Datos detallados
                sales_data = []
                for order in filtered_orders:
                    # Usar fecha_pago si existe, sino fecha_creacion
                    date_to_check_str = order.get('fecha_pago', order.get('fecha_creacion'))
                    local_time = convert_to_local_time(date_to_check_str) if date_to_check_str else datetime.now()
                    
                    # Obtener información de mesa y mesero
                    mesa_info = mesas_dict.get(order.get('mesa_id'), {})
                    mesero_info = meseros_dict.get(order.get('mesero_id'), {})
                    mesa_nombre = mesa_info.get('descripcion', f"Mesa {order.get('mesa_id', 'N/A')}")
                    mesero_nombre = mesero_info.get('nombre', f"Mesero {order.get('mesero_id', 'N/A')}")
                    
                    # Buscar información del ticket para método de pago
                    ticket_info = next((ticket for ticket in all_tickets if ticket.get('orden_id') == order.get('_id')), {})
                    metodo_pago = ticket_info.get('pago_info', {}).get('metodo', 'No especificado')
                    
                    if show_details and 'items' in order and order['items']:
                        for item in order['items']:
                            # Saltar items anulados
                            if item.get('anulado', False):
                                continue
                            sales_data.append({
                                'Ticket': order.get('numero_orden', order.get('_id', '').split(':')[-1]),
                                'Fecha': local_time.strftime('%Y-%m-%d'),
                                'Hora': local_time.strftime('%H:%M'),
                                'Producto': item.get('nombre', ''),
                                'Cantidad': item.get('cantidad', 0),
                                'Precio Unit.': item.get('precio_unitario', 0),
                                'Total': item.get('cantidad', 0) * item.get('precio_unitario', 0),
                                'Mesa': mesa_nombre,
                                'Mesero': mesero_nombre,
                                'Método Pago': metodo_pago,
                                'Comentarios': item.get('comentarios', '')
                            })
                    else:
                        # Mostrar solo resumen por ticket/orden
                        items_no_anulados = [item for item in order.get('items', []) if not item.get('anulado', False)]
                        sales_data.append({
                            'Ticket': order.get('numero_orden', order.get('_id', '').split(':')[-1]),
                            'Fecha': local_time.strftime('%Y-%m-%d'),
                            'Hora': local_time.strftime('%H:%M'),
                            'Total': order.get('total', 0),
                            'Mesa': mesa_nombre,
                            'Mesero': mesero_nombre,
                            'Método Pago': metodo_pago,
                            'Items': len(items_no_anulados),
                            'Estado': order.get('estado', 'N/A')
                        })
                
                # DataFrame y visualización
                if sales_data:
                    df_sales = pd.DataFrame(sales_data)
                    
                    # Si está habilitado "Agrupar por ticket" y tenemos detalles, agrupar los datos
                    if group_by_ticket and show_details and 'Producto' in df_sales.columns:
                        st.subheader("🎫 Datos Agrupados por Ticket")
                        
                        # Mostrar cada ticket con sus productos
                        tickets_grouped = df_sales.groupby('Ticket')
                        
                        for ticket_num, ticket_data in tickets_grouped:
                            ticket_total = ticket_data['Total'].sum()
                            with st.expander(f"Ticket #{ticket_num} - {ticket_data['Mesa'].iloc[0]} - {ticket_data['Mesero'].iloc[0]} - Total: ${ticket_total:.2f}", expanded=False):
                                ticket_summary = ticket_data[['Producto', 'Cantidad', 'Precio Unit.', 'Total', 'Comentarios']].copy()
                                st.dataframe(ticket_summary, use_container_width=True)
                                
                                st.markdown(f"**Fecha:** {ticket_data['Fecha'].iloc[0]} {ticket_data['Hora'].iloc[0]}")
                                st.markdown(f"**Método de Pago:** {ticket_data['Método Pago'].iloc[0]}")
                                st.markdown(f"**Total del Ticket:** ${ticket_total:.2f}")
                    
                    # Gráficos
                    st.subheader("📊 Visualizaciones")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if show_details and 'Producto' in df_sales.columns:
                            # Gr�fico de productos m�s vendidos
                            product_sales = df_sales.groupby('Producto').agg({
                                'Cantidad': 'sum',
                                'Total': 'sum'
                            }).reset_index()
                            
                            fig = px.bar(product_sales.head(10), 
                                       x='Producto', y='Cantidad',
                                       title='Top 10 Productos Mas Vendidos')
                            fig.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            # Gr�fico de ventas por d�a
                            if 'Fecha' in df_sales.columns:
                                daily_sales = df_sales.groupby('Fecha')['Total'].sum().reset_index()
                                fig = px.line(daily_sales, x='Fecha', y='Total',
                                            title='Ventas por Dia')
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("No hay datos de fecha disponibles para el grafico")
                    
                    with col2:
                        # Gr�fico de ventas por hora
                        if 'Hora' in df_sales.columns:
                            hourly_sales = df_sales.groupby('Hora')['Total'].sum().reset_index()
                            fig = px.bar(hourly_sales, x='Hora', y='Total',
                                       title='Ventas por Hora del Dia')
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No hay datos de hora disponibles para el gráfico")

                    # Tabla de datos (solo mostrar si no está agrupado por ticket)
                    if not (group_by_ticket and show_details):
                        st.subheader(" Datos Detallados")
                        st.dataframe(df_sales, use_container_width=True)
                    
                    # Botones de exportaci�n
                    st.subheader(" Exportar Reporte")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(" Generar PDF", key="pdf_ventas"):
                            pdf_data = create_pdf_report(
                                f"Reporte de Ventas ({start_date} - {end_date})",
                                df_sales.values.tolist(),
                                df_sales.columns.tolist()
                            )
                            st.download_button(
                                label=" Descargar PDF",
                                data=pdf_data,
                                file_name=f"reporte_ventas_{start_date}_{end_date}.pdf",
                                mime="application/pdf"
                            )
                    
                    with col2:
                        if st.button("📊 Generar Excel", key="excel_ventas"):
                            excel_data = export_to_excel(df_sales)
                            st.download_button(
                                label=" Descargar Excel",
                                data=excel_data,
                                file_name=f"reporte_ventas_{start_date}_{end_date}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
            else:
                st.warning("No se encontraron ventas en el periodo seleccionado.")
        
        # --- TAB 2: REPORTE DE M�RGENES ---
        with tab2:
            st.header(" Reporte de Margenes de Ganancia")
            
            # Filtros similares
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="filter-box">', unsafe_allow_html=True)
                st.subheader("Filtros de Fecha")
                period_type_margin = st.selectbox("Periodo", ["Día", "Semana", "Mes", "Personalizado"], key="margin_period")

                if period_type_margin == "Personalizado":
                    start_date_margin = st.date_input("Fecha de inicio", value=datetime.now().date() - timedelta(days=30), key="margin_start")
                    end_date_margin = st.date_input("Fecha de fin", value=datetime.now().date(), key="margin_end")
                else:
                    start_date_margin, end_date_margin = get_period_dates(period_type_margin)
                    st.info(f"Periodo: {start_date_margin} al {end_date_margin}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Obtener datos de platos para precios de compra
            all_platos = couchdb_utils.get_documents_by_partition(db, "platos")
            platos_dict = {plato.get('descripcion', ''): plato for plato in all_platos if plato.get('descripcion')}
            
            # Filtrar órdenes pagadas del período usando zona horaria local
            filtered_orders_margin = []
            for orden in all_orders:
                if orden.get('estado') == 'pagada':
                    date_to_check_str = orden.get('fecha_pago', orden.get('fecha_creacion'))
                    if date_to_check_str:
                        try:
                            local_dt = convert_to_local_time(date_to_check_str)
                            if local_dt:
                                order_date = local_dt.date()
                                if start_date_margin <= order_date <= end_date_margin:
                                    filtered_orders_margin.append(orden)
                        except:
                            continue
            
            if filtered_orders_margin:
                # Calcular m�rgenes
                margin_data = []
                
                for order in filtered_orders_margin:
                    date_to_check_str = order.get('fecha_pago', order.get('fecha_creacion'))
                    local_time = convert_to_local_time(date_to_check_str) if date_to_check_str else datetime.now()
                    
                    if 'items' in order:
                        for item in order['items']:
                            # Saltar items anulados
                            if item.get('anulado', False):
                                continue
                                
                            nombre_plato = item.get('nombre', '')
                            precio_venta = float(item.get('precio_unitario', 0))
                            cantidad = int(item.get('cantidad', 0))
                            
                            # Buscar precio de compra en la base de datos de platos
                            plato_info = platos_dict.get(nombre_plato, {})
                            # El precio_normal en platos es el precio de venta, necesitamos el costo
                            # Si hay precio_costo lo usamos, sino estimamos 60% del precio de venta como costo
                            precio_compra = float(plato_info.get('precio_costo', plato_info.get('precio_normal', precio_venta) * 0.6))
                            
                            total_venta = precio_venta * cantidad
                            total_costo = precio_compra * cantidad
                            margen = total_venta - total_costo
                            margen_pct = (margen / total_venta * 100) if total_venta > 0 else 0
                            
                            margin_data.append({
                                'Fecha': local_time.strftime('%Y-%m-%d'),
                                'Producto': nombre_plato,
                                'Cantidad': cantidad,
                                'Precio Compra': precio_compra,
                                'Precio Venta': precio_venta,
                                'Total Costo': total_costo,
                                'Total Venta': total_venta,
                                'Margen $': margen,
                                'Margen %': margen_pct,
                                'Ticket': order.get('numero_orden', order.get('_id', '').split(':')[-1])
                            })
                
                
                if margin_data:
                    df_margins = pd.DataFrame(margin_data)
                    
                    # M�tricas
                    st.subheader(" Resumen de Margenes")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_sales_margin = df_margins['Total Venta'].sum()
                    total_cost_margin = df_margins['Total Costo'].sum()
                    total_margin = total_sales_margin - total_cost_margin
                    avg_margin_pct = (total_margin / total_sales_margin * 100) if total_sales_margin > 0 else 0
                    
                    col1.metric(" Ventas Totales", format_currency(total_sales_margin))
                    col2.metric(" Costos Totales", format_currency(total_cost_margin))
                    col3.metric(" Margen Total", format_currency(total_margin))
                    col4.metric(" Margen %", f"{avg_margin_pct:.1f}%")
                    
                    # Gráficos
                    st.subheader(" Análisis de Márgenes")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Top productos por margen
                        product_margins = df_margins.groupby('Producto').agg({
                            'Margen $': 'sum',
                            'Cantidad': 'sum'
                        }).reset_index().sort_values('Margen $', ascending=False)
                        
                        fig = px.bar(product_margins.head(10), 
                                   x='Producto', y='Margen $',
                                   title='Top 10 Productos por Margen')
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Margen por fecha
                        daily_margins = df_margins.groupby('Fecha')['Margen $'].sum().reset_index()
                        fig = px.line(daily_margins, x='Fecha', y='Margen $',
                                    title='Margen de Ganancia por Dia')
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabla detallada
                    st.subheader(" Detalle de Margenes")
                    st.dataframe(df_margins, use_container_width=True)
                    
                    # Exportaci�n
                    st.subheader(" Exportar Reporte")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(" Generar PDF", key="pdf_margins"):
                            pdf_data = create_pdf_report(
                                f"Reporte de Margenes ({start_date_margin} - {end_date_margin})",
                                df_margins.values.tolist(),
                                df_margins.columns.tolist()
                            )
                            st.download_button(
                                label=" Descargar PDF",
                                data=pdf_data,
                                file_name=f"reporte_margenes_{start_date_margin}_{end_date_margin}.pdf",
                                mime="application/pdf"
                            )
                    
                    with col2:
                        if st.button(" Generar Excel", key="excel_margins"):
                            excel_data = export_to_excel(df_margins)
                            st.download_button(
                                label=" Descargar Excel",
                                data=excel_data,
                                file_name=f"reporte_margenes_{start_date_margin}_{end_date_margin}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
            else:
                st.warning("No se encontraron datos en el per�odo seleccionado.")
        
        # --- TAB 3: REPORTE POR MESERO ---
        with tab3:
            st.header("Reporte de Ventas por Mesero")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="filter-box">', unsafe_allow_html=True)
                st.subheader("Filtros")
                period_type_mesero = st.selectbox("Periodo", ["Día", "Semana", "Mes", "Personalizado"], key="mesero_period")

                if period_type_mesero == "Personalizado":
                    start_date_mesero = st.date_input("Fecha de inicio", value=datetime.now().date() - timedelta(days=30), key="mesero_start")
                    end_date_mesero = st.date_input("Fecha de fin", value=datetime.now().date(), key="mesero_end")
                else:
                    start_date_mesero, end_date_mesero = get_period_dates(period_type_mesero)
                    st.info(f"Periodo: {start_date_mesero} al {end_date_mesero}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Obtener meseros �nicos
            all_meseros = list(set(order.get('mesero_id', '') for order in all_orders if order.get('mesero_id')))
            
            with col2:
                st.markdown('<div class="filter-box">', unsafe_allow_html=True)
                st.subheader("Seleccionar Mesero")
                selected_mesero = st.selectbox("Mesero", ["Todos"] + all_meseros, key="select_mesero")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Filtrar órdenes pagadas del período usando zona horaria local
            filtered_orders_mesero = []
            for orden in all_orders:
                if orden.get('estado') == 'pagada':
                    date_to_check_str = orden.get('fecha_pago', orden.get('fecha_creacion'))
                    if date_to_check_str:
                        try:
                            local_dt = convert_to_local_time(date_to_check_str)
                            if local_dt:
                                order_date = local_dt.date()
                                if start_date_mesero <= order_date <= end_date_mesero:
                                    filtered_orders_mesero.append(orden)
                        except:
                            continue
            
            if selected_mesero != "Todos":
                filtered_orders_mesero = [order for order in filtered_orders_mesero if order.get('mesero_id') == selected_mesero]
            
            if filtered_orders_mesero:
                # Analizar datos por mesero
                mesero_data = {}
                for order in filtered_orders_mesero:
                    mesero = order.get('mesero_id', 'Sin asignar')
                    
                    if mesero not in mesero_data:
                        mesero_data[mesero] = {
                            'ventas': 0,
                            'tickets': 0,
                            'items': 0,
                            'propina': 0
                        }
                    
                    mesero_data[mesero]['ventas'] += float(order.get('total', 0))
                    mesero_data[mesero]['tickets'] += 1
                    mesero_data[mesero]['items'] += len(order.get('items', []))
                    mesero_data[mesero]['propina'] += float(order.get('total', 0)) * 0.1  # 10% propina
                
                # Crear DataFrame
                mesero_summary = []
                for mesero, data in mesero_data.items():
                    mesero_summary.append({
                        'Mesero': mesero,
                        'Ventas': data['ventas'],
                        'Tickets': data['tickets'],
                        'Items': data['items'],
                        'Ticket Promedio': data['ventas'] / data['tickets'] if data['tickets'] > 0 else 0,
                        'Propina Estimada': data['propina']
                    })
                
                df_meseros = pd.DataFrame(mesero_summary)
                df_meseros = df_meseros.sort_values('Ventas', ascending=False)
                
                # M�tricas generales
                st.subheader(" Resumen por Meseros")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric(" Total Meseros", len(df_meseros))
                col2.metric(" Ventas Totales", format_currency(df_meseros['Ventas'].sum()))
                col3.metric(" Total Tickets", int(df_meseros['Tickets'].sum()))
                col4.metric(" Propinas Totales", format_currency(df_meseros['Propina Estimada'].sum()))
                
                # Gráficos
                st.subheader(" Análisis por Mesero")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(df_meseros, x='Mesero', y='Ventas',
                               title='Ventas por Mesero')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.pie(df_meseros, values='Tickets', names='Mesero',
                               title='Distribucion de Tickets por Mesero')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Tabla detallada
                st.subheader(" Detalle por Mesero")
                st.dataframe(df_meseros, use_container_width=True)
                
                # Exportaci�n
                st.subheader(" Exportar Reporte")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(" Generar PDF", key="pdf_meseros"):
                        pdf_data = create_pdf_report(
                            f"Reporte por Meseros ({start_date_mesero} - {end_date_mesero})",
                            df_meseros.values.tolist(),
                            df_meseros.columns.tolist()
                        )
                        st.download_button(
                            label=" Descargar PDF",
                            data=pdf_data,
                            file_name=f"reporte_meseros_{start_date_mesero}_{end_date_mesero}.pdf",
                            mime="application/pdf"
                        )
                
                with col2:
                    if st.button(" Generar Excel", key="excel_meseros"):
                        excel_data = export_to_excel(df_meseros)
                        st.download_button(
                            label=" Descargar Excel",
                            data=excel_data,
                            file_name=f"reporte_meseros_{start_date_mesero}_{end_date_mesero}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.warning("No se encontraron datos para el mesero y per�odo seleccionado.")
        
        # --- TAB 4: REPORTE DE PROPINAS ---
        with tab4:
            st.header("Reporte de Propinas")
            
            # Filtros
            st.markdown('<div class="filter-box">', unsafe_allow_html=True)
            st.subheader("Configuracion de Propinas")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                period_type_propina = st.selectbox("Periodo", ["Día", "Semana", "Mes", "Personalizado"], key="propina_period")

            with col2:
                propina_pct = st.slider("Porcentaje de Propina (%)", min_value=5, max_value=20, value=10, step=1)
            
            with col3:
                distribuir_propina = st.checkbox("Distribuir entre meseros", value=True)
            
            if period_type_propina == "Personalizado":
                col1, col2 = st.columns(2)
                with col1:
                    start_date_propina = st.date_input("Fecha de inicio", value=datetime.now().date() - timedelta(days=30), key="propina_start")
                with col2:
                    end_date_propina = st.date_input("Fecha de fin", value=datetime.now().date(), key="propina_end")
            else:
                start_date_propina, end_date_propina = get_period_dates(period_type_propina)
                st.info(f"Periodo: {start_date_propina} al {end_date_propina}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Filtrar órdenes pagadas del período para calcular propinas
            filtered_orders_propina = []
            for orden in all_orders:
                if orden.get('estado') == 'pagada':
                    date_to_check_str = orden.get('fecha_pago', orden.get('fecha_creacion'))
                    if date_to_check_str:
                        try:
                            local_dt = convert_to_local_time(date_to_check_str)
                            if local_dt:
                                order_date = local_dt.date()
                                if start_date_propina <= order_date <= end_date_propina:
                                    filtered_orders_propina.append(orden)
                        except:
                            continue
            
            if filtered_orders_propina:
                propina_data = {}
                total_ventas_propina = 0
                
                for order in filtered_orders_propina:
                    mesero = order.get('mesero_id', 'Sin asignar')
                    venta = float(order.get('total', 0))
                    propina = venta * (propina_pct / 100)
                    
                    if mesero not in propina_data:
                        propina_data[mesero] = {
                            'ventas': 0,
                            'propina': 0,
                            'tickets': 0
                        }
                    
                    propina_data[mesero]['ventas'] += venta
                    propina_data[mesero]['propina'] += propina
                    propina_data[mesero]['tickets'] += 1
                    total_ventas_propina += venta
                
                total_propinas = total_ventas_propina * (propina_pct / 100)
                
                # Si se distribuye equitativamente
                if distribuir_propina and len(propina_data) > 1:
                    propina_por_mesero = total_propinas / len(propina_data)
                    for mesero in propina_data:
                        propina_data[mesero]['propina_distribuida'] = propina_por_mesero
                
                # Crear DataFrame
                propina_summary = []
                for mesero, data in propina_data.items():
                    row = {
                        'Mesero': mesero,
                        'Ventas': data['ventas'],
                        'Tickets': data['tickets'],
                        'Propina Individual': data['propina'],
                        'Propina Distribuida': data.get('propina_distribuida', data['propina']) if distribuir_propina else data['propina']
                    }
                    propina_summary.append(row)
                
                df_propinas = pd.DataFrame(propina_summary)
                
                # M�tricas
                st.subheader(" Resumen de Propinas")
                col1, col2, col3, col4 = st.columns(4)

                col1.metric(" Ventas del Periodo", format_currency(total_ventas_propina))
                col2.metric(" Total Propinas", format_currency(total_propinas))
                col3.metric(" Porcentaje", f"{propina_pct}%")
                col4.metric(" Meseros", len(propina_data))
                
                # Gráficos
                st.subheader(" Distribución de Propinas")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    propina_column = 'Propina Distribuida' if distribuir_propina else 'Propina Individual'
                    fig = px.bar(df_propinas, x='Mesero', y=propina_column,
                               title=f'Propinas por Mesero ({propina_column})')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.pie(df_propinas, values=propina_column, names='Mesero',
                               title='Distribucion % de Propinas')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Tabla detallada
                st.subheader(" Detalle de Propinas")
                st.dataframe(df_propinas, use_container_width=True)
                
                # Exportaci�n
                st.subheader(" Exportar Reporte")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(" Generar PDF", key="pdf_propinas"):
                        pdf_data = create_pdf_report(
                            f"Reporte de Propinas ({start_date_propina} - {end_date_propina})",
                            df_propinas.values.tolist(),
                            df_propinas.columns.tolist()
                        )
                        st.download_button(
                            label=" Descargar PDF",
                            data=pdf_data,
                            file_name=f"reporte_propinas_{start_date_propina}_{end_date_propina}.pdf",
                            mime="application/pdf"
                        )
                
                with col2:
                    if st.button(" Generar Excel", key="excel_propinas"):
                        excel_data = export_to_excel(df_propinas)
                        st.download_button(
                            label=" Descargar Excel",
                            data=excel_data,
                            file_name=f"reporte_propinas_{start_date_propina}_{end_date_propina}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.warning("No se encontraron ventas en el per�odo seleccionado.")
        
        # --- TAB 5: REPORTE DE COMPRAS ---
        with tab5:
            st.header(" Reporte de Compras")
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="filter-box">', unsafe_allow_html=True)
                st.subheader("Filtros de Fecha")
                period_type_compras = st.selectbox("Periodo", ["Día", "Semana", "Mes", "Personalizado"], key="compras_period")

                if period_type_compras == "Personalizado":
                    start_date_compras = st.date_input("Fecha de inicio", value=datetime.now().date() - timedelta(days=30), key="compras_start")
                    end_date_compras = st.date_input("Fecha de fin", value=datetime.now().date(), key="compras_end")
                else:
                    start_date_compras, end_date_compras = get_period_dates(period_type_compras)
                    st.info(f"Periodo: {start_date_compras} al {end_date_compras}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Obtener datos de compras
            all_compras = couchdb_utils.get_documents_by_partition(db, "compras")
            
            
            filtered_compras = filter_by_date_range(all_compras, start_date_compras, end_date_compras, date_field='fecha_compra')
            
            if filtered_compras:
                # Procesar datos de compras
                compras_data = []
                total_compras = 0
                
                for compra in filtered_compras:
                    # Manejar fecha_compra específicamente para compras (solo fecha, sin hora)
                    fecha_compra = compra.get('fecha_compra', '')
                    if fecha_compra:
                        try:
                            # Para fechas solo con formato YYYY-MM-DD (sin hora ni zona horaria)
                            fecha_mostrar = fecha_compra
                        except:
                            fecha_mostrar = fecha_compra
                    else:
                        fecha_mostrar = ''
                    
                    # Procesar cada item de la compra
                    if 'items' in compra and compra['items']:
                        for item in compra['items']:
                            item_total = float(item.get('Total', 0))
                            total_compras += item_total
                            
                            compras_data.append({
                                'Fecha': fecha_mostrar,
                                'Proveedor': compra.get('proveedor_nombre', ''),
                                'Producto': item.get('Descripción', ''),
                                'Cantidad': item.get('Cantidad', 0),
                                'Unidad': item.get('Unidad', ''),
                                'Precio Unitario': item.get('Precio Unitario', 0),
                                'Total': item_total,
                                'Factura': compra.get('numero_documento', ''),
                                'Subtotal Compra': compra.get('subtotal', 0),
                                'IVA': compra.get('iva', 0),
                                'Total Compra': compra.get('total', 0)
                            })
                    else:
                        # Si no hay items, crear un registro con los datos generales
                        compra_total = float(compra.get('total', 0))
                        total_compras += compra_total
                        
                        compras_data.append({
                            'Fecha': fecha_mostrar,
                            'Proveedor': compra.get('proveedor_nombre', ''),
                            'Producto': 'N/A',
                            'Cantidad': 0,
                            'Unidad': '',
                            'Precio Unitario': 0,
                            'Total': compra_total,
                            'Factura': compra.get('numero_documento', ''),
                            'Subtotal Compra': compra.get('subtotal', 0),
                            'IVA': compra.get('iva', 0),
                            'Total Compra': compra_total
                        })
                
                df_compras = pd.DataFrame(compras_data)
                
                # M�tricas
                st.subheader(" Resumen de Compras")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric(" Total Compras", format_currency(total_compras))
                col2.metric(" Total Items", len(df_compras))
                col3.metric(" Proveedores", df_compras['Proveedor'].nunique())
                col4.metric(" Compra Promedio", format_currency(df_compras['Total'].mean()))
                
                # Gr�ficos
                st.subheader(" Analisis de Compras")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Compras por proveedor
                    proveedor_compras = df_compras.groupby('Proveedor')['Total'].sum().reset_index()
                    fig = px.pie(proveedor_compras, values='Total', names='Proveedor',
                               title='Compras por Proveedor')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Compras por fecha
                    daily_compras = df_compras.groupby('Fecha')['Total'].sum().reset_index()
                    fig = px.line(daily_compras, x='Fecha', y='Total',
                                title='Compras por Dia')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Tabla detallada
                st.subheader(" Detalle de Compras")
                st.dataframe(df_compras, use_container_width=True)
                
                # Exportaci�n
                st.subheader(" Exportar Reporte")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(" Generar PDF", key="pdf_compras"):
                        pdf_data = create_pdf_report(
                            f"Reporte de Compras ({start_date_compras} - {end_date_compras})",
                            df_compras.values.tolist(),
                            df_compras.columns.tolist()
                        )
                        st.download_button(
                            label=" Descargar PDF",
                            data=pdf_data,
                            file_name=f"reporte_compras_{start_date_compras}_{end_date_compras}.pdf",
                            mime="application/pdf"
                        )
                
                with col2:
                    if st.button(" Generar Excel", key="excel_compras"):
                        excel_data = export_to_excel(df_compras)
                        st.download_button(
                            label=" Descargar Excel",
                            data=excel_data,
                            file_name=f"reporte_compras_{start_date_compras}_{end_date_compras}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.warning("No se encontraron compras en el per�odo seleccionado.")
        
        # --- TAB 6: REPORTE DE INVENTARIO ---
        with tab6:
            st.header(" Reporte de Inventario")
            
            # Obtener datos de inventario
            all_inventory = couchdb_utils.get_documents_by_partition(db, "inventario")
            
            # Obtener ingredientes y platos para mapear nombres
            ingredientes = couchdb_utils.get_documents_by_partition(db, "ingredientes")
            platos = couchdb_utils.get_documents_by_partition(db, "platos")
            
            # Crear diccionarios de mapeo
            ingredientes_dict = {ing['_id']: ing.get('descripcion', 'Ingrediente desconocido') for ing in ingredientes}
            platos_dict = {plato['_id']: plato.get('descripcion', 'Plato desconocido') for plato in platos}
            
            if all_inventory:
                # Procesar movimientos de inventario
                inventory_data = []
                
                for movimiento in all_inventory:
                    # FILTRO: Solo procesar movimientos de ingredientes, excluir platos
                    if not movimiento.get('ingrediente_id'):
                        continue  # Saltar movimientos que no sean de ingredientes
                    
                    local_time = convert_to_local_time(movimiento.get('fecha_creacion', ''))
                    
                    # Determinar el tipo de movimiento
                    tipo_mov = movimiento.get('tipo', '')
                    cantidad = float(movimiento.get('cantidad', 0))
                    
                    # Mapear tipos
                    if tipo_mov == 'entrada':
                        tipo_display = 'Ingreso'
                        cantidad = abs(cantidad)
                    elif tipo_mov == 'salida':
                        tipo_display = 'Egreso'
                        cantidad = -abs(cantidad)
                    else:
                        tipo_display = tipo_mov.title()
                    
                    # Obtener nombre del ingrediente
                    ingrediente_id = movimiento.get('ingrediente_id')
                    producto_nombre = ingredientes_dict.get(ingrediente_id, 'Ingrediente desconocido')
                    
                    inventory_data.append({
                        'Ingrediente': producto_nombre,
                        'Fecha': local_time.strftime('%Y-%m-%d'),
                        'Tipo': tipo_display,
                        'Cantidad': cantidad,
                        'Motivo': movimiento.get('motivo', movimiento.get('comentarios', '')),
                        'Usuario': movimiento.get('usuario', ''),
                        'ID Ingrediente': ingrediente_id
                    })
                
                if inventory_data:
                    df_inventory = pd.DataFrame(inventory_data)
                    
                    # Filtros
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        ingredientes_disponibles = df_inventory['Ingrediente'].unique().tolist()
                        selected_ingredients = st.multiselect("Ingredientes", ingredientes_disponibles, default=ingredientes_disponibles[:5] if len(ingredientes_disponibles) > 5 else ingredientes_disponibles)
                    
                    with col2:
                        tipo_movimiento = st.selectbox("Tipo de Movimiento", ["Todos", "Ingreso", "Egreso"])
                    
                    with col3:
                        fecha_desde = st.date_input("Desde", value=datetime.now().date() - timedelta(days=30))
                        fecha_hasta = st.date_input("Hasta", value=datetime.now().date())
                    
                    # Aplicar filtros
                    df_filtered = df_inventory.copy()
                    
                    if selected_ingredients:
                        df_filtered = df_filtered[df_filtered['Ingrediente'].isin(selected_ingredients)]
                    
                    if tipo_movimiento != "Todos":
                        df_filtered = df_filtered[df_filtered['Tipo'] == tipo_movimiento]
                    
                    df_filtered['Fecha'] = pd.to_datetime(df_filtered['Fecha'])
                    df_filtered = df_filtered[
                        (df_filtered['Fecha'] >= pd.to_datetime(fecha_desde)) &
                        (df_filtered['Fecha'] <= pd.to_datetime(fecha_hasta))
                    ]
                    
                    # Resumen de movimientos por producto
                    st.subheader(" Resumen de Movimientos")
                    
                    # Calcular stock te�rico sumando todos los movimientos
                    stock_summary = df_inventory.groupby('Ingrediente').agg({
                        'Cantidad': 'sum'  # Suma todos los movimientos (+ ingresos, - egresos)
                    }).reset_index()
                    stock_summary.rename(columns={'Cantidad': 'Stock Calculado'}, inplace=True)
                    
                    # No hay alertas de stock bajo ya que no tenemos stock m�nimo en esta estructura
                    low_stock = pd.DataFrame()  # DataFrame vac�o
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric(" Total Ingredientes", len(stock_summary))
                    col2.metric(" Movimientos Totales", len(df_filtered))
                    col3.metric(" Total Ingresos", df_filtered[df_filtered['Tipo'] == 'Ingreso']['Cantidad'].sum())
                    col4.metric(" Total Egresos", abs(df_filtered[df_filtered['Tipo'] == 'Egreso']['Cantidad'].sum()))
                    
                    # Mostrar resumen de stock calculado
                    st.subheader(" Stock Calculado por Producto")
                    st.dataframe(stock_summary, use_container_width=True)
                    
                    # Gr�ficos
                    st.subheader(" Movimientos de Inventario")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Movimientos por ingrediente
                        ingredient_movements = df_filtered.groupby(['Ingrediente', 'Tipo'])['Cantidad'].sum().reset_index()
                        fig = px.bar(ingredient_movements, x='Ingrediente', y='Cantidad', color='Tipo',
                                   title='Movimientos por Ingrediente')
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Stock calculado por ingrediente
                        fig = px.bar(stock_summary, x='Ingrediente', y='Stock Calculado',
                                   title='Stock Calculado por Ingrediente')
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabla detallada
                    st.subheader(" Movimientos Detallados")
                    df_filtered['Fecha'] = df_filtered['Fecha'].dt.strftime('%Y-%m-%d')
                    st.dataframe(df_filtered, use_container_width=True)
                    
                    # Exportaci�n
                    st.subheader(" Exportar Reporte")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button(" Generar PDF", key="pdf_inventory"):
                            pdf_data = create_pdf_report(
                                f"Reporte de Inventario ({fecha_desde} - {fecha_hasta})",
                                df_filtered.values.tolist(),
                                df_filtered.columns.tolist()
                            )
                            st.download_button(
                                label=" Descargar PDF",
                                data=pdf_data,
                                file_name=f"reporte_inventario_{fecha_desde}_{fecha_hasta}.pdf",
                                mime="application/pdf"
                            )
                    
                    with col2:
                        if st.button(" Generar Excel", key="excel_inventory"):
                            excel_data = export_to_excel(df_filtered)
                            st.download_button(
                                label=" Descargar Excel",
                                data=excel_data,
                                file_name=f"reporte_inventario_{fecha_desde}_{fecha_hasta}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.warning("No hay movimientos de inventario registrados.")
            else:
                st.warning("No se encontraron productos en el inventario.")
        
        # --- TAB 7: REPORTE DE USUARIOS ---
        with tab7:
            st.header("=d Reporte de Usuarios del Sistema")
            
            # Obtener usuarios
            all_users = couchdb_utils.get_documents_by_partition(db, "Usuario")
            
            if all_users:
                # Procesar datos de usuarios
                users_data = []
                for user in all_users:
                    # Fecha de creaci�n
                    created_date = "N/A"
                    if 'fecha_creacion' in user:
                        created_date = convert_to_local_time(user['fecha_creacion']).strftime('%Y-%m-%d')
                    
                    # �ltimo acceso
                    last_access = "N/A"
                    if 'ultimo_acceso' in user:
                        last_access = convert_to_local_time(user['ultimo_acceso']).strftime('%Y-%m-%d %H:%M')
                    
                    users_data.append({
                        'Usuario': user.get('usuario', ''),
                        'Nombre': user.get('nombre', ''),
                        'Email': user.get('email', ''),
                        'Rol': user.get('rol', ''),
                        'Estado': 'Activo' if user.get('activo', True) else 'Inactivo',
                        'Fecha Creaci�n': created_date,
                        '�ltimo Acceso': last_access,
                        'Permisos': len(user.get('permisos', []))
                    })
                
                df_users = pd.DataFrame(users_data)
                
                # M�tricas
                st.subheader(" Resumen de Usuarios")
                col1, col2, col3, col4 = st.columns(4)
                
                total_users = len(df_users)
                active_users = len(df_users[df_users['Estado'] == 'Activo'])
                roles_count = df_users['Rol'].nunique()
                
                col1.metric("=e Total Usuarios", total_users)
                col2.metric(" Usuarios Activos", active_users)
                col3.metric("L Usuarios Inactivos", total_users - active_users)
                col4.metric("= Roles Diferentes", roles_count)
                
                # Filtros
                col1, col2 = st.columns(2)
                with col1:
                    rol_filter = st.selectbox("Filtrar por Rol", ["Todos"] + df_users['Rol'].unique().tolist())
                
                with col2:
                    estado_filter = st.selectbox("Filtrar por Estado", ["Todos", "Activo", "Inactivo"])
                
                # Aplicar filtros
                df_filtered_users = df_users.copy()
                
                if rol_filter != "Todos":
                    df_filtered_users = df_filtered_users[df_filtered_users['Rol'] == rol_filter]
                
                if estado_filter != "Todos":
                    df_filtered_users = df_filtered_users[df_filtered_users['Estado'] == estado_filter]
                
                # Gr�ficos
                st.subheader(" Distribuci�n de Usuarios")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Distribuci�n por rol
                    role_dist = df_users['Rol'].value_counts().reset_index()
                    role_dist.columns = ['Rol', 'Cantidad']
                    fig = px.pie(role_dist, values='Cantidad', names='Rol',
                               title='Distribuci�n por Rol')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Usuarios activos vs inactivos
                    status_dist = df_users['Estado'].value_counts().reset_index()
                    status_dist.columns = ['Estado', 'Cantidad']
                    fig = px.bar(status_dist, x='Estado', y='Cantidad',
                               title='Usuarios por Estado',
                               color='Estado')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Tabla de usuarios
                st.subheader(" Lista de Usuarios")
                st.dataframe(df_filtered_users, use_container_width=True)
                
                # An�lisis de actividad reciente
                st.subheader(" An�lisis de Actividad")
                
                # Usuarios que no han accedido recientemente
                df_users_copy = df_users.copy()
                df_users_copy = df_users_copy[df_users_copy['�ltimo Acceso'] != 'N/A']
                
                if not df_users_copy.empty:
                    df_users_copy['ultimo Acceso Fecha'] = pd.to_datetime(df_users_copy['ultimo Acceso'])
                    cutoff_date = datetime.now() - timedelta(days=30)
                    inactive_users = df_users_copy[df_users_copy['ultimo Acceso Fecha'] < cutoff_date]
                    
                    if not inactive_users.empty:
                        st.warning(f"**{len(inactive_users)} usuarios no han accedido en los �ltimos 30 dias:**")
                        st.dataframe(inactive_users[['Usuario', 'Nombre', 'ultimo Acceso']], use_container_width=True)
                
                # Exportaci�n
                st.subheader(" Exportar Reporte")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(" Generar PDF", key="pdf_users"):
                        pdf_data = create_pdf_report(
                            "Reporte de Usuarios del Sistema",
                            df_filtered_users.values.tolist(),
                            df_filtered_users.columns.tolist()
                        )
                        st.download_button(
                            label=" Descargar PDF",
                            data=pdf_data,
                            file_name="reporte_usuarios.pdf",
                            mime="application/pdf"
                        )
                
                with col2:
                    if st.button(" Generar Excel", key="excel_users"):
                        excel_data = export_to_excel(df_filtered_users)
                        st.download_button(
                            label=" Descargar Excel",
                            data=excel_data,
                            file_name="reporte_usuarios.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
            else:
                st.warning("No se encontraron usuarios en el sistema.")
    
    else:
        st.error("No se pudo conectar a la base de datos")

else:
    st.warning("Por favor, inicie sesi�n para acceder a los reportes")