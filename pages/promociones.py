# pages/promociones.py
import streamlit as st
from datetime import datetime, timezone, timedelta
import couchdb_utils
import os
import uuid

# Configuracion basica
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))
CURRENT_PARTITION_KEY = "promociones"
couchdb_utils.generarLogin(archivo_actual_relativo)
st.set_page_config(layout="wide", page_title="Gestion de Promociones", page_icon="../assets/LOGO.png")

# Estilos CSS
st.markdown("""
<style>
    .promo-card {
        border: 2px solid #ffd700;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .promo-active {
        border-color: #28a745;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    }
    
    .promo-expired {
        border-color: #dc3545;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        opacity: 0.7;
    }
    
    .promo-programmed {
        border-color: #17a2b8;
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
    }
    
    .discount-badge {
        background: #ff6b6b;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.8em;
    }
    
    .price-original {
        text-decoration: line-through;
        color: #6c757d;
        font-size: 0.9em;
    }
    
    .price-promo {
        color: #28a745;
        font-weight: bold;
        font-size: 1.1em;
    }
    
    .status-active {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-expired {
        color: #dc3545;
        font-weight: bold;
    }
    
    .status-programmed {
        color: #17a2b8;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def calcular_descuento(precio_original, precio_promocion):
    """Calcula el porcentaje de descuento"""
    if precio_original <= 0:
        return 0
    return round(((precio_original - precio_promocion) / precio_original) * 100, 1)

def validar_promociones_activas(db):
    """Valida y actualiza el estado de las promociones segun fecha/hora actual"""
    try:
        promociones = couchdb_utils.get_documents_by_partition(db, "promociones")
        ahora = datetime.now(timezone.utc)
        cambios_realizados = 0
        
        for promo in promociones:
            fecha_inicio = datetime.fromisoformat(promo.get('fecha_inicio', '').replace('Z', '+00:00'))
            fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
            
            # Determinar el nuevo estado
            if ahora < fecha_inicio:
                nuevo_estado = 'programada'
            elif fecha_inicio <= ahora <= fecha_fin:
                nuevo_estado = 'activa'
            else:
                nuevo_estado = 'vencida'
            
            # Actualizar si el estado cambio
            if promo.get('estado') != nuevo_estado:
                promo['estado'] = nuevo_estado
                promo['fecha_actualizacion'] = ahora.isoformat()
                db.save(promo)
                cambios_realizados += 1
        
        return cambios_realizados
    except Exception as e:
        st.error(f"Error validando promociones: {str(e)}")
        return 0

def obtener_productos_ventas(db):
    """Obtiene los productos de ventas disponibles (platos activos)"""
    try:
        # Los productos de ventas son los platos activos
        platos = couchdb_utils.get_documents_by_partition(db, "platos")
        productos_activos = []
        
        for plato in platos:
            if plato.get('activo', 0) == 1:
                productos_activos.append({
                    '_id': plato['_id'],
                    'nombre': plato.get('descripcion', 'Sin nombre'),
                    'precio_normal': plato.get('precio_normal', 0),
                    'categoria': plato.get('categoria', 'Sin categoria')
                })
        
        return productos_activos
    except Exception as e:
        st.error(f"Error obteniendo productos de ventas: {str(e)}")
        return []

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()
    
    if db:
        # Validar promociones al cargar la pagina
        cambios = validar_promociones_activas(db)
        if cambios > 0:
            st.success(f"✅ Se actualizaron {cambios} promociones automaticamente")
        
        # Titulo principal
        st.title("🎉 Gestion de Promociones")
        st.markdown("Crea y gestiona promociones temporales para el menu del restaurante")
        st.markdown("---")
        
        # Tabs para organizar la interfaz
        tab_crear, tab_gestionar, tab_activas = st.tabs(["➕ Crear Promocion", "📋 Gestionar", "🔥 Activas"])
        
        with tab_crear:
            st.subheader("Crear Nueva Promocion")
            
            # Obtener productos de ventas
            productos_ventas = obtener_productos_ventas(db)
            
            if not productos_ventas:
                st.warning("No hay platos activos disponibles. Ve a 'Platos' para crear y activar algunos platos.")
            else:
                col_producto, col_precios = st.columns([2, 1])
                
                with col_producto:
                    # Selector de producto
                    productos_dict = {p['_id']: f"{p['nombre']} - ${p['precio_normal']:.2f} ({p['categoria']})" 
                                    for p in productos_ventas}
                    
                    producto_seleccionado_id = st.selectbox(
                        "Seleccionar Producto de Ventas:",
                        options=list(productos_dict.keys()),
                        format_func=lambda x: productos_dict[x]
                    )
                    
                    if producto_seleccionado_id:
                        producto_seleccionado = next(p for p in productos_ventas if p['_id'] == producto_seleccionado_id)
                        
                        # Informacion del producto seleccionado
                        st.info(f"**Producto:** {producto_seleccionado['nombre']}\n**Precio Normal:** ${producto_seleccionado['precio_normal']:.2f}")
                
                with col_precios:
                    # Configuracion de precios
                    precio_original = producto_seleccionado['precio_normal'] if 'producto_seleccionado' in locals() else 0
                    
                    precio_promocion = st.number_input(
                        "Precio de Promocion:",
                        min_value=0.01,
                        max_value=float(precio_original) if precio_original > 0 else 100.0,
                        value=float(precio_original * 0.8) if precio_original > 0 else 0.01,
                        step=0.01,
                        help="Debe ser menor al precio normal"
                    )
                    
                    if precio_original > 0:
                        descuento = calcular_descuento(precio_original, precio_promocion)
                        if descuento > 0:
                            st.success(f"💰 Descuento: {descuento}%")
                        else:
                            st.error("❌ El precio de promocion debe ser menor al precio normal")
                
                # Configuracion temporal
                st.subheader("Configuracion Temporal")
                col_fecha1, col_fecha2 = st.columns(2)
                
                with col_fecha1:
                    fecha_inicio = st.date_input(
                        "Fecha de Inicio:",
                        value=datetime.now().date(),
                        min_value=datetime.now().date()
                    )
                    # Redondear a la hora más cercana para mejor UX
                    ahora = datetime.now()
                    if ahora.minute >= 30:
                        hora_redondeada = ahora.replace(hour=ahora.hour + 1, minute=0, second=0, microsecond=0)
                    else:
                        hora_redondeada = ahora.replace(minute=0, second=0, microsecond=0)
                    
                    hora_inicio = st.time_input(
                        "Hora de Inicio:",
                        value=hora_redondeada.time(),
                        help="Puedes seleccionar cualquier hora"
                    )
                
                with col_fecha2:
                    fecha_fin = st.date_input(
                        "Fecha de Finalizacion:",
                        value=datetime.now().date() + timedelta(days=1),
                        min_value=datetime.now().date()
                    )
                    
                    # Opción alternativa: usar selectores separados si time_input no funciona bien
                    use_manual_time = st.checkbox("Usar selector manual de hora", help="Marca esta opción si el selector de hora no te funciona correctamente")
                    
                    if use_manual_time:
                        col_hora, col_min = st.columns(2)
                        with col_hora:
                            hora_num = st.selectbox("Hora:", options=list(range(0, 24)), index=23, format_func=lambda x: f"{x:02d}")
                        with col_min:
                            min_num = st.selectbox("Minutos:", options=list(range(0, 60, 5)), index=11, format_func=lambda x: f"{x:02d}")  # De 5 en 5 minutos
                        
                        hora_fin = datetime.now().replace(hour=hora_num, minute=min_num, second=0, microsecond=0).time()
                        st.info(f"Hora seleccionada: {hora_fin.strftime('%H:%M')}")
                    else:
                        hora_fin = st.time_input(
                            "Hora de Finalizacion:",
                            value=datetime.now().replace(hour=23, minute=59, second=0, microsecond=0).time(),
                            help="Selecciona libremente la hora de finalización"
                        )
                
                # Configuracion adicional
                col_tipo, col_nombre = st.columns(2)
                
                with col_tipo:
                    tipo_menu = st.selectbox(
                        "Tipo de Menu:",
                        options=['promoBar', 'promoCocina'],
                        format_func=lambda x: "🍹 Promociones Bar" if x == 'promoBar' else "🍳 Promociones Cocina"
                    )
                
                with col_nombre:
                    nombre_promocion = st.text_input(
                        "Nombre de la Promocion:",
                        value=f"Promo {producto_seleccionado['nombre']}" if 'producto_seleccionado' in locals() else "",
                        help="Nombre descriptivo para identificar la promocion"
                    )
                
                # Boton de crear
                if st.button("🎉 Crear Promocion", type="primary", use_container_width=True):
                    if 'producto_seleccionado' not in locals():
                        st.error("❌ Debes seleccionar un producto")
                    elif precio_promocion >= precio_original:
                        st.error("❌ El precio de promocion debe ser menor al precio normal")
                    elif not nombre_promocion.strip():
                        st.error("❌ Debes proporcionar un nombre para la promocion")
                    else:
                        # Crear datetime objects
                        dt_inicio = datetime.combine(fecha_inicio, hora_inicio).replace(tzinfo=timezone.utc)
                        dt_fin = datetime.combine(fecha_fin, hora_fin).replace(tzinfo=timezone.utc)
                        
                        if dt_fin <= dt_inicio:
                            st.error("❌ La fecha de finalizacion debe ser posterior a la de inicio")
                        else:
                            # Crear documento de promocion
                            ahora = datetime.now(timezone.utc)
                            
                            # Determinar estado inicial
                            if ahora < dt_inicio:
                                estado = 'programada'
                            elif dt_inicio <= ahora <= dt_fin:
                                estado = 'activa'
                            else:
                                estado = 'vencida'
                            
                            promocion_doc = {
                                "_id": f"promociones:{str(uuid.uuid4())}",
                                "type": "promociones",
                                "plato_id": producto_seleccionado_id,
                                "nombre_producto": producto_seleccionado['nombre'],
                                "nombre_promocion": nombre_promocion.strip(),
                                "precio_original": precio_original,
                                "precio_promocion": precio_promocion,
                                "descuento_porcentaje": calcular_descuento(precio_original, precio_promocion),
                                "fecha_inicio": dt_inicio.isoformat(),
                                "fecha_fin": dt_fin.isoformat(),
                                "tipo_menu": tipo_menu,
                                "estado": estado,
                                "activo": True,
                                "fecha_creacion": ahora.isoformat(),
                                "creado_por": st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                            }
                            
                            try:
                                db.save(promocion_doc)
                                st.success("✅ Promocion creada exitosamente!")
                                
                                # Log de la accion
                                logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                couchdb_utils.log_action(db, logged_in_user, f"Promocion creada: {nombre_promocion}")
                                
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al crear promocion: {str(e)}")
        
        with tab_gestionar:
            st.subheader("Gestionar Promociones")
            
            # Obtener todas las promociones
            promociones = couchdb_utils.get_documents_by_partition(db, "promociones")
            
            if not promociones:
                st.info("No hay promociones creadas aun.")
            else:
                # Filtros
                col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
                
                with col_filtro1:
                    filtro_estado = st.selectbox(
                        "Filtrar por Estado:",
                        options=['todos', 'activa', 'programada', 'vencida'],
                        format_func=lambda x: x.title() if x != 'todos' else 'Todos'
                    )
                
                with col_filtro2:
                    filtro_tipo = st.selectbox(
                        "Filtrar por Tipo:",
                        options=['todos', 'promoBar', 'promoCocina'],
                        format_func=lambda x: 'Todos' if x == 'todos' else ('Bar' if x == 'promoBar' else 'Cocina')
                    )
                
                with col_filtro3:
                    col_actualizar, col_reactivar = st.columns(2)
                    
                    with col_actualizar:
                        if st.button("🔄 Actualizar Estados", help="Validar y actualizar estados de promociones"):
                            cambios = validar_promociones_activas(db)
                            if cambios > 0:
                                st.success(f"✅ {cambios} promociones actualizadas")
                            else:
                                st.info("ℹ️ Todas las promociones estan al dia")
                            st.rerun()
                    
                    with col_reactivar:
                        if st.button("⚡ Reactivar Vencidas", help="Reactivar promociones vencidas extendiéndolas 24 horas", type="secondary"):
                            promociones_vencidas = [p for p in promociones if p.get('estado') == 'vencida']
                            reactivadas = 0
                            
                            for promo in promociones_vencidas:
                                try:
                                    # Extender la promoción por 24 horas desde ahora
                                    ahora = datetime.now(timezone.utc)
                                    nueva_fecha_fin = ahora + timedelta(hours=24)
                                    
                                    promo['fecha_inicio'] = (ahora - timedelta(hours=1)).isoformat()  # Empezó hace 1 hora
                                    promo['fecha_fin'] = nueva_fecha_fin.isoformat()
                                    promo['estado'] = 'activa'
                                    promo['fecha_actualizacion'] = ahora.isoformat()
                                    
                                    db.save(promo)
                                    reactivadas += 1
                                    
                                except Exception as e:
                                    st.error(f"Error reactivando {promo.get('nombre_promocion', 'promoción')}: {str(e)}")
                            
                            if reactivadas > 0:
                                st.success(f"✅ {reactivadas} promociones reactivadas por 24 horas")
                                st.rerun()
                            else:
                                st.info("ℹ️ No hay promociones vencidas para reactivar")
                
                # Filtrar promociones
                promociones_filtradas = promociones
                
                if filtro_estado != 'todos':
                    promociones_filtradas = [p for p in promociones_filtradas if p.get('estado') == filtro_estado]
                
                if filtro_tipo != 'todos':
                    promociones_filtradas = [p for p in promociones_filtradas if p.get('tipo_menu') == filtro_tipo]
                
                # Ordenar por fecha de creacion (mas recientes primero)
                promociones_filtradas.sort(key=lambda x: x.get('fecha_creacion', ''), reverse=True)
                
                st.write(f"**Mostrando {len(promociones_filtradas)} de {len(promociones)} promociones**")
                
                # Mostrar promociones
                for promo in promociones_filtradas:
                    estado = promo.get('estado', 'desconocido')
                    
                    # Determinar clase CSS
                    if estado == 'activa':
                        card_class = "promo-card promo-active"
                        status_class = "status-active"
                        emoji_estado = "🟢"
                    elif estado == 'vencida':
                        card_class = "promo-card promo-expired"
                        status_class = "status-expired"
                        emoji_estado = "🔴"
                    elif estado == 'programada':
                        card_class = "promo-card promo-programmed"
                        status_class = "status-programmed"
                        emoji_estado = "🔵"
                    else:
                        card_class = "promo-card"
                        status_class = ""
                        emoji_estado = "⚪"
                    
                    # Card de promocion usando elementos nativos de Streamlit
                    with st.container():
                        # Encabezado con emoji y nombre
                        col_header, col_badge = st.columns([4, 1])
                        with col_header:
                            st.markdown(f"### {emoji_estado} {promo.get('nombre_promocion', 'Sin nombre')}")
                            st.caption(f"📦 {promo.get('nombre_producto', 'Producto desconocido')}")
                        
                        with col_badge:
                            if promo.get('descuento_porcentaje', 0) > 0:
                                st.markdown(f"<div style='background: #ff6b6b; color: white; padding: 5px 10px; border-radius: 20px; text-align: center; font-weight: bold;'>-{promo.get('descuento_porcentaje', 0)}%</div>", unsafe_allow_html=True)
                        
                        # Información de precios y estado
                        col_precio, col_tipo, col_estado = st.columns([2, 1, 1])
                        
                        with col_precio:
                            precio_original = promo.get('precio_original', 0)
                            precio_promo = promo.get('precio_promocion', 0)
                            st.markdown(f"~~${precio_original:.2f}~~ **${precio_promo:.2f}**")
                        
                        with col_tipo:
                            tipo_display = promo.get('tipo_menu', '').replace('promo', '').title()
                            st.write(f"📋 {tipo_display}")
                        
                        with col_estado:
                            if estado == 'activa':
                                st.success(f"🟢 {estado.title()}")
                            elif estado == 'vencida':
                                st.error(f"🔴 {estado.title()}")
                            elif estado == 'programada':
                                st.info(f"🔵 {estado.title()}")
                            else:
                                st.write(f"⚪ {estado.title()}")
                        
                        # Fechas
                        try:
                            fecha_inicio_str = datetime.fromisoformat(promo.get('fecha_inicio', '').replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                            fecha_fin_str = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00')).strftime('%d/%m/%Y %H:%M')
                            st.caption(f"📅 {fecha_inicio_str} - {fecha_fin_str}")
                        except:
                            st.caption("📅 Fechas no disponibles")
                        
                        # Botones de accion
                        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                        
                        with col_btn1:
                            if st.button("✏️ Editar", key=f"edit_{promo['_id']}", help="Editar promocion"):
                                st.session_state[f"editing_{promo['_id']}"] = True
                                st.rerun()
                        
                        with col_btn2:
                            activo_texto = "🔴 Desactivar" if promo.get('activo', True) else "🟢 Activar"
                            if st.button(activo_texto, key=f"toggle_{promo['_id']}", help="Activar/Desactivar promocion"):
                                promo['activo'] = not promo.get('activo', True)
                                promo['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
                                db.save(promo)
                                st.success("✅ Estado actualizado")
                                st.rerun()
                        
                        with col_btn3:
                            if st.button("🗂️ Duplicar", key=f"duplicate_{promo['_id']}", help="Crear copia de esta promocion"):
                                # Crear copia con nuevo ID y fechas
                                nueva_promo = promo.copy()
                                nueva_promo['_id'] = f"promociones:{str(uuid.uuid4())}"
                                nueva_promo['nombre_promocion'] = f"Copia de {promo.get('nombre_promocion', 'Promocion')}"
                                nueva_promo['fecha_creacion'] = datetime.now(timezone.utc).isoformat()
                                nueva_promo['estado'] = 'programada'
                                # Establecer fechas para el dia siguiente
                                maniana = datetime.now() + timedelta(days=1)
                                nueva_promo['fecha_inicio'] = maniana.replace(tzinfo=timezone.utc).isoformat()
                                nueva_promo['fecha_fin'] = (maniana + timedelta(hours=2)).replace(tzinfo=timezone.utc).isoformat()
                                
                                db.save(nueva_promo)
                                st.success("✅ Promocion duplicada")
                                st.rerun()
                        
                        with col_btn4:
                            if st.button("🗑️ Eliminar", key=f"delete_{promo['_id']}", help="Eliminar promocion"):
                                if st.session_state.get(f"confirm_delete_{promo['_id']}", False):
                                    db.delete(promo)
                                    st.success("✅ Promocion eliminada")
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{promo['_id']}"] = True
                                    st.warning("⚠️ Haz clic nuevamente para confirmar eliminacion")
                        
                        # Modal de edicion
                        if st.session_state.get(f"editing_{promo['_id']}", False):
                            with st.expander(f"✏️ Editando: {promo.get('nombre_promocion', 'Promocion')}", expanded=True):
                                # Formulario de edicion
                                nuevo_nombre = st.text_input(
                                    "Nombre:",
                                    value=promo.get('nombre_promocion', ''),
                                    key=f"edit_name_{promo['_id']}"
                                )
                                
                                col_edit1, col_edit2 = st.columns(2)
                                
                                with col_edit1:
                                    nuevo_precio = st.number_input(
                                        "Precio Promocion:",
                                        min_value=0.01,
                                        value=float(promo.get('precio_promocion', 0)),
                                        step=0.01,
                                        key=f"edit_price_{promo['_id']}"
                                    )
                                
                                with col_edit2:
                                    nuevo_tipo = st.selectbox(
                                        "Tipo de Menu:",
                                        options=['promoBar', 'promoCocina'],
                                        index=0 if promo.get('tipo_menu') == 'promoBar' else 1,
                                        key=f"edit_type_{promo['_id']}"
                                    )
                                
                                # Seccion de fechas y horas
                                st.markdown("**📅 Fechas y Horas:**")
                                col_fecha_edit1, col_fecha_edit2 = st.columns(2)
                                
                                # Parsear fechas existentes y convertir a hora local para edición
                                try:
                                    fecha_inicio_utc = datetime.fromisoformat(promo.get('fecha_inicio', '').replace('Z', '+00:00'))
                                    fecha_fin_utc = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                                    
                                    # Convertir de UTC a hora local para mostrar en la UI
                                    fecha_inicio_actual = fecha_inicio_utc.astimezone()
                                    fecha_fin_actual = fecha_fin_utc.astimezone()
                                except:
                                    # Si hay error, usar valores por defecto en hora local
                                    fecha_inicio_actual = datetime.now()
                                    fecha_fin_actual = datetime.now() + timedelta(hours=6)  # 6 horas en lugar de 24
                                
                                with col_fecha_edit1:
                                    nueva_fecha_inicio = st.date_input(
                                        "Nueva Fecha Inicio:",
                                        value=fecha_inicio_actual.date(),
                                        key=f"edit_fecha_inicio_{promo['_id']}"
                                    )
                                    nueva_hora_inicio = st.time_input(
                                        "Nueva Hora Inicio:",
                                        value=fecha_inicio_actual.time(),
                                        key=f"edit_hora_inicio_{promo['_id']}"
                                    )
                                
                                with col_fecha_edit2:
                                    nueva_fecha_fin = st.date_input(
                                        "Nueva Fecha Fin:",
                                        value=fecha_fin_actual.date(),
                                        min_value=nueva_fecha_inicio,
                                        key=f"edit_fecha_fin_{promo['_id']}"
                                    )
                                    nueva_hora_fin = st.time_input(
                                        "Nueva Hora Fin:",
                                        value=fecha_fin_actual.time(),
                                        key=f"edit_hora_fin_{promo['_id']}"
                                    )
                                
                                # Crear datetime objects - simplificado para evitar problemas de zona horaria
                                # Asumir que las fechas/horas ingresadas son en la zona horaria local del servidor
                                nuevo_dt_inicio = datetime.combine(nueva_fecha_inicio, nueva_hora_inicio).replace(tzinfo=timezone.utc)
                                nuevo_dt_fin = datetime.combine(nueva_fecha_fin, nueva_hora_fin).replace(tzinfo=timezone.utc)
                                
                                # Para mejor UX, mostrar el estado comparando con hora local
                                ahora_edit_local = datetime.now()
                                nuevo_dt_inicio_local = nuevo_dt_inicio.replace(tzinfo=None)
                                nuevo_dt_fin_local = nuevo_dt_fin.replace(tzinfo=None)
                                
                                if ahora_edit_local < nuevo_dt_inicio_local:
                                    nuevo_estado_preview = "🔵 Programada"
                                elif nuevo_dt_inicio_local <= ahora_edit_local <= nuevo_dt_fin_local:
                                    nuevo_estado_preview = "🟢 Activa"
                                else:
                                    nuevo_estado_preview = "🔴 Vencida"
                                
                                # Mostrar preview con las fechas locales para mejor comprensión
                                st.info(f"**Vista previa:** {nuevo_dt_inicio_local.strftime('%d/%m/%Y %H:%M')} - {nuevo_dt_fin_local.strftime('%d/%m/%Y %H:%M')} → {nuevo_estado_preview}")
                                
                                if nuevo_dt_fin_local <= nuevo_dt_inicio_local:
                                    st.error("❌ La fecha de fin debe ser posterior a la de inicio")
                                
                                # Botones rápidos de activación
                                st.markdown("**⚡ Activación Rápida:**")
                                
                                # Primera fila: Activaciones cortas
                                col_30m, col_1h, col_2h, col_3h, col_4h = st.columns(5)
                                
                                with col_30m:
                                    if st.button("30min", key=f"quick_30m_{promo['_id']}", help="Activar por 30 minutos", use_container_width=True):
                                        ahora_quick = datetime.now(timezone.utc)
                                        fin_quick = ahora_quick + timedelta(minutes=30)
                                        
                                        # Actualizar la promoción
                                        promo['fecha_inicio'] = ahora_quick.isoformat()
                                        promo['fecha_fin'] = fin_quick.isoformat()
                                        promo['estado'] = 'activa'
                                        promo['activo'] = True
                                        promo['fecha_actualizacion'] = ahora_quick.isoformat()
                                        
                                        db.save(promo)
                                        st.success("⚡ Promoción activada por 30 minutos")
                                        st.rerun()
                                
                                with col_1h:
                                    if st.button("1 hora", key=f"quick_1h_{promo['_id']}", help="Activar por 1 hora", use_container_width=True):
                                        ahora_quick = datetime.now(timezone.utc)
                                        fin_quick = ahora_quick + timedelta(hours=1)
                                        
                                        promo['fecha_inicio'] = ahora_quick.isoformat()
                                        promo['fecha_fin'] = fin_quick.isoformat()
                                        promo['estado'] = 'activa'
                                        promo['activo'] = True
                                        promo['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
                                        
                                        db.save(promo)
                                        st.success("⚡ Promoción activada por 1 hora")
                                        st.rerun()
                                
                                with col_2h:
                                    if st.button("2 horas", key=f"quick_2h_{promo['_id']}", help="Activar por 2 horas", use_container_width=True):
                                        ahora_quick = datetime.now(timezone.utc)
                                        fin_quick = ahora_quick + timedelta(hours=2)
                                        
                                        promo['fecha_inicio'] = ahora_quick.isoformat()
                                        promo['fecha_fin'] = fin_quick.isoformat()
                                        promo['estado'] = 'activa'
                                        promo['activo'] = True
                                        promo['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
                                        
                                        db.save(promo)
                                        st.success("⚡ Promoción activada por 2 horas")
                                        st.rerun()
                                
                                with col_3h:
                                    if st.button("3 horas", key=f"quick_3h_{promo['_id']}", help="Activar por 3 horas", use_container_width=True):
                                        ahora_quick = datetime.now(timezone.utc)
                                        fin_quick = ahora_quick + timedelta(hours=3)
                                        
                                        promo['fecha_inicio'] = ahora_quick.isoformat()
                                        promo['fecha_fin'] = fin_quick.isoformat()
                                        promo['estado'] = 'activa'
                                        promo['activo'] = True
                                        promo['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
                                        
                                        db.save(promo)
                                        st.success("⚡ Promoción activada por 3 horas")
                                        st.rerun()
                                
                                with col_4h:
                                    if st.button("4 horas", key=f"quick_4h_{promo['_id']}", help="Activar por 4 horas", use_container_width=True):
                                        ahora_quick = datetime.now(timezone.utc)
                                        fin_quick = ahora_quick + timedelta(hours=4)
                                        
                                        promo['fecha_inicio'] = ahora_quick.isoformat()
                                        promo['fecha_fin'] = fin_quick.isoformat()
                                        promo['estado'] = 'activa'
                                        promo['activo'] = True
                                        promo['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
                                        
                                        db.save(promo)
                                        st.success("⚡ Promoción activada por 4 horas")
                                        st.rerun()
                                
                                # Segunda fila: Activaciones largas y desactivar
                                col_1d, col_desactivar, col_space1, col_space2, col_space3 = st.columns(5)
                                
                                with col_1d:
                                    if st.button("1 día", key=f"quick_1d_{promo['_id']}", help="Activar por 1 día completo", use_container_width=True):
                                        ahora_quick = datetime.now(timezone.utc)
                                        fin_quick = ahora_quick + timedelta(days=1)
                                        
                                        promo['fecha_inicio'] = ahora_quick.isoformat()
                                        promo['fecha_fin'] = fin_quick.isoformat()
                                        promo['estado'] = 'activa'
                                        promo['activo'] = True
                                        promo['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
                                        
                                        db.save(promo)
                                        st.success("⚡ Promoción activada por 1 día")
                                        st.rerun()
                                
                                with col_desactivar:
                                    if st.button("🔴 Desactivar", key=f"quick_deactivate_{promo['_id']}", help="Desactivar promoción (finalizar ahora)", use_container_width=True):
                                        ahora_quick = datetime.now(timezone.utc)
                                        fin_quick = ahora_quick - timedelta(minutes=1)
                                        
                                        promo['fecha_fin'] = fin_quick.isoformat()
                                        promo['estado'] = 'vencida'
                                        promo['fecha_actualizacion'] = ahora_quick.isoformat()
                                        
                                        db.save(promo)
                                        st.warning("🔴 Promoción desactivada - Finalizada hace 1 minuto")
                                        st.rerun()
                                
                                col_save, col_cancel = st.columns(2)
                                
                                with col_save:
                                    if st.button("💾 Guardar", key=f"save_{promo['_id']}", type="primary"):
                                        # Validaciones
                                        validaciones_ok = True
                                        
                                        if nuevo_precio >= promo.get('precio_original', 0):
                                            st.error("❌ El precio debe ser menor al original")
                                            validaciones_ok = False
                                        
                                        if nuevo_dt_fin_local <= nuevo_dt_inicio_local:
                                            st.error("❌ La fecha de fin debe ser posterior a la de inicio")
                                            validaciones_ok = False
                                        
                                        if validaciones_ok:
                                            # Determinar nuevo estado basado en las nuevas fechas (usar misma lógica que preview)
                                            ahora_save = datetime.now()  # Hora local para consistencia
                                            if ahora_save < nuevo_dt_inicio_local:
                                                nuevo_estado = 'programada'
                                            elif nuevo_dt_inicio_local <= ahora_save <= nuevo_dt_fin_local:
                                                nuevo_estado = 'activa'
                                            else:
                                                nuevo_estado = 'vencida'
                                            
                                            # Actualizar todos los campos
                                            promo['nombre_promocion'] = nuevo_nombre
                                            promo['precio_promocion'] = nuevo_precio
                                            promo['tipo_menu'] = nuevo_tipo
                                            promo['fecha_inicio'] = nuevo_dt_inicio.isoformat()
                                            promo['fecha_fin'] = nuevo_dt_fin.isoformat()
                                            promo['estado'] = nuevo_estado
                                            promo['descuento_porcentaje'] = calcular_descuento(
                                                promo.get('precio_original', 0), nuevo_precio
                                            )
                                            promo['fecha_actualizacion'] = datetime.now(timezone.utc).isoformat()
                                            
                                            try:
                                                db.save(promo)
                                                estado_msg = {"programada": "🔵 Programada", "activa": "🟢 Activa", "vencida": "🔴 Vencida"}.get(nuevo_estado, nuevo_estado)
                                                st.success(f"✅ Promocion actualizada - Estado: {estado_msg}")
                                                
                                                # Log de la accion
                                                logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                                                couchdb_utils.log_action(db, logged_in_user, f"Promocion editada: {nuevo_nombre}")
                                                
                                                del st.session_state[f"editing_{promo['_id']}"]
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"❌ Error al guardar: {str(e)}")
                                
                                with col_cancel:
                                    if st.button("❌ Cancelar", key=f"cancel_{promo['_id']}"):
                                        del st.session_state[f"editing_{promo['_id']}"]
                                        st.rerun()
                        
                        st.markdown("---")
        
        with tab_activas:
            st.subheader("🔥 Promociones Activas")
            
            # Obtener solo promociones activas
            promociones_activas = [
                p for p in couchdb_utils.get_documents_by_partition(db, "promociones")
                if p.get('estado') == 'activa' and p.get('activo', True)
            ]
            
            if not promociones_activas:
                st.info("No hay promociones activas en este momento.")
            else:
                st.success(f"🎉 {len(promociones_activas)} promociones activas ahora")
                
                # Separar por tipo
                promos_bar = [p for p in promociones_activas if p.get('tipo_menu') == 'promoBar']
                promos_cocina = [p for p in promociones_activas if p.get('tipo_menu') == 'promoCocina']
                
                col_bar, col_cocina = st.columns(2)
                
                with col_bar:
                    st.markdown("### 🍹 Promociones Bar")
                    if promos_bar:
                        for promo in promos_bar:
                            fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                            tiempo_restante = fecha_fin - datetime.now(timezone.utc)
                            total_seconds = tiempo_restante.total_seconds()
                            
                            if total_seconds < 3600:  # Menos de 1 hora
                                minutos_restantes = int(total_seconds // 60)
                                tiempo_texto = f"{minutos_restantes}min restantes"
                            else:
                                horas_restantes = int(total_seconds // 3600)
                                tiempo_texto = f"{horas_restantes}h restantes"
                            
                            # Tarjeta de promoción activa usando elementos nativos
                            with st.container():
                                st.markdown(f"**🍹 {promo.get('nombre_producto', 'Producto')}**")
                                col_precio_bar, col_tiempo_bar = st.columns([2, 1])
                                with col_precio_bar:
                                    st.markdown(f"~~${promo.get('precio_original', 0):.2f}~~ → **${promo.get('precio_promocion', 0):.2f}**")
                                with col_tiempo_bar:
                                    st.caption(f"⏰ {tiempo_texto}")
                                st.markdown("---")
                    else:
                        st.info("Sin promociones de bar activas")
                
                with col_cocina:
                    st.markdown("### 🍳 Promociones Cocina")
                    if promos_cocina:
                        for promo in promos_cocina:
                            fecha_fin = datetime.fromisoformat(promo.get('fecha_fin', '').replace('Z', '+00:00'))
                            tiempo_restante = fecha_fin - datetime.now(timezone.utc)
                            total_seconds = tiempo_restante.total_seconds()
                            
                            if total_seconds < 3600:  # Menos de 1 hora
                                minutos_restantes = int(total_seconds // 60)
                                tiempo_texto = f"{minutos_restantes}min restantes"
                            else:
                                horas_restantes = int(total_seconds // 3600)
                                tiempo_texto = f"{horas_restantes}h restantes"
                            
                            # Tarjeta de promoción activa usando elementos nativos
                            with st.container():
                                st.markdown(f"**🍳 {promo.get('nombre_producto', 'Producto')}**")
                                col_precio_cocina, col_tiempo_cocina = st.columns([2, 1])
                                with col_precio_cocina:
                                    st.markdown(f"~~${promo.get('precio_original', 0):.2f}~~ → **${promo.get('precio_promocion', 0):.2f}**")
                                with col_tiempo_cocina:
                                    st.caption(f"⏰ {tiempo_texto}")
                                st.markdown("---")
                    else:
                        st.info("Sin promociones de cocina activas")
        
    else:
        st.error("No se pudo conectar a la base de datos")
else:
    st.info("Por favor, inicia sesion para acceder a la gestion de promociones")