# couchdb_utils.py

import warnings
# Suprimir warning específico de pkg_resources deprecation
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")

import pytz
import streamlit as st
import couchdb
import json
import uuid
from datetime import datetime, timezone
import pandas as pd
from streamlit_cookies_controller import CookieController
import bcrypt # Importar la librería bcrypt para hashing de contraseñas
import menu_utils # Importar el nuevo módulo de utilidades de menú
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from auth import get_controller, initialize_auth
initialize_auth()
# controller = get_controller()  # Comentado - se obtiene dinámicamente según sea necesario


# --- Configuración de Conexión a CouchDB ---
COUCHDB_URL = "http://localhost:5984/" 
COUCHDB_USER = "admin"
COUCHDB_PASSWORD = "ues2025" # ¡CAMBIA ESTO CON TU CONTRASEÑA REAL DE COUCHDB!

# Nombre de la base de datos principal que contendrá las particiones
COUCHDB_DATABASE_NAME = "tiajuana" 

# La clave de partición fija para los documentos de usuario dentro de 'tiajuana'
PARTITION_KEY = "Usuario" # Asegúrate de que coincida con la partición real de tus documentos (minúsculas, plural)

# NUEVA CLAVE DE PARTICIÓN PARA LOGS
LOGS_PARTITION_KEY = "logs" # Clave de partición para los registros de logs
# Definir la constante de partición
CURRENT_PARTITION_KEY = "ordenes"

# --- Funciones de Hashing de Contraseñas ---
def hash_password(password):
    """
    Hashea una contraseña usando bcrypt.
    Retorna la contraseña hasheada como una cadena de texto.
    """
    # Genera un salt y hashea la contraseña
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8') # Decodifica a string para almacenamiento

def check_password(plain_password, hashed_password):
    """
    Verifica si una contraseña en texto plano coincide con una contraseña hasheada.
    Retorna True si coinciden, False en caso contrario.
    """
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        # Manejar el caso donde el hashed_password no es un hash bcrypt válido
        return False

def logout_user():
    """
    Función para cerrar sesión de usuario de forma segura
    """
    try:
        # Obtener el usuario actual antes de limpiar la sesión
        current_user = st.session_state.get('usuario', 'Usuario desconocido')
        
        # Limpiar cookies de forma específica para esta sesión
        controller = get_controller()
        if controller.get('usuario') is not None:
            controller.remove('usuario')
        if controller.get('user_data') is not None:
            controller.remove('user_data')
        if controller.get('session_id') is not None:
            controller.remove('session_id')
        
        # Registrar el cierre de sesión antes de limpiar session_state
        try:
            log_action(get_database_instance(), current_user, "Cierre de sesión exitoso.")
        except:
            pass  # Si no se puede registrar, continuar con el logout
        
        # Limpiar completamente el session_state
        st.session_state.clear()
        
        # Redirigir al login
        st.switch_page("pages/login_page.py")
        
    except Exception as e:
        # En caso de error, forzar limpieza completa
        st.session_state.clear()
        st.switch_page("pages/login_page.py")

def log_action(db_instance, user_who_performed_action, description):
    """
    Guarda un registro de actividad en la colección de logs.
    """
    utc_now = datetime.now(timezone.utc)
    local_tz = pytz.timezone('America/El_Salvador')  # Ajusta a tu zona
    local_now = utc_now.astimezone(local_tz)
    # print(f"DEBUG: log_action called. db_instance is None: {db_instance is None}, user: {user_who_performed_action}, desc: {description}")
    if not db_instance:
        print("ERROR: log_action received a None db_instance. Cannot log action.")
        return False # Cannot log if db is not available

    log_doc = {
        "usuario": user_who_performed_action,
        "descripcion": description,
        "fecha": local_now.isoformat(timespec='milliseconds') #datetime.now(timezone.utc).isoformat(timespec='milliseconds')
    }
    # print(f"DEBUG: log_action - log_doc to save: {log_doc}")
    
    # Usamos 'fecha' como id_field_for_suffix para la partición 'logs'
    # Esto generará _id como logs:<fecha_sanitizada>-<uuid_corto>
    result = save_document_with_partition(db_instance, log_doc, LOGS_PARTITION_KEY, 'fecha')
    # print(f"DEBUG: log_action - save_document_with_partition returned: {result}")
    return result

class PDF(FPDF):
    def header(self):
        # Logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'LOGO.png')
            if os.path.exists(logo_path):
                # Centrar el logo en la página de 80mm de ancho
                self.image(logo_path, 20, 8, 40)  # x=20 para centrar en 80mm, width=40
                self.set_y(self.get_y() + 25)  # Espacio después del logo
        except:
            pass
        
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 8, 'Tia Juana', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('Helvetica', '', 8)
        self.cell(0, 4, 'Elias, Salvador Alfonso', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'NIT: 0210-030563-104-1', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'IVA DL296', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'REG. 102166713', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'Giro: Restaurantes', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'Fecha Autorización: 11/12/2019', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_y(self.get_y() + 5)

    def footer(self):
        self.set_y(-30)
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 10, '!!!!! CANCELADO/PAGADO !!!!!', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 5, 'GRACIAS POR TU COMPRA', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 5, 'REGRESA PRONTO', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

class PDF_Orden(FPDF):
    def header(self):
        # Logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'LOGO.png')
            if os.path.exists(logo_path):
                # Centrar el logo en la página de 80mm de ancho
                self.image(logo_path, 20, 8, 40)  # x=20 para centrar en 80mm, width=40
                self.set_y(self.get_y() + 25)  # Espacio después del logo
        except:
            pass
        
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 8, 'Tia Juana', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('Helvetica', '', 8)
        self.cell(0, 4, 'Elias, Salvador Alfonso', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'NIT: 0210-030563-104-1', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'IVA DL296', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'REG. 102166713', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'Giro: Restaurantes', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 4, 'Fecha Autorización: 11/12/2019', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_y(self.get_y() + 5)

    def footer(self):
        self.set_y(-30)
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 10, '!!!!! EN PROCESO/COBRO !!!!!', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 5, 'GRACIAS POR TU COMPRA', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.cell(0, 5, 'REGRESA PRONTO', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

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

def generar_orden_pdf(ticket, orden, mesa, mesero):
    """Genera PDF para órdenes enviadas a cobro (en proceso)"""
    pdf = PDF_Orden('P', 'mm', (80, 200)) # Ancho de ticket de 80mm
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Helvetica', '', 9)

    # Info del Ticket
    pdf.cell(0, 5, f"Orden #{ticket.get('numero_orden', 'N/A')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    fecha_pago = datetime.now(timezone.utc).astimezone().strftime('%d/%m/%Y %I:%M:%S %p')
    pdf.cell(0, 5, f"Fecha: {fecha_pago}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    mesa_nombre_limpio = limpiar_texto_pdf(mesa.get('descripcion', 'N/A'))
    pdf.cell(0, 5, f"Mesa: {mesa_nombre_limpio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    mesero_nombre_limpio = limpiar_texto_pdf(mesero.get('nombre', 'N/A'))
    pdf.cell(0, 5, f"Mesero: {mesero_nombre_limpio}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
    pdf.set_y(pdf.get_y() + 5)

    # Encabezados de productos
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(10, 5, 'CANT.', new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
    pdf.cell(30, 5, 'PRODUCTO', new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
    pdf.cell(15, 5, 'PRECIO', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(15, 5, 'TOTAL', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 70, pdf.get_y())
    pdf.set_y(pdf.get_y() + 2)

    # Items
    pdf.set_font('Helvetica', '', 8)
    subtotal = sum(item.get('cantidad', 0) * item.get('precio_unitario', 0) for item in orden.get('items', []))
    
    for item in orden.get('items', []):
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
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(40, 5, 'Subtotal:', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 5, f"${subtotal:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.cell(40, 5, 'Servicio (10%):', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 5, f"${servicio:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(40, 8, 'TOTAL:', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 8, f"${total_final:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

    return bytes(pdf.output())

def generar_ticket_pdf(ticket, orden, mesa, mesero):
    pdf = PDF('P', 'mm', (80, 200)) # Ancho de ticket de 80mm
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Helvetica', '', 9)

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
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(10, 5, 'CANT.', new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
    pdf.cell(30, 5, 'PRODUCTO', new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
    pdf.cell(15, 5, 'PRECIO', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(15, 5, 'TOTAL', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 70, pdf.get_y())
    pdf.set_y(pdf.get_y() + 2)

    # Items
    pdf.set_font('Helvetica', '', 8)
    subtotal = sum(item.get('cantidad', 0) * item.get('precio_unitario', 0) for item in orden.get('items', []))
    
    for item in orden.get('items', []):
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
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(40, 5, 'Subtotal:', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 5, f"${subtotal:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.cell(40, 5, 'Servicio (10%):', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 5, f"${servicio:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(40, 8, 'TOTAL:', new_x=XPos.RIGHT, new_y=YPos.TOP, align='R')
    pdf.cell(30, 8, f"${total_final:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

    return bytes(pdf.output())
#para la pantalla inicial de estadisticas
def get_all_paid_orders(db):
    """
    Recupera todas las órdenes con estado 'pagada'.
    """
    all_orders = get_documents_by_partition(db, "ordenes")
    # print(f"DEBUG: get_all_paid_orders - Total orders fetched: {len(all_orders)}")
    # Asegurarse de que 'fecha_pago' exista para las órdenes pagadas.
    # Si no, se puede asumir que 'fecha_creacion' es el momento de pago para propósitos estadísticos.
    return [order for order in all_orders if order.get('estado') == 'pagada']

def get_all_purchases(db):
    """
    Recupera todos los documentos de compras.
    Asume una partición 'compras'. Los documentos deben tener un campo 'fecha' y 'total'.
    """
    # La función get_documents_by_partition creará la vista si no existe.
    return get_documents_by_partition(db, "compras")

def get_all_inventory_records(db):
    """
    Genera registros de movimiento de inventario a partir de compras y ventas.
    Asume que las compras son entradas de inventario (valor = total_compra).
    Asume que las ventas son salidas de inventario (valor = total de la orden pagada).
    Esto es una simplificación y no representa el costo real de los bienes vendidos.
    """
    inventory_movements = []

    # Obtener todos los registros de compras (entradas de inventario)
    purchases = get_all_purchases(db)
    for p in purchases:
        if p.get('fecha_compra') and p.get('total_compra') is not None:
            inventory_movements.append({
                'fecha': p['fecha_compra'],
                'tipo': 'entrada',
                'valor_entrada': p['total_compra'],
                'valor_salida': 0.0,
                'descripcion': f"Compra #{p.get('numero_compra', p['_id'])}"
            })

    # Obtener todas las órdenes pagadas (salidas de inventario)
    paid_orders = get_all_paid_orders(db)
    for o in paid_orders:
        # Usar 'fecha_pago' si existe, de lo contrario 'fecha_creacion'
        date_field = o.get('fecha_pago') or o.get('fecha_creacion')
        if date_field and o.get('total') is not None:
            inventory_movements.append({
                'fecha': date_field,
                'tipo': 'salida',
                'valor_entrada': 0.0,
                'valor_salida': o['total'], # Usando el total de la venta como proxy del valor de salida
                'descripcion': f"Venta #{o.get('numero_orden', o['_id'])}"
            })
    
    # Ordenar por fecha para asegurar un procesamiento cronológico correcto en las estadísticas
    inventory_movements.sort(key=lambda x: datetime.fromisoformat(x['fecha']))

    return inventory_movements

def generar_resumen_ventas_pdf(ordenes_pagadas, mesas_dict, meseros_dict, start_date=None, end_date=None):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Resumen de Ventas', 0, 1, 'C')
    pdf.ln(5)

    report_date_str = datetime.now(timezone.utc).strftime('%d/%m/%Y')
    date_range_str = ""
    if start_date and end_date:
        date_range_str = f"Periodo: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
    elif start_date:
        date_range_str = f"Desde: {start_date.strftime('%d/%m/%Y')}"
    elif end_date:
        date_range_str = f"Hasta: {end_date.strftime('%d/%m/%Y')}"
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Fecha de Generación: {report_date_str}", 0, 1)
    if date_range_str:
        pdf.cell(0, 10, date_range_str, 0, 1)
    pdf.ln(5)

    total_ventas = sum(o.get('total', 0) for o in ordenes_pagadas)
    total_items_vendidos = sum(sum(item.get('cantidad', 0) for item in o.get('items', [])) for o in ordenes_pagadas)

    pdf.cell(0, 10, f"Total de Órdenes Pagadas: {len(ordenes_pagadas)}", 0, 1)
    pdf.cell(0, 10, f"Total de Ventas Brutas: ${total_ventas:.2f}", 0, 1)
    pdf.cell(0, 10, f"Total de Ítems Vendidos: {total_items_vendidos}", 0, 1)
    pdf.ln(10)

    if ordenes_pagadas:
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(25, 7, 'Orden #', 1, 0, 'C')
        pdf.cell(35, 7, 'Mesa', 1, 0, 'C')
        pdf.cell(40, 7, 'Mesero', 1, 0, 'C')
        pdf.cell(30, 7, 'Total', 1, 0, 'C')
        pdf.cell(45, 7, 'Fecha/Hora Pago', 1, 1, 'C')
        
        pdf.set_font('Arial', '', 9)
        for orden in ordenes_pagadas:
            orden_num = orden.get('numero_orden', 'N/A')
            mesa_desc = mesas_dict.get(orden.get('mesa_id'), {}).get('descripcion', 'N/A')
            mesero_nombre = meseros_dict.get(orden.get('mesero_id'), {}).get('nombre', 'N/A')
            total = f"${orden.get('total', 0):.2f}"
            fecha_pago_str = orden.get('fecha_pago', orden.get('fecha_creacion')) # Use fecha_pago if available
            fecha_hora_display = datetime.fromisoformat(fecha_pago_str).strftime('%d/%m/%Y %H:%M')
            
            pdf.cell(25, 6, str(orden_num), 1, 0)
            pdf.cell(35, 6, mesa_desc, 1, 0)
            pdf.cell(40, 6, mesero_nombre, 1, 0)
            pdf.cell(30, 6, total, 1, 0, 'R')
            pdf.cell(45, 6, fecha_hora_display, 1, 1)
            
    else:
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, 'No hay órdenes pagadas para el criterio seleccionado.', 0, 1, 'C')

    return bytes(pdf.output(dest='S'))

# --- Funciones Genéricas para CouchDB ---

@st.cache_resource
def get_couchdb_server():
    """
    Establece y retorna el objeto servidor de CouchDB.
    Cacheada para evitar reconexiones.
    """
    try:
        server = couchdb.Server(COUCHDB_URL)
        server.resource.credentials = (COUCHDB_USER, COUCHDB_PASSWORD)
        _ = server.version() # Verificar conexión
        return server
    except couchdb.http.Unauthorized:
        st.error("Error de autenticación en CouchDB. Verifica tu usuario y contraseña.")
        return None
    except Exception as e:
        st.error(f"Error al conectar a CouchDB: {e}. Asegúrate de que CouchDB esté corriendo en {COUCHDB_URL}")
        return None

def get_database_instance():
    """
    Obtiene la instancia de la base de datos principal y la crea si no existe como particionada.
    """
    server = get_couchdb_server()
    if not server:
        return None

    try:
        if COUCHDB_DATABASE_NAME not in server:
            server.resource.put(COUCHDB_DATABASE_NAME, body={"partitioned": True})
            st.success(f"Base de datos particionada '{COUCHDB_DATABASE_NAME}' creada exitosamente.")
            return server[COUCHDB_DATABASE_NAME]
        else:
            db = server[COUCHDB_DATABASE_NAME]
            db_info = db.info() 
            if db_info.get("props", {}).get("partitioned") == True:
                return db
            else:
                st.error(f"La base de datos '{COUCHDB_DATABASE_NAME}' existe pero NO es particionada. Para usarla como particionada, debes eliminarla y recréala con las propiedades correctas.")
                return None
    except couchdb.http.ServerError as e:
        if e.args[0] == 412: 
            db = server[COUCHDB_DATABASE_NAME]
            db_info = db.info()
            if db_info.get("props", {}).get("partitioned") == True:
                return db
            else:
                 st.error(f"La base de datos '{COUCHDB_DATABASE_NAME}' existe pero NO es particionada (manejo de error 412). Para usarla como particionada, debes eliminarla y recréala con las propiedades correctas.")
                 return None
        st.error(f"Error en el servidor CouchDB al crear/verificar DB particionada: {e}")
        return None
    except Exception as e:
        st.error(f"Error inesperado al obtener/crear la DB '{COUCHDB_DATABASE_NAME}': {e}")
        return None

def get_documents_by_partition(db, partition_key_filter=None):
    """
    Obtiene documentos filtrados por una clave de partición específica.
    Si no se proporciona partition_key_filter, obtiene todos los documentos (¡cuidado con grandes DBs!).
    """
    try:
        if partition_key_filter:
            start_key = f"{partition_key_filter}:"
            end_key = f"{partition_key_filter}:\ufff0" 
            rows = db.view('_all_docs', startkey=start_key, endkey=end_key, include_docs=True)
            return [row.doc for row in rows]
        else:
            return [row.doc for row in db.view('_all_docs', include_docs=True)]
    except Exception as e:
        st.error(f"Error al obtener documentos para la partición '{partition_key_filter}': {e}")
        return []

def save_document_with_partition1(db, doc, partition_key, unique_field=None):
    try:
        # Si el documento ya tiene _id, es una actualización
        if '_id' in doc:
            # Asegurarse de incluir _rev para actualizaciones
            existing = db[doc['_id']]
            doc['_rev'] = existing['_rev']
            db.save(doc)
            return True
        else:
            # Es un nuevo documento
            doc['type'] = partition_key
            db.save(doc)
            return True
    except Exception as e:
        st.error(f"Error al guardar documento: {str(e)}")
        return False

#para ordenar platos
def get_users_by_role(db, role_id):
    """Obtiene usuarios por rol con múltiples enfoques"""
    try:
        # Intento 1: Buscar usuarios con id_rol
        users = []
        try:
            results = db.find({
                "selector": {
                    "id_rol": role_id,
                    "activo": 1
                },
                "limit": 100
            })
            users = list(results)
        except:
            pass
        
        # Intento 2: Buscar en todos los documentos si falla
        if not users:
            all_docs = [doc for doc in db if doc.get('id_rol') == role_id and doc.get('activo', 0) == 1]
            users = all_docs[:100]  # Limitar a 100 resultados
        
        return users
        
    except Exception as e:
        print(f"Error getting users: {str(e)}")
        return []
            
def get_mesas(db):
    try:
        results = db.find({
            "selector": {
                "type": "mesas"
            }
        })
        return [doc for doc in results] or []
    except Exception as e:
        st.error(f"Error al obtener mesas: {str(e)}")
        return []

# def get_next_order_number(db):
#     try:
#         # Buscar la última orden
#         last_order = db.view('_design/orders/_view/by_order_number', 
#                            limit=1, 
#                            descending=True).rows
        
#         if last_order and len(last_order) > 0:
#             # Asegurarse de que el valor es numérico
#             last_number = int(last_order[0].key)
#             return last_number + 1
#         else:
#             return 1  # Primera orden
    
#     except Exception as e:
#         print(f"Error al obtener número de orden: {str(e)}")
#         return 1  # Valor por defecto si hay error
def get_next_order_number(db):
    try:
        # Obtener configuración del sistema
        configuracion = obtener_configuracion_sistema(db)
        numero_inicial_configurado = configuracion.get('numero_orden_inicial', 1)
        
        # Buscar la última orden, ESPECIFICANDO LA PARTICIÓN
        last_order = db.view('_design/orders/_view/by_order_number',
                           limit=1,
                           descending=True,
                           partition=CURRENT_PARTITION_KEY # ADD THIS LINE
                           ).rows
        
        if last_order and len(last_order) > 0:
            # Asegurarse de que el valor es numérico
            last_number = int(last_order[0].key)
            # Retornar el máximo entre el último número usado + 1 y el configurado
            return max(last_number + 1, numero_inicial_configurado)
        else:
            return numero_inicial_configurado  # Primera orden usa la configuración
    
    except Exception as e:
        print(f"Error al obtener número de orden: {str(e)}")
        return 1  # Valor por defecto si hay error

def get_next_ticket_number(db):
    """Obtiene el siguiente número de ticket correlativo"""
    try:
        # Obtener configuración del sistema
        configuracion = obtener_configuracion_sistema(db)
        numero_inicial_configurado = configuracion.get('numero_ticket_inicial', 1)
        
        last_ticket = db.find({
            "selector": {"type": "tickets"},
            "sort": [{"numero_ticket": "desc"}],
            "limit": 1
        })
        
        if last_ticket:
            last_number = last_ticket[0]['numero_ticket']
            # Retornar el máximo entre el último número usado + 1 y el configurado
            return max(last_number + 1, numero_inicial_configurado)
        else:
            return numero_inicial_configurado  # Primer ticket usa la configuración
    except:
        return 1

def obtener_configuracion_sistema(db):
    """Obtiene la configuración del sistema, creándola si no existe"""
    try:
        config_docs = list(db.find({"selector": {"type": "configuracion"}}))
        if config_docs:
            return config_docs[0]
        else:
            # Crear configuración por defecto
            from datetime import datetime, timezone
            import uuid
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
        print(f"Error al obtener configuración del sistema: {e}")
        # Retornar configuración por defecto en caso de error
        return {
            "numero_orden_inicial": 1,
            "numero_ticket_inicial": 1,
            "alertas_stock": {}
        }

def verificar_alertas_stock_bajo(db):
    """Verifica ingredientes con stock bajo usando alertas configurables y retorna alertas"""
    alertas = []
    try:
        # Obtener configuración del sistema
        configuracion = obtener_configuracion_sistema(db)
        alertas_config = configuracion.get('alertas_stock', {})
        
        # Obtener ingredientes activos
        ingredientes = get_documents_by_partition(db, "ingredientes")
        ingredientes_activos = [i for i in ingredientes if i.get('activo', 0) == 1]
        
        for ingrediente in ingredientes_activos:
            ingrediente_id = ingrediente['_id']
            cantidad = float(ingrediente.get('cantidad', 0))
            nombre = ingrediente.get('descripcion', 'Ingrediente sin nombre')
            unidad = ingrediente.get('unidad', 'unidad')
            
            # Buscar configuración específica para este ingrediente
            config_ingrediente = alertas_config.get(ingrediente_id, {})
            limite_minimo = config_ingrediente.get('minimo', 10)  # Por defecto 10
            
            if cantidad == 0:
                alertas.append({
                    'tipo': 'critico',
                    'nivel': 'error',
                    'mensaje': f"🚨 CRÍTICO: {nombre} está AGOTADO (0 {unidad})",
                    'ingrediente_id': ingrediente_id,
                    'cantidad': cantidad,
                    'limite_configurado': limite_minimo
                })
            elif cantidad <= limite_minimo:
                # Determinar si es crítico o advertencia basado en el porcentaje del límite
                if cantidad <= (limite_minimo * 0.3):  # 30% del límite o menos = crítico
                    alertas.append({
                        'tipo': 'critico',
                        'nivel': 'error',
                        'mensaje': f"🚨 CRÍTICO: Quedan solo {cantidad:.1f} {unidad} de {nombre} (límite: {limite_minimo})",
                        'ingrediente_id': ingrediente_id,
                        'cantidad': cantidad,
                        'limite_configurado': limite_minimo
                    })
                else:  # Entre 30% y 100% del límite = advertencia
                    alertas.append({
                        'tipo': 'advertencia',
                        'nivel': 'warning',
                        'mensaje': f"⚠️ STOCK BAJO: Quedan {cantidad:.1f} {unidad} de {nombre} (límite: {limite_minimo})",
                        'ingrediente_id': ingrediente_id,
                        'cantidad': cantidad,
                        'limite_configurado': limite_minimo
                    })
                    
    except Exception as e:
        alertas.append({
            'tipo': 'error',
            'nivel': 'error',
            'mensaje': f"Error al verificar stock: {str(e)}",
            'ingrediente_id': None,
            'cantidad': 0
        })
    
    return alertas

def generar_ticket(db, orden):
    """Genera un ticket de cobro con número correlativo"""
    try:
        # Verificar que 'orden' sea un diccionario
        if not isinstance(orden, dict):
            raise ValueError("El parámetro 'orden' debe ser un diccionario")
            
        # Obtener el último número de ticket (método alternativo sin índices)
        all_tickets = [doc for doc in db if doc.get('type') == 'tickets']
        numero_ticket = max([tkt.get('numero_ticket', 0) for tkt in all_tickets] or [0]) + 1
        
        # Crear documento de ticket
        ticket_doc = {
            "_id": f"tickets:{str(uuid.uuid4())}",
            "type": "tickets",
            "numero_ticket": numero_ticket,
            "orden_id": orden.get('_id', ''),
            "numero_orden": orden.get('numero_orden', 0),
            "mesa_id": orden.get('mesa_id', ''),
            "mesero_id": orden.get('mesero_id', ''),
            "items": orden.get('items', []),
            "total": float(orden.get('total', 0)),
            "fecha_creacion": datetime.now(timezone.utc).isoformat(),
            "estado": "pendiente_pago"
        }
        
        # Guardar ticket
        db.save(ticket_doc)
        
        # Actualizar estado de la orden
        if isinstance(orden, dict):
            orden['estado'] = 'en_cobro'
            db.save(orden)
        
        return numero_ticket, None  # Retorna número de ticket y error
        
    except Exception as e:
        return None, str(e)
    
def save_document_with_partition(db, doc_data, partition_key, id_field_for_suffix):
    """
    Guarda (crea o actualiza) un documento en la base de datos particionada.
    id_field_for_suffix: El nombre del campo del documento que se usará para construir el sufijo del _id.
    """
    try:
        # print(f"DEBUG: save_document_with_partition - doc_data inicial: {doc_data}")
        # print(f"DEBUG: save_document_with_partition - partition_key: {partition_key}, id_field_for_suffix: {id_field_for_suffix}")

        # Asegurarse de que todas las fechas se guarden en formato ISO estándar
        # y que los valores datetime sean convertidos a string antes de usarlos para el sufijo
        for key, value in doc_data.items():
            if isinstance(value, datetime):
                doc_data[key] = value.isoformat(timespec='milliseconds')
        # print(f"DEBUG: save_document_with_partition - doc_data después de formatear fechas: {doc_data}")

        # Obtener el valor del campo que se usará como sufijo, ahora que las fechas son strings
        raw_suffix_value = doc_data.get(id_field_for_suffix, '')
        # print(f"DEBUG: save_document_with_partition - raw_suffix_value para sufijo: '{raw_suffix_value}'")
        
        # Sanitizar suffix_value para CouchDB ID
        if id_field_for_suffix == 'fecha' and isinstance(raw_suffix_value, str):
            try:
                dt_obj = datetime.fromisoformat(raw_suffix_value)
                suffix_value = dt_obj.strftime('%Y%m%d%H%M%S%f')[:-3] # YYYYMMDDHHMMSSmmm
                # print(f"DEBUG: save_document_with_partition - Fecha parseada, suffix_value: '{suffix_value}'")
            except ValueError:
                suffix_value = raw_suffix_value.replace(':', '').replace('.', '').replace('+', '').replace('-', '').replace('T', '')
                st.warning(f"No se pudo parsear la fecha '{raw_suffix_value}' para el ID. Usando formato simplificado.")
                # print(f"DEBUG: save_document_with_partition - Fallo al parsear fecha, fallback suffix_value: '{suffix_value}'")
        else:
            suffix_value = str(raw_suffix_value).lower().replace(' ', '-')
            # print(f"DEBUG: save_document_with_partition - Sufijo no fecha, suffix_value: '{suffix_value}'")
        
        if not suffix_value:
            st.error(f"El campo '{id_field_for_suffix}' es obligatorio para generar el ID de partición y un _id válido.")
            # print(f"ERROR: save_document_with_partition - El valor del sufijo está vacío para '{id_field_for_suffix}'")
            return False

        expected_id_prefix = f"{partition_key}:{suffix_value}"
        # print(f"DEBUG: save_document_with_partition - expected_id_prefix: '{expected_id_prefix}'")
        
        # Solo establecer _id si es nuevo o no coincide con el prefijo esperado
        if '_id' not in doc_data or not doc_data['_id'].startswith(expected_id_prefix):
            doc_data['_id'] = f"{expected_id_prefix}-{str(uuid.uuid4())[:8]}"
            # print(f"DEBUG: save_document_with_partition - Generado nuevo _id: '{doc_data['_id']}'")
        else:
            print(f"DEBUG: save_document_with_partition - Usando _id existente: '{doc_data['_id']}'")

        doc_id, doc_rev = db.save(doc_data)
        st.success(f"Documento guardado exitosamente con ID: {doc_id}")
        # print(f"DEBUG: save_document_with_partition - Documento guardado con ID: {doc_id}, REV: {doc_rev}")
        return True
    except Exception as e:
        st.error(f"Error al guardar documento: {e}")
        # print(f"EXCEPTION in save_document_with_partition: {e}")
        return False

def delete_document(db, doc_id, doc_rev):
    """Elimina un documento de la base de datos."""
    try:
        db.delete({'_id': doc_id, '_rev': doc_rev})
        st.success(f"Documento con ID '{doc_id}' eliminado exitosamente.")
        return True
    except Exception as e:
        st.error(f"Error al eliminar documento: {e}")
        return False

# --- Funciones de Autenticación ---

def validarUsuario(usuario, clave):    
    """
    Permite la validación de usuario y clave contra CouchDB.
    """    
    db = get_database_instance()
    if not db:
        st.error("No se pudo conectar a la base de datos de CouchDB para la validación de usuario.")
        return False

    all_users_in_partition = get_documents_by_partition(db, PARTITION_KEY)

    for user_doc in all_users_in_partition:
        stored_username = user_doc.get('usuario')
        stored_hashed_password = user_doc.get('password')

        if stored_username == usuario:
            # Verificar la contraseña hasheada
            if stored_hashed_password and check_password(clave, stored_hashed_password):
                st.session_state['user_data'] = user_doc 
                return True
            else:
                # Contraseña incorrecta o hash inválido
                return False
    return False # Usuario no encontrado

# -----------------------------------------------------------
#  Funciones de menú y login (ahora usan menu_utils)
# -----------------------------------------------------------

def generarMenu(usuario_nombre_couchdb):
    user_data = st.session_state.get('user_data')
    if not user_data:
        st.warning("Datos de usuario no disponibles para el menú. Redirigiendo a login.")
        controller = get_controller()
        if controller.get('usuario') is not None: 
            controller.remove('usuario')
        if controller.get('user_data') is not None:
            controller.remove('user_data')
        st.session_state.clear()
        st.switch_page("pages/login_page.py") 
        return

    # MODIFICACIÓN: Envolver la llamada a render_sidebar_content en st.sidebar
    with st.sidebar:
        menu_utils.render_sidebar_content(user_data, user_data.get('id_rol', 'N/A'))


def generarMenuRoles(usuario_nombre_couchdb):
    user_data = st.session_state.get('user_data')
    if not user_data:
        st.warning("Datos de usuario no disponibles para el menú. Redirigiendo a login.")
        controller = get_controller()
        if controller.get('usuario') is not None: 
            controller.remove('usuario')
        if controller.get('user_data') is not None:
            controller.remove('user_data')
        st.session_state.clear()
        st.switch_page("pages/login_page.py") 
        return

    # MODIFICACIÓN: Envolver la llamada a render_sidebar_content en st.sidebar
    with st.sidebar:
        menu_utils.render_sidebar_content(user_data, user_data.get('id_rol', 'N/A'))


# -----------------------------------------------------------
#  Función generarLogin (principal punto de entrada)
# -----------------------------------------------------------
def generarLogin(archivo_pagina_actual):
    # Asegurar que tenemos un session_id único
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Verificar integridad de la sesión
    if 'session_timestamp' not in st.session_state:
        st.session_state.session_timestamp = datetime.now(timezone.utc).isoformat()
    
    # Validar que la sesión no sea demasiado antigua (opcional: timeout de 8 horas)
    try:
        session_time = datetime.fromisoformat(st.session_state.session_timestamp.replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        if (current_time - session_time).total_seconds() > 28800:  # 8 horas
            st.session_state.clear()
            controller = get_controller()
            if controller.get('usuario') is not None:
                controller.remove('usuario')
            if controller.get('user_data') is not None:
                controller.remove('user_data')
    except:
        # Si hay error en el timestamp, limpiar sesión
        st.session_state.clear()
    
    controller = get_controller()
    usuario_cookie = controller.get('usuario')
    user_data_cookie_str = controller.get('user_data') 
    
    # Validar que el usuario de la cookie coincida con el de session_state si existe
    if 'usuario' in st.session_state and usuario_cookie and st.session_state['usuario'] != usuario_cookie:
        # Inconsistencia detectada - limpiar todo
        st.session_state.clear()
        controller = get_controller()
        if controller.get('usuario') is not None:
            controller.remove('usuario')
        if controller.get('user_data') is not None:
            controller.remove('user_data')
        usuario_cookie = None
        user_data_cookie_str = None
    
    # DEBUG: Mostrar información de sesión para verificar aislamiento
    if st.secrets.get("debug_sessions", False):
        st.sidebar.info(f"Session ID: {st.session_state.get('session_id', 'N/A')[:8]}...")
        st.sidebar.info(f"Usuario: {st.session_state.get('usuario', 'N/A')}")
    
    # print(f"DEBUG: generarLogin - session_id: {st.session_state.get('session_id')}, usuario_cookie: {usuario_cookie}, user_data_cookie_str: {user_data_cookie_str}")
    
    if usuario_cookie and 'user_data' not in st.session_state:
        db_instance = get_couchdb_server()
        if db_instance:
            db = get_database_instance()
            if db:
                all_users_in_partition = get_documents_by_partition(db, PARTITION_KEY)
                found_user = None
                # print(f"Tipo de dato recibido: {type(user_data_cookie_str)}")
                # print(f"Contenido recibido: {user_data_cookie_str}")
                if user_data_cookie_str:
                    try:
                        if isinstance(user_data_cookie_str, dict):
                            found_user = user_data_cookie_str  # Ya es diccionario
                        else:
                            found_user = json.loads(user_data_cookie_str)  # Convierte de string a dict
                    except json.JSONDecodeError:
                        st.warning("Cookie 'user_data' corrupta, intentando revalidar con usuario.")
                        found_user = None

                if not found_user: 
                    for user_doc in all_users_in_partition:
                        if user_doc.get('usuario') == usuario_cookie:
                            found_user = user_doc 
                            break
                
                if found_user:
                    st.session_state['usuario'] = usuario_cookie
                    st.session_state['user_data'] = found_user
                    controller = get_controller()
                    controller.set('user_data', json.dumps(found_user)) 
                else:
                    controller = get_controller()
                    if controller.get('usuario') is not None:
                        controller.remove('usuario')
                    if controller.get('user_data') is not None:
                        controller.remove('user_data') 
                    st.session_state.clear()
            else: 
                st.error("No se pudo acceder a la base de datos para revalidar sesión. Intente iniciar sesión de nuevo.")
                controller = get_controller()
                if controller.get('usuario') is not None:
                    controller.remove('usuario')
                if controller.get('user_data') is not None:
                    controller.remove('user_data') 
                st.session_state.clear()


    if 'usuario' in st.session_state:
        # print(f"DEBUG: session state ya autenticado: {st.session_state}")
        # Aquí se llama a las funciones que renderizan el menú, las cuales ya manejan el `with st.sidebar:` internamente.
        if st.secrets.get("tipoPermiso") == "rolpagina":
            generarMenuRoles(st.session_state['usuario']) 
        else:
             generarMenu(st.session_state['usuario'])
            
    else:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("assets/LOGO.png",
                     
                     width=300)
        # st.markdown("---") 

        with st.form('frmLogin'):
            parUsuario = st.text_input('Usuario', key='login_username_input')
            parPassword = st.text_input('Contraseña', type='password', key='login_password_input')
            btnLogin = st.form_submit_button('Ingresar', type='primary')
           
            if btnLogin:
                if validarUsuario(parUsuario, parPassword):
                    # Establecer nueva sesión con timestamp actualizado
                    st.session_state['usuario'] = parUsuario
                    st.session_state['session_timestamp'] = datetime.now(timezone.utc).isoformat()
                    
                    # Obtener el controlador de cookies para esta sesión específica
                    controller = get_controller()
                    controller.set('usuario', parUsuario)
                    controller.set('user_data', json.dumps(st.session_state['user_data'])) 
                    controller.set('session_id', st.session_state['session_id'])
                    
                    #agregar al log de actividad
                    log_action(get_database_instance(), parUsuario, "Inicio de sesión exitoso.")
                    st.switch_page("inicio.py")
                    
                else:
                    st.error("Usuario o contraseña inválidos", icon=":material/gpp_maybe:")
        
        # Enlace al manual del sistema
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-top: 20px;">
                <p style="margin-bottom: 10px; color: #666;">¿Necesitas ayuda?</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("📖 Ver Manual del Sistema", type="secondary", use_container_width=True):
                st.switch_page("pages/manual.py")
            
            st.markdown("""
            <div style="text-align: center; margin-top: 15px;">
                <p style="font-size: 0.8em; color: #888;">
                    El manual contiene toda la información sobre<br/>
                    cómo usar el sistema de restaurante
                </p>
            </div>
            """, unsafe_allow_html=True)

def registrar_movimiento_inventario(db, plato_id, cantidad_vendida, usuario):
    """
    Registra movimientos de inventario (salidas de ingredientes) cuando se vende un plato.
    """
    try:
        # Obtener el plato para verificar si usa ingredientes
        platos = get_documents_by_partition(db, "platos")
        plato = next((p for p in platos if p['_id'] == plato_id), None)
        
        if not plato:
            return False
            
        if plato.get('usa_ingrediente', 0) == 1:
            # Obtener ingredientes disponibles para mapear ingredientes del plato
            ingredientes = get_documents_by_partition(db, "ingredientes")
            ingredientes_activos = {ing['_id']: ing for ing in ingredientes if ing.get('activo', 0) == 1}
            
            # Mapear ingredientes por nombre del plato (lógica simplificada)
            ingredientes_plato = obtener_ingredientes_por_plato(plato, ingredientes_activos)
            
            # Registrar movimiento de salida para cada ingrediente y actualizar stock
            alertas_stock = []
            
            for ingrediente_info in ingredientes_plato:
                ingrediente_id = ingrediente_info['ingrediente_id']
                cantidad_usada = ingrediente_info['cantidad'] * cantidad_vendida
                
                # 1. Crear movimiento de inventario
                movimiento = {
                    "_id": f"inventario:{uuid.uuid4()}",
                    "type": "inventario", 
                    "ingrediente_id": ingrediente_id,
                    "tipo": "salida",
                    "cantidad": -cantidad_usada,  # Negativo para salidas
                    "motivo": f"Venta de {plato.get('descripcion', 'plato')}",
                    "usuario": usuario,
                    "fecha_creacion": datetime.now(timezone.utc).isoformat()
                }
                db.save(movimiento)
                
                # 2. Actualizar cantidad física en la tabla de ingredientes
                try:
                    ingrediente_doc = db[ingrediente_id]
                    cantidad_actual = float(ingrediente_doc.get('cantidad', 0))
                    nueva_cantidad = cantidad_actual - cantidad_usada
                    
                    # Verificar que no quede negativo
                    if nueva_cantidad < 0:
                        nueva_cantidad = 0
                        st.warning(f"⚠️ Stock insuficiente de {ingrediente_doc.get('descripcion', 'ingrediente')}. Se agotó el inventario.")
                    
                    # Actualizar la cantidad en el documento del ingrediente
                    ingrediente_doc['cantidad'] = nueva_cantidad
                    db.save(ingrediente_doc)
                    
                    # 3. Verificar alerta de stock bajo (menos de 10 unidades)
                    if nueva_cantidad <= 10 and nueva_cantidad > 0:
                        nombre_ingrediente = ingrediente_doc.get('descripcion', 'Ingrediente desconocido')
                        unidad = ingrediente_doc.get('unidad', 'unidades')
                        alertas_stock.append(f"🔔 ALERTA: Quedan solo {nueva_cantidad:.1f} {unidad} de {nombre_ingrediente}. ¡Es necesario comprar más!")
                    elif nueva_cantidad == 0:
                        nombre_ingrediente = ingrediente_doc.get('descripcion', 'Ingrediente desconocido')
                        alertas_stock.append(f"🚨 CRÍTICO: {nombre_ingrediente} se ha AGOTADO. ¡Compra urgente necesaria!")
                        
                except Exception as e:
                    st.error(f"Error al actualizar stock de ingrediente {ingrediente_id}: {e}")
            
            # Mostrar alertas de stock bajo
            for alerta in alertas_stock:
                st.warning(alerta)
            
            return True
        else:
            return False
    except Exception as e:
        st.error(f"Error al registrar movimiento de inventario: {e}")
        return False

def obtener_ingredientes_por_plato(plato, ingredientes_activos):
    """
    Determina qué ingredientes usa un plato y en qué cantidad.
    Por ahora usa lógica simplificada basada en el nombre del plato.
    En el futuro se puede expandir a un sistema de recetas completo.
    """
    plato_nombre = plato.get('descripcion', '').lower()
    ingredientes_plato = []
    
    # Mapeos específicos y exactos de platos a ingredientes
    if plato_nombre == 'balde de pilsener':
        # Balde de Pilsener: 6 cervezas Pilsener
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            if 'pilsener' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 6})  # 6 cervezas
    
    elif plato_nombre == 'pilsener':
        # Pilsener individual: 1 cerveza Pilsener
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            if 'pilsener' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 1})  # 1 cerveza
    
    elif plato_nombre == 'cuba libre':
        # Cuba libre: ron, coca cola, limón
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            if 'ron' in nombre_ing or 'flor de cana' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 0.05})  # 1.5 oz ron (~45ml de una botella de 750ml)
            elif 'coca cola' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 0.6})  # 0.6 de una lata/botella para el mix
            elif 'limon' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 0.5})  # medio limón
    
    elif plato_nombre == 'mojito liz':
        # Mojito: ron, hierba buena, limón, azúcar
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            if 'ron' in nombre_ing or 'flor de cana' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 2})  # 2 oz ron
            elif 'hierva buena' in nombre_ing or 'hierbabuena' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 0.1})  # hojas de hierba buena
            elif 'limon' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 1})  # 1 limón
    
    elif plato_nombre == 'shot de tequila':
        # Shot de Tequila: tequila
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            if 'tequila' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 1.5})  # 1.5 oz tequila
    
    elif plato_nombre == 'coca cola':
        # Coca Cola: coca cola
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            if 'coca cola' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 1})  # 1 unidad (botella/lata)
    
    elif plato_nombre == 'alitas':
        # Alitas: pollo, condimentos
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            # Buscar ingredientes relacionados con pollo o carnes
            if any(word in nombre_ing for word in ['pollo', 'alita', 'carne']):
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 300})  # 300g pollo
    
    elif plato_nombre == 'carnitas mixtas':
        # Carnitas mixtas: carne de res, carne de cerdo, condimentos
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            if any(word in nombre_ing for word in ['carne', 'res', 'cerdo']):
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 200})  # 200g carne mixta
            elif any(word in nombre_ing for word in ['cebolla', 'tomate']):
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 50})  # 50g verduras
    
    elif plato_nombre == 'tacos al pastor':
        # Tacos al Pastor: carne al pastor, tortilla, cebolla, cilantro
        for ing_id, ing in ingredientes_activos.items():
            nombre_ing = ing.get('descripcion', '').lower()
            if any(word in nombre_ing for word in ['carne', 'pastor']):
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 150})  # 150g carne
            elif 'tortilla' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 3})  # 3 tortillas
            elif 'cebolla' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 30})  # 30g cebolla
            elif 'cilantro' in nombre_ing:
                ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 10})  # 10g cilantro
    
    else:
        # Para platos no mapeados, crear un mapeo genérico con cualquier ingrediente disponible
        if ingredientes_activos:
            # Tomar el primer ingrediente disponible como genérico
            primer_ingrediente = next(iter(ingredientes_activos.items()))
            ing_id, ing = primer_ingrediente
            ingredientes_plato.append({'ingrediente_id': ing_id, 'cantidad': 1})
    
    return ingredientes_plato

# --- Funciones para Sistema de Anulaciones ---

def crear_solicitud_anulacion(db, orden_id, item_index, motivo, usuario_solicita):
    """
    Crea una solicitud de anulación de producto en una orden
    """
    try:
        import uuid
        from datetime import datetime, timezone
        
        # Crear la solicitud
        solicitud = {
            "_id": f"anulaciones:{uuid.uuid4()}",
            "type": "anulacion_solicitud",
            "orden_id": orden_id,
            "item_index": item_index,
            "motivo": motivo,
            "usuario_solicita": usuario_solicita,
            "estado": "pendiente",  # pendiente, aprobada, rechazada
            "fecha_solicitud": datetime.now(timezone.utc).isoformat(),
            "fecha_procesamiento": None,
            "usuario_procesa": None
        }
        
        db.save(solicitud)
        
        # Marcar el item en la orden como "en proceso de anulación"
        try:
            orden = db[orden_id]
            if item_index < len(orden.get('items', [])):
                orden['items'][item_index]['en_proceso_anulacion'] = True
                orden['items'][item_index]['fecha_solicitud_anulacion'] = datetime.now(timezone.utc).isoformat()
                orden['items'][item_index]['usuario_solicita_anulacion'] = usuario_solicita
                orden['items'][item_index]['solicitud_anulacion_id'] = solicitud['_id']
                db.save(orden)
        except Exception as e:
            # Log del error pero continuar, la solicitud ya fue creada
            log_action(db, usuario_solicita, f"Error al marcar item en proceso: {e}")
        
        log_action(db, usuario_solicita, f"Solicitud de anulación creada para orden {orden_id}")
        return True, solicitud['_id']
        
    except Exception as e:
        return False, str(e)

def obtener_solicitudes_anulacion_pendientes(db):
    """
    Obtiene todas las solicitudes de anulación pendientes
    """
    try:
        solicitudes = get_documents_by_partition(db, "anulaciones")
        pendientes = [s for s in solicitudes if s.get('estado') == 'pendiente']
        return pendientes
    except Exception:
        return []

def procesar_solicitud_anulacion(db, solicitud_id, decision, usuario_admin, motivo_admin=""):
    """
    Procesa una solicitud de anulación (aprobar o rechazar)
    decision: 'aprobada' o 'rechazada'
    """
    try:
        from datetime import datetime, timezone
        
        # Obtener la solicitud
        solicitud = db[solicitud_id]
        if solicitud.get('estado') != 'pendiente':
            return False, "La solicitud ya fue procesada"
        
        # Actualizar solicitud
        solicitud['estado'] = decision
        solicitud['fecha_procesamiento'] = datetime.now(timezone.utc).isoformat()
        solicitud['usuario_procesa'] = usuario_admin
        if motivo_admin:
            solicitud['motivo_admin'] = motivo_admin
        
        if decision == 'aprobada':
            # Procesar la anulación del producto
            success, message = ejecutar_anulacion_producto(
                db, 
                solicitud['orden_id'], 
                solicitud['item_index'], 
                usuario_admin
            )
            
            if not success:
                return False, f"Error al ejecutar anulación: {message}"
        
        elif decision == 'rechazada':
            # Marcar como anulación rechazada para que el mesero vea el feedback
            try:
                orden = db[solicitud['orden_id']]
                item_index = solicitud['item_index']
                if item_index < len(orden.get('items', [])):
                    item = orden['items'][item_index]
                    
                    # Limpiar estado de "en proceso de anulación"
                    if 'en_proceso_anulacion' in item:
                        del item['en_proceso_anulacion']
                    
                    # Marcar como rechazada para mostrar al mesero
                    item['anulacion_rechazada'] = True
                    item['fecha_rechazo_anulacion'] = datetime.now(timezone.utc).isoformat()
                    item['usuario_rechaza_anulacion'] = usuario_admin
                    item['motivo_rechazo_anulacion'] = motivo_admin if motivo_admin else "Sin motivo especificado"
                    item['solicitud_original_anulacion'] = solicitud.get('motivo', 'Sin motivo')
                    
                    # Mantener info de quien solicitó originalmente
                    # (se mantendrán los campos: fecha_solicitud_anulacion, usuario_solicita_anulacion, solicitud_anulacion_id)
                    
                    db.save(orden)
            except Exception as e:
                log_action(db, usuario_admin, f"Error al marcar rechazo: {e}")
        
        # Guardar solicitud actualizada
        db.save(solicitud)
        
        # Log de la acción
        accion = "aprobada" if decision == 'aprobada' else "rechazada"
        log_action(db, usuario_admin, f"Solicitud de anulación {accion}: {solicitud_id}")
        
        return True, f"Solicitud {accion} exitosamente"
        
    except Exception as e:
        return False, str(e)

def ejecutar_anulacion_producto(db, orden_id, item_index, usuario_admin):
    """
    Ejecuta la anulación de un producto: marca como anulado y revierte inventario
    """
    try:
        from datetime import datetime, timezone
        
        # Obtener la orden
        orden = db[orden_id]
        
        if item_index >= len(orden.get('items', [])):
            return False, "Índice de producto inválido"
        
        item = orden['items'][item_index]
        
        # Marcar el item como anulado y limpiar estado de proceso
        item['anulado'] = True
        item['fecha_anulacion'] = datetime.now(timezone.utc).isoformat()
        item['usuario_anula'] = usuario_admin
        
        # Limpiar estado de "en proceso de anulación"
        if 'en_proceso_anulacion' in item:
            del item['en_proceso_anulacion']
        if 'fecha_solicitud_anulacion' in item:
            del item['fecha_solicitud_anulacion']
        if 'usuario_solicita_anulacion' in item:
            del item['usuario_solicita_anulacion']
        if 'solicitud_anulacion_id' in item:
            del item['solicitud_anulacion_id']
        
        # Revertir inventario si el plato usa ingredientes
        platos = get_documents_by_partition(db, "platos")
        plato = next((p for p in platos if p.get('descripcion') == item.get('nombre')), None)
        
        if plato and plato.get('usa_ingrediente', 0) == 1:
            # Revertir movimientos de inventario
            ingredientes = get_documents_by_partition(db, "ingredientes")
            ingredientes_activos = {ing['_id']: ing for ing in ingredientes if ing.get('activo', 0) == 1}
            ingredientes_plato = obtener_ingredientes_por_plato(plato, ingredientes_activos)
            
            for ingrediente_info in ingredientes_plato:
                ingrediente_id = ingrediente_info['ingrediente_id']
                cantidad_a_revertir = ingrediente_info['cantidad'] * item.get('cantidad', 1)
                
                # 1. Crear movimiento de inventario de reversión (entrada)
                import uuid
                movimiento = {
                    "_id": f"inventario:{uuid.uuid4()}",
                    "type": "inventario", 
                    "ingrediente_id": ingrediente_id,
                    "tipo": "entrada",
                    "cantidad": cantidad_a_revertir,  # Positivo para entradas
                    "motivo": f"Reversión por anulación - {item.get('nombre', 'producto')}",
                    "usuario": usuario_admin,
                    "orden_relacionada": orden_id,
                    "fecha_creacion": datetime.now(timezone.utc).isoformat()
                }
                db.save(movimiento)
                
                # 2. Actualizar cantidad física en ingredientes
                try:
                    ingrediente_doc = db[ingrediente_id]
                    cantidad_actual = float(ingrediente_doc.get('cantidad', 0))
                    nueva_cantidad = cantidad_actual + cantidad_a_revertir
                    ingrediente_doc['cantidad'] = nueva_cantidad
                    db.save(ingrediente_doc)
                except Exception as e:
                    # Log del error pero continuar con otros ingredientes
                    log_action(db, usuario_admin, f"Error al revertir ingrediente {ingrediente_id}: {e}")
        
        # Recalcular total de la orden (excluyendo items anulados)
        nuevo_total = sum(
            i['precio_unitario'] * i['cantidad'] 
            for i in orden['items'] 
            if not i.get('anulado', False)
        )
        orden['total'] = nuevo_total
        
        # Guardar orden actualizada
        db.save(orden)
        
        # Log de la anulación
        log_action(db, usuario_admin, f"Producto '{item.get('nombre', 'N/A')}' anulado en orden {orden_id}")
        
        return True, "Producto anulado exitosamente"
        
    except Exception as e:
        return False, str(e)

def marcar_rechazo_como_visto(db, orden_id, item_index, usuario):
    """
    Marca un rechazo de anulación como visto por el mesero, limpiando la notificación
    """
    try:
        orden = db[orden_id]
        
        if item_index >= len(orden.get('items', [])):
            return False, "Índice de producto inválido"
        
        item = orden['items'][item_index]
        
        # Limpiar todos los campos de rechazo
        if 'anulacion_rechazada' in item:
            del item['anulacion_rechazada']
        if 'fecha_rechazo_anulacion' in item:
            del item['fecha_rechazo_anulacion']
        if 'usuario_rechaza_anulacion' in item:
            del item['usuario_rechaza_anulacion']
        if 'motivo_rechazo_anulacion' in item:
            del item['motivo_rechazo_anulacion']
        if 'solicitud_original_anulacion' in item:
            del item['solicitud_original_anulacion']
        if 'fecha_solicitud_anulacion' in item:
            del item['fecha_solicitud_anulacion']
        if 'usuario_solicita_anulacion' in item:
            del item['usuario_solicita_anulacion']
        if 'solicitud_anulacion_id' in item:
            del item['solicitud_anulacion_id']
        
        # Guardar orden actualizada
        db.save(orden)
        
        # Log de la acción
        log_action(db, usuario, f"Notificación de rechazo marcada como vista para orden {orden_id}")
        
        return True, "Notificación marcada como vista"
        
    except Exception as e:
        return False, str(e)

def crear_solicitud_anulacion_orden_completa(db, orden_id, motivo, usuario_solicita):
    """
    Crea una solicitud de anulación para una orden completa
    """
    try:
        orden = db[orden_id]
        
        # Verificar que la orden esté en estado válido para anulación
        if orden.get('estado') not in ['pendiente']:
            return False, "La orden no está en un estado válido para anulación"
        
        # Verificar si ya hay una solicitud pendiente para esta orden
        if orden.get('solicitud_anulacion_completa_pendiente', False):
            return False, "Ya existe una solicitud de anulación pendiente para esta orden"
        
        # Crear documento de solicitud de anulación completa
        solicitud_id = f"solicitud_anulacion_completa:{str(uuid.uuid4())}"
        solicitud_doc = {
            "_id": solicitud_id,
            "type": "solicitud_anulacion_completa",
            "orden_id": orden_id,
            "numero_orden": orden.get('numero_orden'),
            "mesa_id": orden.get('mesa_id'),
            "mesero_id": orden.get('mesero_id'),
            "total_orden": orden.get('total', 0),
            "items_count": len(orden.get('items', [])),
            "motivo": motivo,
            "usuario_solicita": usuario_solicita,
            "fecha_solicitud": datetime.now(timezone.utc).isoformat(),
            "estado": "pendiente",
            "procesada": False
        }
        
        # Guardar solicitud
        db.save(solicitud_doc)
        
        # Marcar la orden como con solicitud pendiente
        orden['solicitud_anulacion_completa_pendiente'] = True
        orden['solicitud_anulacion_completa_id'] = solicitud_id
        orden['fecha_solicitud_anulacion_completa'] = datetime.now(timezone.utc).isoformat()
        orden['usuario_solicita_anulacion_completa'] = usuario_solicita
        orden['motivo_solicitud_anulacion_completa'] = motivo
        
        # Guardar orden actualizada
        db.save(orden)
        
        # Log de la solicitud
        log_action(db, usuario_solicita, f"Solicitó anulación completa de orden #{orden.get('numero_orden')}")
        
        return True, "Solicitud de anulación completa creada exitosamente"
        
    except Exception as e:
        return False, str(e)

def get_documents_by_type(db, document_type):
    """
    Obtiene todos los documentos de un tipo específico de la base de datos
    """
    try:
        # Usar vista para obtener todos los documentos
        docs = []
        for doc_id in db:
            if not doc_id.startswith('_'):  # Evitar documentos de diseño
                try:
                    doc = db[doc_id]
                    if doc.get('type') == document_type:
                        docs.append(doc)
                except:
                    continue
        return docs
    except Exception as e:
        print(f"Error al obtener documentos por tipo {document_type}: {e}")
        return []

def obtener_solicitudes_anulacion_completa_pendientes(db):
    """
    Obtiene todas las solicitudes de anulación completa pendientes
    """
    try:
        # Obtener solicitudes por tipo
        solicitudes = get_documents_by_type(db, "solicitud_anulacion_completa")
        
        # Filtrar solo las pendientes
        solicitudes_pendientes = [s for s in solicitudes if not s.get('procesada', False)]
        
        return solicitudes_pendientes
    except Exception as e:
        print(f"Error al obtener solicitudes de anulación completa: {e}")
        return []

def procesar_solicitud_anulacion_completa(db, solicitud_id, decision, usuario_admin, motivo_admin=""):
    """
    Procesa una solicitud de anulación completa (aprobar o rechazar)
    decision: 'aprobar' o 'rechazar'
    """
    try:
        # Obtener solicitud
        solicitud = db[solicitud_id]
        orden = db[solicitud['orden_id']]
        
        if solicitud.get('procesada', False):
            return False, "Esta solicitud ya ha sido procesada"
        
        # Marcar solicitud como procesada
        solicitud['procesada'] = True
        solicitud['decision'] = decision
        solicitud['usuario_admin'] = usuario_admin
        solicitud['motivo_admin'] = motivo_admin
        solicitud['fecha_decision'] = datetime.now(timezone.utc).isoformat()
        
        if decision == 'aprobar':
            # Ejecutar la anulación completa
            success, message = ejecutar_anulacion_orden_completa(db, solicitud['orden_id'], usuario_admin)
            
            if success:
                solicitud['anulacion_ejecutada'] = True
                db.save(solicitud)
                return True, f"Anulación completa ejecutada exitosamente: {message}"
            else:
                return False, f"Error al ejecutar anulación: {message}"
        
        else:  # rechazar
            # Marcar rechazo en la orden
            orden['solicitud_anulacion_completa_pendiente'] = False
            orden['anulacion_completa_rechazada'] = True
            orden['fecha_rechazo_anulacion_completa'] = datetime.now(timezone.utc).isoformat()
            orden['usuario_rechaza_anulacion_completa'] = usuario_admin
            orden['motivo_rechazo_anulacion_completa'] = motivo_admin
            
            # Guardar cambios
            db.save(solicitud)
            db.save(orden)
            
            # Log del rechazo
            log_action(db, usuario_admin, f"Rechazó anulación completa de orden #{orden.get('numero_orden')}")
            
            return True, "Solicitud de anulación rechazada"
        
    except Exception as e:
        return False, str(e)

def ejecutar_anulacion_orden_completa(db, orden_id, usuario_admin):
    """
    Ejecuta la anulación completa de una orden, revirtiendo inventario
    """
    try:
        orden = db[orden_id]
        
        if orden.get('estado') == 'anulada':
            return False, "La orden ya está anulada"
        
        # Obtener datos necesarios para reversión de inventario
        platos = {p['_id']: p for p in get_documents_by_partition(db, "platos")}
        ingredientes = {i['_id']: i for i in get_documents_by_partition(db, "ingredientes")}
        
        items_revertidos = []
        
        # Revertir inventario para cada item no anulado
        for item in orden.get('items', []):
            if not item.get('anulado', False):
                plato_id = item.get('plato_id')
                cantidad = item.get('cantidad', 0)
                
                if plato_id in platos:
                    plato = platos[plato_id]
                    
                    # Revertir ingredientes del plato
                    for ingrediente_info in plato.get('ingredientes', []):
                        ingrediente_id = ingrediente_info.get('ingrediente_id')
                        cantidad_por_plato = ingrediente_info.get('cantidad', 0)
                        cantidad_total_revertir = cantidad_por_plato * cantidad
                        
                        if ingrediente_id in ingredientes:
                            # Crear movimiento de inventario de reversión
                            movimiento_doc = {
                                "_id": f"inventario:{str(uuid.uuid4())}",
                                "type": "inventario",
                                "ingrediente_id": ingrediente_id,
                                "tipo": "entrada",
                                "cantidad": cantidad_total_revertir,
                                "motivo": f"Reversión por anulación completa - Orden #{orden.get('numero_orden')}",
                                "comentarios": f"Anulación completa de orden. Item: {item.get('nombre', 'N/A')}",
                                "fecha_creacion": datetime.now(timezone.utc).isoformat(),
                                "usuario": usuario_admin,
                                "orden_referencia": orden_id
                            }
                            
                            # Guardar movimiento
                            db.save(movimiento_doc)
                            
                            items_revertidos.append({
                                "item_nombre": item.get('nombre', 'N/A'),
                                "ingrediente_id": ingrediente_id,
                                "cantidad_revertida": cantidad_total_revertir
                            })
        
        # Cambiar estado de la orden
        orden['estado'] = 'anulada'
        orden['fecha_anulacion_completa'] = datetime.now(timezone.utc).isoformat()
        orden['usuario_anula_completa'] = usuario_admin
        orden['items_revertidos_inventario'] = items_revertidos
        
        # Limpiar campos de solicitud pendiente
        if 'solicitud_anulacion_completa_pendiente' in orden:
            del orden['solicitud_anulacion_completa_pendiente']
        if 'anulacion_completa_rechazada' in orden:
            del orden['anulacion_completa_rechazada']
        
        # Guardar orden actualizada
        db.save(orden)
        
        # Log de la anulación
        log_action(db, usuario_admin, f"Ejecutó anulación completa de orden #{orden.get('numero_orden')} - {len(items_revertidos)} items revertidos al inventario")
        
        return True, f"Orden anulada completamente. {len(items_revertidos)} items revertidos al inventario"
        
    except Exception as e:
        return False, str(e)

def marcar_rechazo_anulacion_completa_como_visto(db, orden_id, usuario):
    """
    Marca un rechazo de anulación completa como visto por el mesero
    """
    try:
        orden = db[orden_id]
        
        # Limpiar campos de rechazo
        if 'anulacion_completa_rechazada' in orden:
            del orden['anulacion_completa_rechazada']
        if 'fecha_rechazo_anulacion_completa' in orden:
            del orden['fecha_rechazo_anulacion_completa']
        if 'usuario_rechaza_anulacion_completa' in orden:
            del orden['usuario_rechaza_anulacion_completa']
        if 'motivo_rechazo_anulacion_completa' in orden:
            del orden['motivo_rechazo_anulacion_completa']
        if 'solicitud_anulacion_completa_id' in orden:
            del orden['solicitud_anulacion_completa_id']
        if 'fecha_solicitud_anulacion_completa' in orden:
            del orden['fecha_solicitud_anulacion_completa']
        if 'usuario_solicita_anulacion_completa' in orden:
            del orden['usuario_solicita_anulacion_completa']
        if 'motivo_solicitud_anulacion_completa' in orden:
            del orden['motivo_solicitud_anulacion_completa']
        
        # Guardar orden actualizada
        db.save(orden)
        
        # Log de la acción
        log_action(db, usuario, f"Notificación de rechazo de anulación completa marcada como vista para orden #{orden.get('numero_orden')}")
        
        return True, "Notificación marcada como vista"
        
    except Exception as e:
        return False, str(e)

# Wrapper functions for ordenes_activas.py compatibility
def aprobar_anulacion(db, solicitud_id, usuario_admin):
    """
    Wrapper function to approve a product cancellation request
    """
    return procesar_solicitud_anulacion(db, solicitud_id, 'aprobada', usuario_admin)

def rechazar_anulacion(db, solicitud_id, motivo, usuario_admin):
    """
    Wrapper function to reject a product cancellation request
    """
    return procesar_solicitud_anulacion(db, solicitud_id, 'rechazada', usuario_admin, motivo)

def aprobar_anulacion_orden_completa(db, orden_id, usuario_admin):
    """
    Wrapper function to approve a complete order cancellation request
    """
    # First, find the pending cancellation request for this order
    try:
        orden = db[orden_id]
        solicitud_id = orden.get('solicitud_anulacion_completa_id')
        if not solicitud_id:
            return False, "No hay solicitud de anulación pendiente para esta orden"
        
        return procesar_solicitud_anulacion_completa(db, solicitud_id, 'aprobada', usuario_admin)
    except Exception as e:
        return False, str(e)

def rechazar_anulacion_orden_completa(db, orden_id, motivo, usuario_admin):
    """
    Wrapper function to reject a complete order cancellation request
    """
    # First, find the pending cancellation request for this order
    try:
        orden = db[orden_id]
        solicitud_id = orden.get('solicitud_anulacion_completa_id')
        if not solicitud_id:
            return False, "No hay solicitud de anulación pendiente para esta orden"
        
        return procesar_solicitud_anulacion_completa(db, solicitud_id, 'rechazada', usuario_admin, motivo)
    except Exception as e:
        return False, str(e)
