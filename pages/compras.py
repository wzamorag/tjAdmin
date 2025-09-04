# pages/compras.py
import streamlit as st
from datetime import datetime, timezone
import couchdb_utils
import os
import uuid
import pandas as pd
import base64
from fpdf import FPDF
import pytz

# Obtener la ruta relativa de la página
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = "compras"

# --- Funciones de Zona Horaria ---
def get_timezone():
    """Retorna la zona horaria de El Salvador"""
    return pytz.timezone('America/El_Salvador')

def convert_to_local_time(utc_datetime_str):
    """Convierte una fecha UTC a hora local de El Salvador"""
    if not utc_datetime_str:
        return None
    try:
        if isinstance(utc_datetime_str, str):
            if utc_datetime_str.endswith('Z'):
                utc_datetime_str = utc_datetime_str.replace('Z', '+00:00')
            utc_dt = datetime.fromisoformat(utc_datetime_str)
        else:
            utc_dt = utc_datetime_str
        
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)
        elif utc_dt.tzinfo != timezone.utc:
            utc_dt = utc_dt.astimezone(timezone.utc)
        
        local_tz = get_timezone()
        local_dt = utc_dt.astimezone(local_tz)
        return local_dt
    except Exception:
        return None

# Llama a la función de login/menú/validación
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Registro de Compras", page_icon="../assets/LOGO.png")

# --- CSS EXTERNO ---
css_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'style.css')
if os.path.exists(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning(f"Archivo CSS no encontrado en: {css_file_path}")

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()

    if db:
        # Obtener lista de proveedores activos
        def get_proveedores_activos():
            proveedores = couchdb_utils.get_documents_by_partition(db, "proveedores")
            return [p for p in proveedores if p.get('activo', 0) == 1]

        # Opciones para la unidad de medida
        UNIDAD_OPTIONS = ["unidad", "botella", "litro", "medio litro"]

        # Función para generar PDF de factura de compra
        def generar_factura_compra_pdf(compra_data):
            # Crear instancia de FPDF
            pdf = FPDF()
            pdf.add_page()
            
            # Logo
            try:
                logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'LOGO.png')
                if os.path.exists(logo_path):
                    # Logo en la esquina superior izquierda
                    pdf.image(logo_path, 10, 8, 33)
                    pdf.set_y(35)  # Espacio después del logo
            except:
                pass
            
            pdf.set_font('Arial', 'B', 16)
            # Header del negocio
            pdf.cell(0, 10, 'Restaurante Tia Juana', 0, 1, 'C')
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 6, 'GIRO: Restaurantes', 0, 1, 'C')
            pdf.cell(0, 6, 'Sec: Venta de Vehiculos Automotores', 0, 1, 'C')
            pdf.cell(0, 6, 'Direccion del Restaurante', 0, 1, 'C')
            pdf.ln(5)
            
            # Tipo de factura
            es_sujeto_excluido = compra_data.get('sujeto_excluido', False)
            if es_sujeto_excluido:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 8, 'FACTURA DE SUJETO EXCLUIDO', 1, 1, 'C')
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(50, 8, f'No. {compra_data.get("numero_documento", "N/A")}', 1, 0, 'C')
            else:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 8, 'FACTURA DE COMPRA', 1, 1, 'C')
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(50, 8, f'No. {compra_data.get("numero_documento", "N/A")}', 1, 0, 'C')
            
            # Fecha
            fecha_compra = datetime.strptime(compra_data.get('fecha_compra'), '%Y-%m-%d') if compra_data.get('fecha_compra') else datetime.now()
            pdf.cell(30, 8, 'DIA', 1, 0, 'C')
            pdf.cell(30, 8, 'MES', 1, 0, 'C')
            pdf.cell(30, 8, 'ANO', 1, 1, 'C')
            pdf.cell(50, 8, '', 0, 0)
            pdf.cell(30, 8, f'{fecha_compra.day:02d}', 1, 0, 'C')
            pdf.cell(30, 8, f'{fecha_compra.month:02d}', 1, 0, 'C')
            pdf.cell(30, 8, f'{fecha_compra.year}', 1, 1, 'C')
            pdf.ln(5)
            
            # Datos del proveedor
            if es_sujeto_excluido:
                pdf.set_font('Arial', '', 10)
                pdf.cell(40, 8, 'Nombre de Sujeto Excluido:', 0, 0)
                pdf.cell(0, 8, compra_data.get('proveedor_nombre', ''), 'B', 1)
                pdf.ln(2)
                pdf.cell(20, 8, 'Direccion:', 0, 0)
                pdf.cell(0, 8, '', 'B', 1)
                pdf.ln(2)
                pdf.cell(40, 8, 'NIT o DUI de Sujeto Excluido:', 0, 0)
                pdf.cell(60, 8, '', 'B', 0)
                pdf.cell(20, 8, 'Telefono:', 0, 0)
                pdf.cell(0, 8, '', 'B', 1)
            else:
                pdf.set_font('Arial', '', 10)
                pdf.cell(30, 8, 'Proveedor:', 0, 0)
                pdf.cell(0, 8, compra_data.get('proveedor_nombre', ''), 'B', 1)
                pdf.ln(2)
                pdf.cell(20, 8, 'Direccion:', 0, 0)
                pdf.cell(0, 8, '', 'B', 1)
                pdf.ln(2)
                pdf.cell(25, 8, 'NIT/DUI:', 0, 0)
                pdf.cell(60, 8, '', 'B', 0)
                pdf.cell(20, 8, 'Telefono:', 0, 0)
                pdf.cell(0, 8, '', 'B', 1)
            
            pdf.ln(10)
            
            # Tabla de productos
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(20, 8, 'CANT.', 1, 0, 'C')
            pdf.cell(80, 8, 'DESCRIPCION', 1, 0, 'C')
            pdf.cell(35, 8, 'PRECIO UNITARIO', 1, 0, 'C')
            pdf.cell(35, 8, 'TOTAL COMPRAS', 1, 1, 'C')
            
            # Items de la compra
            pdf.set_font('Arial', '', 9)
            total_items = 0
            for item in compra_data.get('items', []):
                cantidad = item.get('Cantidad', 0)
                descripcion = item.get('Descripción', '')[:35]  # Truncar si es muy largo
                precio_unit = item.get('Precio Unitario', 0)
                total_item = item.get('Total', 0)
                
                pdf.cell(20, 8, f"{cantidad}", 1, 0, 'C')
                pdf.cell(80, 8, descripcion, 1, 0, 'L')
                pdf.cell(35, 8, f"${precio_unit:.2f}", 1, 0, 'R')
                pdf.cell(35, 8, f"${total_item:.2f}", 1, 1, 'R')
                total_items += total_item
            
            # Espacios vacios para completar la tabla
            for _ in range(10 - len(compra_data.get('items', []))):
                pdf.cell(20, 8, '', 1, 0, 'C')
                pdf.cell(80, 8, '', 1, 0, 'L')
                pdf.cell(35, 8, '', 1, 0, 'R')
                pdf.cell(35, 8, '', 1, 1, 'R')
            
            # Totales
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 10)
            subtotal = compra_data.get('subtotal', 0)
            iva = compra_data.get('iva', 0)
            total = compra_data.get('total', 0)
            
            pdf.cell(135, 8, 'Sumas $', 1, 0, 'R')
            pdf.cell(35, 8, f"{subtotal:.2f}", 1, 1, 'R')
            
            # Solo mostrar IVA si no es sujeto excluido y hay IVA
            if not es_sujeto_excluido and iva > 0:
                pdf.cell(135, 8, 'IVA (13%)', 1, 0, 'R')
                pdf.cell(35, 8, f"{iva:.2f}", 1, 1, 'R')
            
            # Para sujetos excluidos, no mostrar renta retenida
            if not es_sujeto_excluido:
                pdf.cell(135, 8, '(-) Renta Retenido', 1, 0, 'R')
                pdf.cell(35, 8, '0.00', 1, 1, 'R')
            
            pdf.cell(135, 8, 'Venta Total $', 1, 0, 'R')
            pdf.cell(35, 8, f"{total:.2f}", 1, 1, 'R')
            
            # Firma
            pdf.ln(10)
            pdf.cell(85, 15, '', 1, 0)
            pdf.cell(85, 15, '', 1, 1)
            pdf.cell(85, 8, 'FIRMA & Huella', 0, 1, 'C')
            
            # Información adicional al pie
            pdf.ln(5)
            pdf.set_font('Arial', '', 8)
            pdf.cell(0, 4, f'Fecha de Registro: {compra_data.get("fecha_registro", "")}', 0, 1, 'L')
            
            # Generar el PDF como bytes
            pdf_content = pdf.output(dest='S')
            
            # Convertir a bytes si no lo está ya
            if isinstance(pdf_content, str):
                return pdf_content.encode('latin-1')
            elif isinstance(pdf_content, bytearray):
                return bytes(pdf_content)
            else:
                return pdf_content

        # Función para actualizar ingredientes y registrar movimientos de inventario
        def actualizar_ingredientes(items_compra, usuario, num_documento):
            ingredientes = couchdb_utils.get_documents_by_partition(db, "ingredientes")
            
            for item in items_compra:
                descripcion = item['Descripción']
                cantidad = item['Cantidad']
                unidad = item.get('Unidad', 'unidad')  # Usar 'unidad' como valor por defecto
                
                # Buscar si el ingrediente ya existe
                ingrediente_existente = next((i for i in ingredientes if i.get('descripcion', '').lower() == descripcion.lower()), None)
                
                if ingrediente_existente:
                    # Verificar si la unidad es diferente
                    if ingrediente_existente.get('unidad') != unidad:
                        st.warning(f"La unidad del ingrediente '{descripcion}' ha cambiado de '{ingrediente_existente.get('unidad')}' a '{unidad}'")
                    
                    # Actualizar cantidad existente y unidad
                    cantidad_actual = float(ingrediente_existente.get('cantidad', 0))
                    nueva_cantidad = cantidad_actual + cantidad
                    
                    ingrediente_actualizado = {
                        "_id": ingrediente_existente["_id"],
                        "_rev": ingrediente_existente["_rev"],
                        "descripcion": ingrediente_existente["descripcion"],
                        "cantidad": nueva_cantidad,
                        "unidad": unidad,  # Actualizar la unidad
                        "imagen": ingrediente_existente.get("imagen", ""),
                        "activo": ingrediente_existente.get("activo", 1),
                        "fecha_creacion": ingrediente_existente.get("fecha_creacion"),
                        "type": "ingredientes"
                    }
                    
                    try:
                        db.save(ingrediente_actualizado)
                        
                        # Registrar movimiento de inventario (entrada)
                        movimiento = {
                            "_id": f"inventario:{str(uuid.uuid4())}",
                            "type": "inventario",
                            "ingrediente_id": ingrediente_existente["_id"],
                            "tipo": "entrada",
                            "cantidad": cantidad,  # Cantidad positiva para entradas
                            "motivo": f"Compra - Documento: {num_documento}",
                            "usuario": usuario,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat()
                        }
                        db.save(movimiento)
                        
                    except Exception as e:
                        st.error(f"Error al actualizar ingrediente {descripcion}: {str(e)}")
                else:
                    # Crear nuevo ingrediente con la unidad especificada
                    doc_id = f"ingredientes:{str(uuid.uuid4())}"
                    
                    nuevo_ingrediente = {
                        "_id": doc_id,
                        "descripcion": descripcion,
                        "cantidad": cantidad,
                        "unidad": unidad,  # Usar la unidad especificada en la compra
                        "imagen": "",
                        "activo": 1,
                        "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                        "type": "ingredientes"
                    }
                    
                    try:
                        db.save(nuevo_ingrediente)
                        
                        # Registrar movimiento de inventario (entrada) para nuevo ingrediente
                        movimiento = {
                            "_id": f"inventario:{str(uuid.uuid4())}",
                            "type": "inventario",
                            "ingrediente_id": doc_id,
                            "tipo": "entrada",
                            "cantidad": cantidad,  # Cantidad positiva para entradas
                            "motivo": f"Compra - Documento: {num_documento}",
                            "usuario": usuario,
                            "fecha_creacion": datetime.now(timezone.utc).isoformat()
                        }
                        db.save(movimiento)
                        
                    except Exception as e:
                        st.error(f"Error al crear nuevo ingrediente {descripcion}: {str(e)}")

        # Inicializar tabla de items si no existe
        if 'items_compra' not in st.session_state:
            st.session_state.items_compra = pd.DataFrame(columns=['Cantidad', 'Descripción', 'Unidad', 'Precio Unitario', 'Total'])

        # --- Sección de Registro de Compra ---
        st.header("Registro de Nueva Compra")
        
        with st.form("nueva_compra_form"):
            # Selección de proveedor
            proveedores = get_proveedores_activos()
            proveedor_options = {p['_id']: p['nombre'] for p in proveedores}
            selected_proveedor_id = st.selectbox(
                "Proveedor:",
                options=list(proveedor_options.keys()),
                format_func=lambda x: proveedor_options[x],
                key="select_proveedor"
            )
            
            # Fecha y número de documento
            col1, col2 = st.columns(2)
            with col1:
                fecha_compra = st.date_input("Fecha de Compra:", key="fecha_compra")
            with col2:
                num_documento = st.text_input("Número de Documento/Factura:", key="num_documento").strip()
            
            # Checkbox para sujeto excluido
            sujeto_excluido = st.checkbox("Sujeto Excluido (No contribuyente)", key="sujeto_excluido", help="Marcar si el proveedor no es contribuyente de impuestos")
            
            # Tabla dinámica de items
            st.subheader("Detalle de la Compra")
            
            # Inicializar contador si no existe (debe estar antes de usar las keys)
            if 'form_reset_counter' not in st.session_state:
                st.session_state.form_reset_counter = 0
            
            # Crear columnas para los inputs
            col_cant, col_desc, col_unidad, col_precio, col_action = st.columns([1, 2, 1, 1, 1])
            
            with col_cant:
                nueva_cantidad = st.number_input("Cantidad", min_value=0.5, step=0.5, format="%.1f", key=f"nueva_cantidad_{st.session_state.form_reset_counter}")
            with col_desc:
                # Obtener ingredientes disponibles
                ingredientes = couchdb_utils.get_documents_by_partition(db, "ingredientes")
                ingredientes_activos = [i for i in ingredientes if i.get('activo', 0) == 1]
                opciones_ingredientes = ["-- Escribir nuevo ingrediente --"] + [ing.get('descripcion', '') for ing in ingredientes_activos]
                
                # Selectbox con opción de nuevo ingrediente (con key única)
                seleccion_ingrediente = st.selectbox(
                    "Ingrediente/Descripción",
                    options=opciones_ingredientes,
                    key=f"seleccion_ingrediente_{st.session_state.form_reset_counter}"
                )
                
                # Si selecciona escribir nuevo, mostrar campo de texto
                if seleccion_ingrediente == "-- Escribir nuevo ingrediente --":
                    nueva_descripcion = st.text_input("Escribir nuevo ingrediente:", key=f"nueva_descripcion_manual_{st.session_state.form_reset_counter}")
                else:
                    nueva_descripcion = seleccion_ingrediente
            with col_unidad:
                # Auto-seleccionar unidad si se eligió un ingrediente existente
                unidad_default = "unidad"
                if seleccion_ingrediente != "-- Escribir nuevo ingrediente --":
                    ingrediente_seleccionado = next((ing for ing in ingredientes_activos if ing.get('descripcion') == seleccion_ingrediente), None)
                    if ingrediente_seleccionado:
                        unidad_existente = ingrediente_seleccionado.get('unidad', 'unidad')
                        if unidad_existente in UNIDAD_OPTIONS:
                            unidad_default = unidad_existente
                
                nueva_unidad = st.selectbox(
                    "Unidad", 
                    options=UNIDAD_OPTIONS, 
                    index=UNIDAD_OPTIONS.index(unidad_default) if unidad_default in UNIDAD_OPTIONS else 0,
                    key=f"nueva_unidad_{st.session_state.form_reset_counter}"
                )
            with col_precio:
                nuevo_precio = st.number_input("Precio Unitario", min_value=0.1, step=0.1, format="%.2f", key=f"nuevo_precio_{st.session_state.form_reset_counter}")
            with col_action:
                st.markdown("<br>", unsafe_allow_html=True)
                agregar_item = st.form_submit_button("➕ Agregar")
            
            if agregar_item and nueva_descripcion and nueva_descripcion.strip():
                nuevo_item = {
                    'Cantidad': nueva_cantidad,
                    'Descripción': nueva_descripcion,
                    'Unidad': nueva_unidad,
                    'Precio Unitario': nuevo_precio,
                    'Total': round(nueva_cantidad * nuevo_precio, 2)
                }
                st.session_state.items_compra = pd.concat([
                    st.session_state.items_compra, 
                    pd.DataFrame([nuevo_item])
                ], ignore_index=True)
                # Incrementar contador para resetear formulario
                st.session_state.form_reset_counter += 1
                st.rerun()
            
            # Mostrar tabla de items
            if not st.session_state.items_compra.empty:
                st.dataframe(
                    st.session_state.items_compra,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Calcular totales
                total_items = len(st.session_state.items_compra)
                subtotal = st.session_state.items_compra['Total'].sum()
                
                # Mostrar resumen
                col_res1, col_res2, col_res3 = st.columns([2, 2, 2])
                with col_res1:
                    st.metric("Total Items", total_items)
                with col_res2:
                    st.metric("Subtotal", f"${subtotal:,.2f}")
                with col_res3:
                    if sujeto_excluido:
                        iva = 0.0  # Sin IVA para sujetos excluidos
                        st.metric("IVA (13%)", f"${iva:,.2f}")
                    else:
                        iva = subtotal * 0.13  # 13% de IVA para contribuyentes normales
                        st.metric("IVA (13%)", f"${iva:,.2f}")
                
                st.markdown("---")
                if sujeto_excluido:
                    st.metric("TOTAL", f"${subtotal:,.2f}", delta_color="off")  # Total = Subtotal para sujetos excluidos
                else:
                    st.metric("TOTAL", f"${(subtotal + iva):,.2f}", delta_color="off")
            
            # Botones de acción
            col_submit, col_clear = st.columns(2)
            with col_submit:
                submit_compra = st.form_submit_button("Guardar Compra", type="primary")
            with col_clear:
                clear_items = st.form_submit_button("Limpiar Items")
            
            if clear_items:
                st.session_state.items_compra = pd.DataFrame(columns=['Cantidad', 'Descripción', 'Unidad', 'Precio Unitario', 'Total'])
                st.rerun()
            
            if submit_compra:
                if st.session_state.items_compra.empty:
                    st.error("Debe agregar al menos un item a la compra")
                elif not num_documento:
                    st.error("El número de documento/factura es obligatorio")
                else:
                    # Actualizar ingredientes (cantidad y unidad) y registrar movimientos de inventario
                    logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                    actualizar_ingredientes(st.session_state.items_compra.to_dict('records'), logged_in_user, num_documento)
                    
                    # Calcular IVA y total basado en si es sujeto excluido
                    if sujeto_excluido:
                        iva_final = 0.0
                        total_final = subtotal  # Para sujetos excluidos, total = subtotal
                    else:
                        iva_final = subtotal * 0.13
                        total_final = subtotal + iva_final
                    
                    # Crear documento de compra
                    doc_id = f"{CURRENT_PARTITION_KEY}:{str(uuid.uuid4())}"
                    
                    nueva_compra = {
                        "_id": doc_id,
                        "proveedor_id": selected_proveedor_id,
                        "proveedor_nombre": proveedor_options[selected_proveedor_id],
                        "fecha_compra": fecha_compra.isoformat(),
                        "numero_documento": num_documento,
                        "sujeto_excluido": sujeto_excluido,
                        "items": st.session_state.items_compra.to_dict('records'),
                        "subtotal": float(subtotal),
                        "iva": float(iva_final),
                        "total": float(total_final),
                        "fecha_registro": datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
                        "type": CURRENT_PARTITION_KEY
                    }
                    
                    try:
                        db.save(nueva_compra)
                        st.success("Compra registrada exitosamente!")
                        
                        # LOGGING
                        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                        tipo_compra = "Sujeto Excluido" if sujeto_excluido else "Normal"
                        couchdb_utils.log_action(
                            db, 
                            logged_in_user, 
                            f"Compra #{num_documento} registrada ({tipo_compra}) con {total_items} items (Total: ${total_final:,.2f})"
                        )
                        
                        # Limpiar formulario
                        st.session_state.items_compra = pd.DataFrame(columns=['Cantidad', 'Descripción', 'Unidad', 'Precio Unitario', 'Total'])
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al registrar la compra: {str(e)}")

        # --- Sección de Historial de Compras ---
        st.header("Historial de Compras")
        
        # Filtros
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        with col_filtro1:
            filtro_proveedor = st.selectbox(
                "Filtrar por proveedor:",
                options=["Todos"] + [p['nombre'] for p in proveedores],
                key="filtro_proveedor"
            )
        with col_filtro2:
            filtro_desde = st.date_input("Desde:", key="filtro_desde")
        with col_filtro3:
            filtro_hasta = st.date_input("Hasta:", key="filtro_hasta")
        
        # Botón de búsqueda
        if st.button("Buscar Compras", key="btn_buscar_compras"):
            st.session_state.filtro_aplicado = True
        
        # Mostrar resultados
        if st.session_state.get('filtro_aplicado', False):
            compras = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
            
            # Aplicar filtros
            if filtro_proveedor != "Todos":
                compras = [c for c in compras if c.get('proveedor_nombre') == filtro_proveedor]
            
            if filtro_desde:
                compras = [c for c in compras if datetime.strptime(c.get('fecha_compra', '1970-01-01'), "%Y-%m-%d").date() >= filtro_desde]
            
            if filtro_hasta:
                compras = [c for c in compras if datetime.strptime(c.get('fecha_compra', '1970-01-01'), "%Y-%m-%d").date() <= filtro_hasta]
            
            # Mostrar compras
            if compras:
                for compra in compras:
                    with st.expander(f"📄 Compra #{compra.get('numero_documento', 'N/A')} - {compra.get('proveedor_nombre', 'N/A')} - ${compra.get('total', 0):,.2f}", expanded=False):
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.write(f"**Proveedor:** {compra.get('proveedor_nombre', 'N/A')}")
                            st.write(f"**Fecha:** {datetime.strptime(compra.get('fecha_compra'), '%Y-%m-%d').strftime('%d/%m/%Y') if compra.get('fecha_compra') else 'N/A'}")
                            sujeto_status = "Sí" if compra.get('sujeto_excluido', False) else "No"
                            st.write(f"**Sujeto Excluido:** {sujeto_status}")
                        with col_info2:
                            st.write(f"**Documento:** {compra.get('numero_documento', 'N/A')}")
                            local_date = convert_to_local_time(compra.get('fecha_registro'))
                            st.write(f"**Registrado:** {local_date.strftime('%d/%m/%Y %H:%M') if local_date else 'N/A'}")
                        
                        # Mostrar items
                        items_df = pd.DataFrame(compra.get('items', []))
                        st.dataframe(
                            items_df,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Mostrar totales
                        col_total1, col_total2, col_total3 = st.columns(3)
                        with col_total1:
                            st.write(f"**Subtotal:** ${compra.get('subtotal', 0):,.2f}")
                        with col_total2:
                            st.write(f"**IVA (13%):** ${compra.get('iva', 0):,.2f}")
                        with col_total3:
                            st.write(f"**TOTAL:** ${compra.get('total', 0):,.2f}")
                        
                        # Botones para PDF
                        st.markdown("---")
                        col_pdf1, col_pdf2 = st.columns(2)
                        
                        with col_pdf1:
                            if st.button(f"📄 Ver Factura", key=f"ver_pdf_{compra.get('_id')}"):
                                try:
                                    pdf_data = generar_factura_compra_pdf(compra)
                                    base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                                    
                                    # Crear una nueva sección expandida para la vista previa
                                    with st.expander("📄 Vista Previa de la Factura - Click para expandir/contraer", expanded=True):
                                        st.markdown("### Vista Previa de la Factura")
                                        pdf_display = f'''
                                        <iframe 
                                            src="data:application/pdf;base64,{base64_pdf}" 
                                            width="100%" 
                                            height="800" 
                                            type="application/pdf"
                                            style="border: none;">
                                        </iframe>
                                        '''
                                        st.markdown(pdf_display, unsafe_allow_html=True)
                                        
                                        # Botón adicional para cerrar la vista previa
                                        if st.button("❌ Cerrar Vista Previa", key=f"close_pdf_{compra.get('_id')}"):
                                            st.rerun()
                                            
                                except Exception as e:
                                    st.error(f"Error al generar la vista previa: {str(e)}")
                        
                        with col_pdf2:
                            try:
                                pdf_data = generar_factura_compra_pdf(compra)
                                tipo_factura = "SujetoExcluido" if compra.get('sujeto_excluido', False) else "Normal"
                                filename = f"Factura_Compra_{tipo_factura}_{compra.get('numero_documento', 'N/A')}.pdf"
                                
                                st.download_button(
                                    label="⬇️ Descargar PDF",
                                    data=pdf_data,
                                    file_name=filename,
                                    mime="application/pdf",
                                    key=f"download_pdf_{compra.get('_id')}"
                                )
                            except Exception as e:
                                st.error(f"Error al generar PDF: {str(e)}")
            else:
                st.info("No se encontraron compras con los filtros aplicados")

    else:
        st.error("No se pudo conectar o configurar la base de datos. Revisa los mensajes de conexión.")