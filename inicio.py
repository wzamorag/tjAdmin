# pages/inicio.py
import streamlit as st
import couchdb_utils
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
import plotly.express as px
import io
import base64
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage # To embed images in Excel
import pytz

# --- Configuración Inicial ---
st.set_page_config(layout="wide", page_title="Dashboard de Restaurante", page_icon="assets/LOGO.png")
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
couchdb_utils.generarLogin(archivo_actual_relativo)

# --- Funciones de Zona Horaria ---
def get_timezone():
    """Retorna la zona horaria de El Salvador"""
    return pytz.timezone('America/El_Salvador')

def convert_to_local_time(utc_datetime_str):
    """Convierte una fecha UTC a hora local de El Salvador"""
    if not utc_datetime_str:
        return None
    try:
        # Manejar diferentes formatos de fecha
        if isinstance(utc_datetime_str, str):
            if 'T' in utc_datetime_str:
                # Formato ISO con T
                if utc_datetime_str.endswith('Z'):
                    utc_datetime_str = utc_datetime_str.replace('Z', '+00:00')
                utc_dt = datetime.fromisoformat(utc_datetime_str)
            else:
                # Otro formato
                utc_dt = datetime.fromisoformat(utc_datetime_str)
        else:
            utc_dt = utc_datetime_str
        
        # Asegurar que la fecha esté en UTC
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        elif utc_dt.tzinfo != timezone.utc:
            utc_dt = utc_dt.astimezone(timezone.utc)
        
        # Convertir a hora local
        local_tz = get_timezone()
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt
    except Exception as e:
        return None

# --- Funciones de Procesamiento de Datos ---

def get_data_for_period(data_list, date_field, start_date, end_date):
    """Filtra una lista de documentos por un rango de fechas."""
    filtered_data = []
    for doc in data_list:
        date_str = doc.get(date_field)
        if date_str:
            try:
                doc_date = datetime.fromisoformat(date_str).date() 
                if start_date <= doc_date <= end_date:
                    filtered_data.append(doc)
            except ValueError:
                # Handle cases where date format might be off
                continue
    return filtered_data

def calculate_sales_stats(orders):
    """Calcula estadísticas de ventas."""
    total_sales = sum(order.get('total', 0) for order in orders)
    num_orders = len(orders)
    total_items_sold = sum(sum(item.get('cantidad', 0) for item in order.get('items', [])) for order in orders)
    
    # Data for chart
    sales_data = []
    for order in orders:
        date_str = order.get('fecha_pago', order.get('fecha_creacion'))
        if date_str:
            try:
                sales_data.append({
                    'Fecha': datetime.fromisoformat(date_str).date(),
                    'Total Venta': order.get('total', 0)
                })
            except ValueError:
                continue
    df = pd.DataFrame(sales_data)
    if not df.empty:
        df = df.groupby('Fecha')['Total Venta'].sum().reset_index()
    
    return {
        "Total Ventas": f"${total_sales:.2f}",
        "Número de Órdenes": num_orders,
        "Total Ítems Vendidos": total_items_sold,
        "chart_data": df
    }

def calculate_purchase_stats(purchases):
    """Calcula estadísticas de compras."""
    total_purchases = sum(purchase.get('total_compra', 0) for purchase in purchases)
    num_purchases = len(purchases)

    # Data for chart
    purchase_data = []
    for purchase in purchases:
        date_str = purchase.get('fecha_compra') # Assuming 'fecha_compra' field
        if date_str:
            try:
                purchase_data.append({
                    'Fecha': datetime.fromisoformat(date_str).date(),
                    'Total Compra': purchase.get('total_compra', 0)
                })
            except ValueError:
                continue
    df = pd.DataFrame(purchase_data)
    if not df.empty:
        df = df.groupby('Fecha')['Total Compra'].sum().reset_index()

    return {
        "Total Compras": f"${total_purchases:.2f}",
        "Número de Compras": num_purchases,
        "chart_data": df
    }

def calculate_inventory_stats(inventory_records):
    """Calcula estadísticas de inventario (ejemplo: valor total de entradas/salidas)."""
    total_value_in = sum(rec.get('valor_entrada', 0) for rec in inventory_records if rec.get('tipo') == 'entrada')
    total_value_out = sum(rec.get('valor_salida', 0) for rec in inventory_records if rec.get('tipo') == 'salida')
    num_movements = len(inventory_records)

    # Data for chart
    inventory_data = []
    for rec in inventory_records:
        date_str = rec.get('fecha') # Assuming 'fecha' field for inventory movements
        if date_str:
            try:
                inventory_data.append({
                    'Fecha': datetime.fromisoformat(date_str).date(),
                    'Valor Movimiento': rec.get('valor_entrada', 0) - rec.get('valor_salida', 0) # Net change
                })
            except ValueError:
                continue
    df = pd.DataFrame(inventory_data)
    if not df.empty:
        df = df.groupby('Fecha')['Valor Movimiento'].sum().reset_index()

    return {
        "Valor Total Entradas": f"${total_value_in:.2f}",
        "Valor Total Salidas": f"${total_value_out:.2f}",
        "Número de Movimientos": num_movements,
        "chart_data": df
    }

# --- Generación de Reportes ---

def generate_excel_report(data_frames, sheet_names, title="Reporte de Estadísticas"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for df, sheet_name in zip(data_frames, sheet_names):
            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                # Create an empty sheet if DataFrame is empty
                writer.book.create_sheet(sheet_name)
                writer.sheets[sheet_name].append([f"No hay datos para {sheet_name}."])
    output.seek(0)
    return output.getvalue()

# --- Lógica Principal de la Pantalla ---
if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # Verificar rol del usuario y redirigir directamente a su página específica
        user_data = st.session_state.get('user_data', {})
        user_role = user_data.get('id_rol', 0)
        
        # Roles: 1-Admin, 2-Caja, 3-Mesero, 4-Bar, 5-Cocina, 6-Operativo
        if user_role == 2:  # Caja
            st.switch_page("pages/cobros.py")
        elif user_role == 3:  # Mesero
            st.switch_page("pages/restaurant_main.py")
        elif user_role == 4:  # Bar
            st.switch_page("pages/bar.py")
        elif user_role == 5:  # Cocina
            st.switch_page("pages/cocina.py")
        elif user_role not in [1, 6]:  # Si no es admin ni operativo
            st.error("❌ Tu rol no tiene una página asignada.")
            st.info("💡 Contacta al administrador para más información.")
            st.stop()
        
        # Solo continuar si es administrador (rol 1) u operativo (rol 6)
        st.title("📈 Dashboard de Gestión")
        
        # Verificar alertas de stock bajo con configuración personalizada
        alertas_stock = couchdb_utils.verificar_alertas_stock_bajo(db)
        if alertas_stock:
            st.markdown("### 🚨 Alertas de Inventario (Configurables)")
            
            # Separar por tipo de alerta
            alertas_criticas = [a for a in alertas_stock if a['tipo'] == 'critico']
            alertas_advertencia = [a for a in alertas_stock if a['tipo'] == 'advertencia']
            alertas_error = [a for a in alertas_stock if a['tipo'] == 'error']
            
            # Mostrar estadísticas rápidas
            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
            with col_stats1:
                st.metric("🚨 Críticas", len(alertas_criticas))
            with col_stats2:
                st.metric("⚠️ Advertencias", len(alertas_advertencia))
            with col_stats3:
                st.metric("📦 Total Alertas", len(alertas_stock))
            with col_stats4:
                if st.button("⚙️ Configurar Alertas", help="Ir a configuración de alertas"):
                    st.switch_page("pages/configuracion.py")
            
            # Mostrar alertas en columnas
            if alertas_criticas or alertas_advertencia:
                col1, col2 = st.columns(2)
                
                if alertas_criticas:
                    with col1:
                        st.markdown("**🚨 Críticas (Stock muy bajo o agotado):**")
                        for alerta in alertas_criticas:
                            with st.expander(f"🚨 {alerta['mensaje'][:50]}...", expanded=False):
                                st.error(alerta['mensaje'])
                                st.caption(f"Stock actual: {alerta['cantidad']:.1f} | Límite configurado: {alerta.get('limite_configurado', 'N/A')}")
                                
                if alertas_advertencia:
                    with col2:
                        st.markdown("**⚠️ Advertencias (Stock bajo):**")
                        for alerta in alertas_advertencia:
                            with st.expander(f"⚠️ {alerta['mensaje'][:50]}...", expanded=False):
                                st.warning(alerta['mensaje'])
                                st.caption(f"Stock actual: {alerta['cantidad']:.1f} | Límite configurado: {alerta.get('limite_configurado', 'N/A')}")
            
            # Mostrar errores si existen
            if alertas_error:
                st.markdown("**❌ Errores del Sistema:**")
                for alerta in alertas_error:
                    st.error(alerta['mensaje'])
        else:
            # Mostrar mensaje positivo cuando no hay alertas
            st.success("✅ Todos los productos tienen stock suficiente según los límites configurados")
        
        st.markdown("---")

        # --- Selección de Período ---
        period_options = {
            "Diario": "daily",
            "Semanal": "weekly",
            "Mensual": "monthly",
            "Semestral": "semi-annual",
            "Anual": "annual",
            "Personalizado": "custom"
        }
        selected_period_name = st.selectbox("Seleccionar Período:", list(period_options.keys()))
        selected_period_type = period_options[selected_period_name]

        # Always allow selecting the start date
        today = datetime.now(timezone.utc).date()
        
        # Set default value for start_date based on selected_period_type
        default_start_date = today
        if selected_period_type == "weekly":
            default_start_date = today - timedelta(days=today.weekday()) # Monday of current week
        elif selected_period_type == "monthly":
            default_start_date = today.replace(day=1)
        elif selected_period_type == "semi-annual":
            default_start_date = today.replace(month=1, day=1) if today.month <= 6 else today.replace(month=7, day=1)
        elif selected_period_type == "annual":
            default_start_date = today.replace(month=1, day=1)

        start_date = st.date_input("Fecha de Inicio:", value=default_start_date)

        end_date = today # Default for custom if not overridden

        if selected_period_type == "daily":
            end_date = start_date
        elif selected_period_type == "weekly":
            end_date = start_date + timedelta(days=6)
        elif selected_period_type == "monthly":
            # Calculate last day of the month for the selected start_date
            next_month = start_date.replace(day=28) + timedelta(days=4) # Go to 28th, add 4 days to ensure we are in next month
            end_date = next_month.replace(day=1) - timedelta(days=1) # Go to 1st of next month, subtract 1 day
        elif selected_period_type == "semi-annual":
            if start_date.month <= 6:
                end_date = start_date.replace(month=6, day=30)
            else:
                end_date = start_date.replace(month=12, day=31)
        elif selected_period_type == "annual":
            end_date = start_date.replace(month=12, day=31)
        elif selected_period_type == "custom":
            # For custom, allow user to pick end date as well
            end_date = st.date_input("Fecha de Fin:", value=today)
        
        # Ensure end_date is not before start_date if user manually changes it
        if end_date < start_date:
            st.warning("La fecha de fin no puede ser anterior a la fecha de inicio. Ajustando fecha de fin.")
            end_date = start_date # Or handle as desired

        st.info(f"Mostrando datos desde **{start_date.strftime('%d/%m/%Y')}** hasta **{end_date.strftime('%d/%m/%Y')}**")
        st.markdown("---")

        # --- Cargar todos los datos ---
        all_paid_orders = couchdb_utils.get_all_paid_orders(db)
        all_purchases = couchdb_utils.get_all_purchases(db)
        all_inventory_records = couchdb_utils.get_all_inventory_records(db)

        # --- Filtrar datos por el período seleccionado ---
        filtered_sales = get_data_for_period(all_paid_orders, 'fecha_creacion', start_date, end_date)
        filtered_purchases = get_data_for_period(all_purchases, 'fecha_compra', start_date, end_date)
        filtered_inventory = get_data_for_period(all_inventory_records, 'fecha', start_date, end_date)

        # --- Calcular Estadísticas ---
        sales_stats = calculate_sales_stats(filtered_sales)
        purchase_stats = calculate_purchase_stats(filtered_purchases)
        inventory_stats = calculate_inventory_stats(filtered_inventory)

        # --- Pestañas para Estadísticas Detalladas ---
        tab_sales, tab_purchases, tab_inventory, tab_sales_detail, tab_purchases_detail = st.tabs(["Ventas", "Compras", "Inventario", "Detalle de Ventas", "Detalle de Compras"])

        with tab_sales:
            st.subheader("Ventas")
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1: st.metric("Total Ventas", sales_stats["Total Ventas"])
            with col_s2: st.metric("Número de Órdenes", sales_stats["Número de Órdenes"])
            with col_s3: st.metric("Total Ítems Vendidos", sales_stats["Total Ítems Vendidos"])

            if not sales_stats["chart_data"].empty:
                fig_sales = px.line(sales_stats["chart_data"], x='Fecha', y='Total Venta', 
                                    title='Tendencia de Ventas', markers=True)
                st.plotly_chart(fig_sales, use_container_width=True)
            else:
                st.info("No hay datos de ventas para el período seleccionado.")

        with tab_purchases:
            st.subheader("Compras")
            col_p1, col_p2 = st.columns(2)
            with col_p1: st.metric("Total Compras", purchase_stats["Total Compras"])
            with col_p2: st.metric("Número de Compras", purchase_stats["Número de Compras"])
            
            if not purchase_stats["chart_data"].empty:
                fig_purchases = px.line(purchase_stats["chart_data"], x='Fecha', y='Total Compra', 
                                        title='Tendencia de Compras', markers=True, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_purchases, use_container_width=True)
            else:
                st.info("No hay datos de compras para el período seleccionado.")

        with tab_inventory:
            st.subheader("Inventario")
            col_i1, col_i2, col_i3 = st.columns(3)
            with col_i1: st.metric("Valor Total Entradas", inventory_stats["Valor Total Entradas"])
            with col_i2: st.metric("Valor Total Salidas", inventory_stats["Valor Total Salidas"])
            with col_i3: st.metric("Número de Movimientos", inventory_stats["Número de Movimientos"])

            if not inventory_stats["chart_data"].empty:
                fig_inventory = px.line(inventory_stats["chart_data"], x='Fecha', y='Valor Movimiento', 
                                        title='Movimiento Neto de Inventario', markers=True, color_discrete_sequence=px.colors.qualitative.Dark2)
                st.plotly_chart(fig_inventory, use_container_width=True)
            else:
                st.info("No hay datos de inventario para el período seleccionado.")

        with tab_sales_detail:
            st.subheader("Detalle de Órdenes Pagadas")
            if not filtered_sales:
                st.info("No hay órdenes pagadas para el período seleccionado.")
            else:
                # Sort sales by order number for better grouping
                sorted_sales = sorted(filtered_sales, key=lambda x: x.get('numero_orden', 0))

                for order in sorted_sales:
                    order_number = order.get('numero_orden', 'N/A')
                    order_total = order.get('total', 0)
                    payment_date_str = order.get('fecha_pago', order.get('fecha_creacion'))
                    local_date = convert_to_local_time(payment_date_str)
                    payment_date = local_date.strftime('%d/%m/%Y %H:%M:%S') if local_date else 'N/A'
                    
                    # Create an expander for each order
                    with st.expander(f"Orden #{order_number} - Total: ${order_total:.2f} (Fecha: {payment_date})", expanded=False):
                        st.markdown(f"**Número de Orden:** {order_number}")
                        st.markdown(f"**Fecha de Pago:** {payment_date}")
                        st.markdown(f"**Total de la Orden:** ${order_total:.2f}")
                        if order.get('comentarios'):
                            st.markdown(f"**Comentarios de la Orden:** {order['comentarios']}")
                        
                        st.markdown("---")
                        st.markdown("**Artículos Vendidos:**")

                        if order.get('items'):
                            # Prepare items for a DataFrame
                            items_data = []
                            for item in order['items']:
                                items_data.append({
                                    'Artículo': item.get('nombre', 'N/A'),
                                    'Cantidad': item.get('cantidad', 0),
                                    'Precio Unitario': f"${item.get('precio_unitario', 0):.2f}",
                                    'Subtotal': f"${item.get('cantidad', 0) * item.get('precio_unitario', 0):.2f}",
                                    'Comentarios': item.get('comentarios', '')
                                })
                            
                            df_items = pd.DataFrame(items_data)
                            st.dataframe(df_items, use_container_width=True, hide_index=True)
                        else:
                            st.info("Esta orden no tiene artículos registrados.")
                    st.markdown("---") # Separator between orders

        with tab_purchases_detail:
            st.subheader("Detalle de Compras")
            if not filtered_purchases:
                st.info("No hay compras para el período seleccionado.")
            else:
                # Sort purchases by purchase number (assuming a 'numero_compra' field)
                # If 'numero_compra' doesn't exist, use another unique identifier like '_id'
                sorted_purchases = sorted(filtered_purchases, key=lambda x: x.get('numero_compra', x.get('_id', 'N/A')))

                for purchase in sorted_purchases:
                    purchase_number = purchase.get('numero_compra', 'N/A')
                    purchase_total = purchase.get('total_compra', 0)
                    purchase_date_str = purchase.get('fecha_compra')
                    
                    purchase_date = 'N/A'
                    if purchase_date_str:
                        try:
                            local_date = convert_to_local_time(purchase_date_str)
                            purchase_date = local_date.strftime('%d/%m/%Y %H:%M:%S') if local_date else 'N/A'
                        except ValueError:
                            st.warning(f"Formato de fecha inválido para la compra {purchase_number}: {purchase_date_str}")
                            purchase_date = "Fecha inválida"
                    
                    # Create an expander for each purchase
                    with st.expander(f"Compra #{purchase_number} - Total: ${purchase_total:.2f} (Fecha: {purchase_date})", expanded=False):
                        st.markdown(f"**Número de Compra:** {purchase_number}")
                        st.markdown(f"**Fecha de Compra:** {purchase_date}")
                        st.markdown(f"**Total de la Compra:** ${purchase_total:.2f}")
                        if purchase.get('proveedor'):
                            st.markdown(f"**Proveedor:** {purchase['proveedor']}")
                        if purchase.get('comentarios'): # Assuming purchases can have general comments
                            st.markdown(f"**Comentarios de la Compra:** {purchase['comentarios']}")
                        
                        st.markdown("---")
                        st.markdown("**Artículos Comprados:**")

                        if purchase.get('items_comprados'): # Assuming items are in 'items_comprados'
                            # Prepare items for a DataFrame
                            items_data = []
                            for item in purchase['items_comprados']:
                                items_data.append({
                                    'Artículo': item.get('producto', 'N/A'), # Assuming 'producto' field
                                    'Cantidad': item.get('cantidad', 0),
                                    'Costo Unitario': f"${item.get('costo_unitario', 0):.2f}",
                                    'Subtotal': f"${item.get('cantidad', 0) * item.get('costo_unitario', 0):.2f}",
                                    'Notas': item.get('notas', '') # Assuming item-specific notes
                                })
                            
                            df_items = pd.DataFrame(items_data)
                            st.dataframe(df_items, use_container_width=True, hide_index=True)
                        else:
                            st.info("Esta compra no tiene artículos registrados.")
                    st.markdown("---") # Separator between purchases


        st.markdown("---")
        st.subheader("Generar Reportes")

        col_report_pdf, col_report_excel = st.columns(2)

        with col_report_pdf:
            if st.button("📄 Generar Reporte PDF", use_container_width=True, type="primary"):
                # Capturar gráficos como imágenes para el PDF
                sales_chart_bytes = None
                if not sales_stats["chart_data"].empty:
                    fig_sales = px.line(sales_stats["chart_data"], x='Fecha', y='Total Venta', title='Tendencia de Ventas', markers=True)
                    sales_chart_bytes = fig_sales.to_image(format="png")

                # Combine all stats into a dictionary for the PDF report
                all_stats_for_pdf = {
                    "Ventas": sales_stats["Total Ventas"],
                    "Órdenes Vendidas": sales_stats["Número de Órdenes"],
                    "Ítems Vendidos": sales_stats["Total Ítems Vendidos"],
                    "Compras": purchase_stats["Total Compras"],
                    "Número de Compras": purchase_stats["Número de Compras"],
                    "Entradas Inventario": inventory_stats["Valor Total Entradas"],
                    "Salidas Inventario": inventory_stats["Valor Total Salidas"],
                    "Movimientos Inventario": inventory_stats["Número de Movimientos"],
                }

                pdf_data = couchdb_utils.generar_dashboard_pdf_report(
                    f"Reporte de Dashboard ({selected_period_name})",
                    all_stats_for_pdf,
                    start_date.strftime('%d/%m/%Y'),
                    end_date.strftime('%d/%m/%Y'),
                    chart_image_bytes=sales_chart_bytes # Only including sales chart for simplicity in PDF
                )
                st.download_button(
                    label="Descargar PDF",
                    data=pdf_data,
                    file_name=f"Reporte_Dashboard_{selected_period_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                st.success("Reporte PDF generado con éxito.")

        with col_report_excel:
            if st.button("📊 Generar Reporte Excel", use_container_width=True, type="secondary"):
                excel_data_frames = [
                    sales_stats["chart_data"].rename(columns={'Total Venta': 'Venta'}),
                    purchase_stats["chart_data"].rename(columns={'Total Compra': 'Compra'}),
                    inventory_stats["chart_data"].rename(columns={'Valor Movimiento': 'Movimiento'})
                ]
                sheet_names = ["Ventas", "Compras", "Inventario"]

                excel_bytes = generate_excel_report(excel_data_frames, sheet_names)
                
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name=f"Reporte_Dashboard_{selected_period_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.success("Reporte Excel generado con éxito.")

    else:
        st.error("No se pudo conectar a la base de datos.")
else:
    st.info("Por favor, inicia sesión para acceder a esta página.")
