# pages/mesas.py
import streamlit as st
import json
from datetime import datetime, timezone
import couchdb_utils
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Obtener la ruta relativa de la página
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Define la clave de partición específica para esta página
CURRENT_PARTITION_KEY = "mesas"

# Llama a la función de login/menú/validación
couchdb_utils.generarLogin(archivo_actual_relativo)

st.set_page_config(layout="wide", page_title="Gestión de Mesas", page_icon="../assets/LOGO.png")

# --- CSS EXTERNO ---
css_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'style.css')
if os.path.exists(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning(f"Archivo CSS no encontrado en: {css_file_path}")

# --- Funciones principales ---
def get_mesa_position(mesa_id, area, numero_en_area):
    """Calcula la posición de una mesa en el plano según su área"""
    positions = {
        'VIP': {'base_x': 80, 'base_y': 80, 'cols': 3, 'spacing': 60},
        'Barra': {'base_x': 320, 'base_y': 60, 'cols': 8, 'spacing': 50},
        'General': {'base_x': 280, 'base_y': 180, 'cols': 5, 'spacing': 65},
        'Sillones': {'base_x': 80, 'base_y': 300, 'cols': 3, 'spacing': 70},
        'Terraza': {'base_x': 620, 'base_y': 80, 'cols': 2, 'spacing': 80},
        'Fumadores': {'base_x': 620, 'base_y': 300, 'cols': 2, 'spacing': 80}
    }
    
    if area not in positions:
        area = 'General'
    
    config = positions[area]
    row = numero_en_area // config['cols']
    col = numero_en_area % config['cols']
    
    x = config['base_x'] + (col * config['spacing'])
    y = config['base_y'] + (row * config['spacing'])
    
    return x, y

def create_quick_mesa(db, area_seleccionada):
    """Crear mesa rápidamente en el área seleccionada"""
    try:
        st.info(f"Creando mesa en {area_seleccionada}...")
        
        # Obtener número de mesas existentes en el área
        existing_mesas = couchdb_utils.get_documents_by_partition(db, "mesas")
        area_mesas = [m for m in existing_mesas if m.get('area') == area_seleccionada]
        numero_mesa = len(area_mesas) + 1
        
        # Configuraciones por defecto por área
        area_configs = {
            'VIP': {'capacidad': 6, 'descripcion': f'Mesa VIP {numero_mesa}'},
            'Barra': {'capacidad': 2, 'descripcion': f'Barra {numero_mesa}'},
            'General': {'capacidad': 4, 'descripcion': f'Mesa {numero_mesa}'},
            'Sillones': {'capacidad': 4, 'descripcion': f'Sillón {numero_mesa}'},
            'Terraza': {'capacidad': 4, 'descripcion': f'Terraza {numero_mesa}'},
            'Fumadores': {'capacidad': 4, 'descripcion': f'Fumadores {numero_mesa}'}
        }
        
        config = area_configs.get(area_seleccionada, {'capacidad': 4, 'descripcion': f'Mesa {numero_mesa}'})
        
        # Crear la nueva mesa
        nueva_mesa = {
            "descripcion": config['descripcion'],
            "capacidad": config['capacidad'],
            "area": area_seleccionada,
            "activo": 1,
            "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds')
        }
        
        if couchdb_utils.save_document_with_partition(db, nueva_mesa, "mesas", 'descripcion'):
            st.success(f"✅ Mesa '{config['descripcion']}' creada exitosamente en {area_seleccionada}!")
            
            # LOGGING
            logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
            couchdb_utils.log_action(db, logged_in_user, f"Mesa '{config['descripcion']}' creada en {area_seleccionada}.")
            
            st.rerun()
        else:
            st.error("Error al crear la mesa. Inténtalo nuevamente.")
            
    except Exception as e:
        st.error(f"Error al crear mesa: {str(e)}")
        st.exception(e)

def deactivate_mesa(db, mesa):
    """Desactiva una mesa específica"""
    try:
        mesa_doc = db[mesa['_id']]
        mesa_doc['activo'] = 0
        db.save(mesa_doc)
        
        # LOGGING
        logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
        couchdb_utils.log_action(db, logged_in_user, f"Mesa '{mesa.get('descripcion')}' desactivada.")
        
        return True
    except Exception as e:
        st.error(f"Error al desactivar mesa: {str(e)}")
        return False

def render_restaurant_layout(db):
    """Renderiza la vista visual del restaurante con las mesas"""
    st.header("🗺️ Distribución Visual del Restaurante")
    
    # Inicializar session state para edición
    if 'selected_mesa_doc' not in st.session_state:
        st.session_state.selected_mesa_doc = None
    if 'show_edit_mesa_dialog' not in st.session_state:
        st.session_state.show_edit_mesa_dialog = False
    
    # Obtener todas las mesas
    try:
        all_mesas = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
        if not all_mesas:
            st.info("No hay mesas registradas en el sistema.")
            return
            
        # Filtrar mesas activas y convertir a dict
        mesas_activas = []
        for mesa in all_mesas:
            if mesa.get('activo', 0) == 1:
                # Convertir Document a dict para evitar problemas de acceso
                mesa_dict = dict(mesa)
                mesas_activas.append(mesa_dict)
        
        # Agrupar mesas por área
        mesas_por_area = {}
        for mesa in mesas_activas:
            area = mesa.get('area', 'General')
            if area not in mesas_por_area:
                mesas_por_area[area] = []
            mesas_por_area[area].append(mesa)
                
    except Exception as e:
        st.error(f"Error cargando mesas desde la base de datos: {e}")
        return
    
    if not mesas_activas:
        st.info("No hay mesas activas registradas. Ve a la pestaña 'Crear Mesa' para agregar mesas.")
        # Aún mostrar el plano vacío con las áreas
        mesas_por_area = {}
    
    # Crear figura de Plotly
    fig = go.Figure()
    
    # Colores por área
    area_colors = {
        'VIP': '#FFD700',      # Dorado
        'General': '#87CEEB',   # Azul cielo
        'Fumadores': '#DDA0DD', # Púrpura claro
        'Sillones': '#98FB98',  # Verde claro
        'Terraza': '#F0E68C',   # Caqui
        'Barra': '#FFA07A'      # Salmón claro
    }
    
    # Agregar áreas de fondo organizadas de forma ordenada
    areas_background = [
        {'area': 'VIP', 'x0': 40, 'y0': 40, 'x1': 260, 'y1': 160, 'priority': 1},
        {'area': 'Barra', 'x0': 280, 'y0': 30, 'x1': 720, 'y1': 110, 'priority': 2},
        {'area': 'Terraza', 'x0': 580, 'y0': 40, 'x1': 780, 'y1': 200, 'priority': 3},
        {'area': 'General', 'x0': 240, 'y0': 140, 'x1': 560, 'y1': 320, 'priority': 4},
        {'area': 'Sillones', 'x0': 40, 'y0': 260, 'x1': 260, 'y1': 420, 'priority': 5},
        {'area': 'Fumadores', 'x0': 580, 'y0': 260, 'x1': 780, 'y1': 420, 'priority': 6}
    ]
    
    # Agregar rectángulos de fondo para cada área
    for area_bg in areas_background:
        area_color = area_colors.get(area_bg['area'], '#E0E0E0')
        fig.add_shape(
            type="rect",
            x0=area_bg['x0'], y0=area_bg['y0'],
            x1=area_bg['x1'], y1=area_bg['y1'],
            fillcolor=area_color,
            opacity=0.2,
            line=dict(color=area_color, width=2)
        )
        
        # Agregar etiqueta del área con mejor formato
        fig.add_annotation(
            x=(area_bg['x0'] + area_bg['x1']) / 2,
            y=area_bg['y0'] + 15,
            text=f"<b>{area_bg['area']}</b>",
            showarrow=False,
            font=dict(size=14, color="black"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=area_colors.get(area_bg['area'], '#808080'),
            borderwidth=1
        )
    
    # Agregar mesas
    mesa_x = []
    mesa_y = []
    mesa_text = []
    mesa_colors = []
    mesa_sizes = []
    
    mesa_counter = 1
    for area, mesas in mesas_por_area.items():
        for idx, mesa in enumerate(mesas):
            try:
                x, y = get_mesa_position(mesa['_id'], area, idx)
                
                mesa_x.append(x)
                mesa_y.append(y)
                
                capacidad = mesa.get('capacidad', 2)
                descripcion = mesa.get('descripcion', 'Mesa')
                mesa_text.append(f"{descripcion}<br>💺 {capacidad} personas<br>📍 {area}")
                mesa_colors.append(area_colors.get(area, '#E0E0E0'))
                mesa_sizes.append(max(20, capacidad * 4))  # Tamaño basado en capacidad
                
                mesa_counter += 1
            except (KeyError, TypeError) as e:
                st.error(f"Error procesando mesa {mesa}: {e}")
                continue
    
    # Agregar scatter plot de las mesas solo si hay mesas
    if mesa_x and mesa_y:
        fig.add_trace(go.Scatter(
            x=mesa_x,
            y=mesa_y,
            mode='markers+text',
            marker=dict(
                size=mesa_sizes,
                color=mesa_colors,
                line=dict(width=3, color='darkblue'),
                opacity=0.9
            ),
            text=[f"M{i+1}" for i in range(len(mesa_x))],
            textposition="middle center",
            textfont=dict(size=12, color="white", family="Arial Black"),
            hovertext=mesa_text,
            hoverinfo='text',
            name='Mesas'
        ))
    
    # Configurar layout con mejor distribución
    fig.update_layout(
        title="Plano del Restaurante - Click en las áreas para crear mesas",
        xaxis=dict(range=[0, 800], showgrid=False, showticklabels=False, fixedrange=True),
        yaxis=dict(range=[0, 450], showgrid=False, showticklabels=False, fixedrange=True),
        showlegend=False,
        width=900,
        height=500,
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=20),
        dragmode=False
    )
    
    # Mostrar la figura
    st.plotly_chart(fig, use_container_width=True, key="restaurant_layout")
    
    # Panel de selección de mesas
    if mesas_activas:
        st.subheader("🎯 Seleccionar Mesa del Plano")
        
        # Filtro por área
        col_filter, col_info = st.columns([2, 1])
        with col_filter:
            areas_disponibles = list(set(mesa.get('area', 'Sin área') for mesa in mesas_activas))
            areas_disponibles.sort()
            area_filter = st.selectbox(
                "Filtrar por área:",
                options=["Todas las áreas"] + areas_disponibles,
                key="area_filter"
            )
        with col_info:
            st.markdown("<br>", unsafe_allow_html=True)
            if area_filter != "Todas las áreas":
                count = len([m for m in mesas_activas if m.get('area') == area_filter])
                st.write(f"📊 {count} mesas en {area_filter}")
        
        # Filtrar mesas según área seleccionada
        mesas_filtradas = mesas_activas
        if area_filter != "Todas las áreas":
            mesas_filtradas = [m for m in mesas_activas if m.get('area') == area_filter]
        
        st.markdown("Selecciona una mesa para ver detalles o editarla:")
        
        # Crear opciones para selectbox
        mesa_options = {}
        for i, mesa in enumerate(mesas_activas):  # Mantener numeración original
            if mesa in mesas_filtradas:  # Solo mostrar las filtradas
                descripcion = mesa.get('descripcion', 'Mesa sin nombre')
                area = mesa.get('area', 'Sin área')
                capacidad = mesa.get('capacidad', 0)
                label = f"M{i+1}: {descripcion} ({area} - {capacidad} pers.)"
                mesa_options[label] = mesa
        
        selected_mesa_label = st.selectbox(
            "Mesas disponibles en el plano:",
            options=["Seleccionar mesa..."] + list(mesa_options.keys()),
            key="mesa_selector",
            help="Selecciona una mesa del plano para ver sus detalles y opciones"
        )
        
        if selected_mesa_label != "Seleccionar mesa...":
            selected_mesa = mesa_options[selected_mesa_label]
            
            # Mostrar detalles de la mesa seleccionada
            col_detail1, col_detail2, col_detail3 = st.columns(3)
            
            with col_detail1:
                st.markdown(f"**🏠 {selected_mesa.get('descripcion', 'N/A')}**")
                st.write(f"📍 Área: {selected_mesa.get('area', 'N/A')}")
                st.write(f"👥 Capacidad: {selected_mesa.get('capacidad', 'N/A')} personas")
                
            with col_detail2:
                estado_icon = "✅ Activa" if selected_mesa.get('activo', 0) else "❌ Inactiva"
                st.write(f"🔘 Estado: {estado_icon}")
                if selected_mesa.get('fecha_creacion'):
                    fecha = selected_mesa['fecha_creacion'][:10]
                    st.write(f"📅 Creada: {fecha}")
                st.write(f"🆔 ID: {selected_mesa.get('_id', 'N/A')[:8]}...")
                
            with col_detail3:
                # Botones de acción para la mesa seleccionada
                if st.button("✏️ Editar Mesa", key=f"edit_mesa_{selected_mesa.get('_id')}", type="primary"):
                    st.session_state.selected_mesa_doc = selected_mesa
                    st.session_state.show_edit_mesa_dialog = True
                    st.switch_page("pages/mesas.py")
                
                if st.button("🗑️ Desactivar Mesa", key=f"deactivate_{selected_mesa.get('_id')}"):
                    if deactivate_mesa(db, selected_mesa):
                        st.success("Mesa desactivada exitosamente")
                        st.rerun()
                        
                if st.button("📋 Ver en Lista", key=f"view_list_{selected_mesa.get('_id')}"):
                    st.session_state.selected_mesa_doc = selected_mesa
                    st.switch_page("pages/mesas.py")
            
            # Mostrar ubicación visual de la mesa seleccionada
            st.markdown("---")
            st.write("📍 **Ubicación en el plano:**")
            mesa_index = next(i for i, m in enumerate(mesas_activas) if m['_id'] == selected_mesa['_id'])
            area = selected_mesa.get('area', 'General')
            area_mesas = [m for m in mesas_activas if m.get('area') == area]
            posicion_en_area = next(i for i, m in enumerate(area_mesas) if m['_id'] == selected_mesa['_id'])
            
            col_loc1, col_loc2 = st.columns(2)
            with col_loc1:
                st.write(f"• Mesa **M{mesa_index + 1}** en el gráfico")
                st.write(f"• Posición #{posicion_en_area + 1} en el área **{area}**")
            with col_loc2:
                x, y = get_mesa_position(selected_mesa['_id'], area, posicion_en_area)
                st.write(f"• Coordenadas: ({x:.0f}, {y:.0f})")
                st.write(f"• Total en área: {len(area_mesas)} mesas")
    
    # Información sobre funcionalidades
    st.info("💡 **Funciones disponibles:**\n"
            "• Usa el selector de arriba para interactuar con las mesas del plano\n"
            "• Usa los botones de abajo para crear mesas rápidamente\n"
            "• Ve a la pestaña 'Lista de Mesas' para administración completa")
    
    # Sección de creación rápida por áreas
    st.subheader("🚀 Creación Rápida de Mesas")
    st.markdown("Haz clic en un área para crear una mesa directamente:")
    
    
    # Crear botones para cada área organizados en grid
    col1, col2, col3 = st.columns(3)
    
    # Obtener conteo actual de mesas por área para mostrar en botones
    all_current_mesas = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
    area_counts = {}
    for mesa in all_current_mesas:
        if mesa.get('activo', 0) == 1:
            area = mesa.get('area', 'General')
            area_counts[area] = area_counts.get(area, 0) + 1
    
    with col1:
        st.markdown("**🥇 Zona Premium**")
        vip_count = area_counts.get('VIP', 0)
        if st.button(f"➕ Crear en VIP ({vip_count} actual)", key="quick_vip", use_container_width=True):
            create_quick_mesa(db, "VIP")
        sillones_count = area_counts.get('Sillones', 0)
        if st.button(f"➕ Crear en Sillones ({sillones_count} actual)", key="quick_sillones", use_container_width=True):
            create_quick_mesa(db, "Sillones")
    
    with col2:
        st.markdown("**🍽️ Zona Principal**") 
        general_count = area_counts.get('General', 0)
        if st.button(f"➕ Crear en General ({general_count} actual)", key="quick_general", use_container_width=True):
            create_quick_mesa(db, "General")
        barra_count = area_counts.get('Barra', 0)
        if st.button(f"➕ Crear en Barra ({barra_count} actual)", key="quick_barra", use_container_width=True):
            create_quick_mesa(db, "Barra")
    
    with col3:
        st.markdown("**🌿 Zona Exterior**")
        terraza_count = area_counts.get('Terraza', 0)
        if st.button(f"➕ Crear en Terraza ({terraza_count} actual)", key="quick_terraza", use_container_width=True):
            create_quick_mesa(db, "Terraza")
        fumadores_count = area_counts.get('Fumadores', 0)
        if st.button(f"➕ Crear en Fumadores ({fumadores_count} actual)", key="quick_fumadores", use_container_width=True):
            create_quick_mesa(db, "Fumadores")
    
    st.markdown("---")
    
    # Leyenda de información
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Mesas", len(mesas_activas))
    with col2:
        total_capacidad = sum(mesa.get('capacidad', 2) for mesa in mesas_activas)
        st.metric("Capacidad Total", f"{total_capacidad} personas")
    with col3:
        st.metric("Áreas Activas", len(mesas_por_area))
    
    # Mostrar información por área
    st.subheader("Resumen por Área")
    area_data = []
    for area in area_colors.keys():
        mesas_area = mesas_por_area.get(area, [])
        if mesas_area:
            area_data.append({
                'Área': area,
                'Mesas': len(mesas_area),
                'Capacidad': sum(m.get('capacidad', 2) for m in mesas_area),
                'Color': area_colors[area]
            })
    
    if area_data:
        for area_info in area_data:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.markdown(f"**{area_info['Área']}** <span style='color: {area_info['Color']};'>●</span>", unsafe_allow_html=True)
            with col2:
                st.write(f"{area_info['Mesas']} mesas")
            with col3:
                st.write(f"{area_info['Capacidad']} personas")
            with col4:
                if st.button(f"Ver detalles", key=f"details_{area_info['Área']}"):
                    show_area_details(area_info['Área'], mesas_por_area.get(area_info['Área'], []))

def show_area_details(area_name, mesas):
    """Muestra detalles de un área específica"""
    st.subheader(f"Detalles del Área: {area_name}")
    
    for mesa in mesas:
        with st.expander(f"Mesa: {mesa.get('descripcion', 'N/A')}", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Capacidad:** {mesa.get('capacidad', 'N/A')} personas")
                st.write(f"**Estado:** {'Activa' if mesa.get('activo', 0) else 'Inactiva'}")
            with col2:
                st.write(f"**ID:** {mesa.get('_id', 'N/A')}")
                if mesa.get('fecha_creacion'):
                    st.write(f"**Creada:** {mesa['fecha_creacion'][:10]}")

def render_create_mesa_form(db):
    """Renderiza el formulario de creación de mesas con vista previa"""
    st.header("➕ Crear Nueva Mesa")
    
    with st.form("create_mesa_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            descripcion = st.text_input("Descripción de la Mesa:", placeholder="Ej: Mesa Principal 1")
            capacidad = st.number_input("Capacidad (personas):", min_value=1, max_value=20, value=4, step=1)
            
        with col2:
            area_options = ["VIP", "General", "Fumadores", "Sillones", "Terraza", "Barra"]
            area = st.selectbox("Área del Restaurante:", options=area_options, index=1)
            activo = st.checkbox("Mesa Activa", value=True)
        
        st.markdown("---")
        
        # Vista previa de la ubicación
        if descripcion and area:
            st.subheader("Vista Previa de Ubicación")
            
            # Obtener mesas existentes en el área
            existing_mesas = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
            area_mesas = [dict(m) for m in existing_mesas if m.get('area') == area and m.get('activo', 0) == 1]
            
            # Calcular posición de la nueva mesa
            nueva_posicion = len(area_mesas)
            x_preview, y_preview = get_mesa_position("preview", area, nueva_posicion)
            
            # Crear mini figura de vista previa
            fig_preview = go.Figure()
            
            # Agregar mesas existentes
            if area_mesas:
                existing_x = []
                existing_y = []
                for idx, mesa in enumerate(area_mesas):
                    x, y = get_mesa_position(mesa['_id'], area, idx)
                    existing_x.append(x)
                    existing_y.append(y)
                
                fig_preview.add_trace(go.Scatter(
                    x=existing_x, y=existing_y,
                    mode='markers',
                    marker=dict(size=20, color='lightblue', line=dict(width=2, color='blue')),
                    name='Mesas Existentes'
                ))
            
            # Agregar nueva mesa
            fig_preview.add_trace(go.Scatter(
                x=[x_preview], y=[y_preview],
                mode='markers+text',
                marker=dict(size=25, color='red', line=dict(width=3, color='darkred')),
                text=["NUEVA"],
                textposition="middle center",
                name='Nueva Mesa'
            ))
            
            fig_preview.update_layout(
                title=f"Ubicación en Área: {area}",
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=False, showticklabels=False),
                width=400, height=300,
                showlegend=True
            )
            
            st.plotly_chart(fig_preview, use_container_width=True)
            
            # Información de la nueva mesa
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.info(f"**Área:** {area}")
                st.info(f"**Posición:** #{nueva_posicion + 1} en el área")
            with col_info2:
                st.info(f"**Capacidad:** {capacidad} personas")
                st.info(f"**Total en área:** {len(area_mesas) + 1} mesas")
        
        # Botón de crear
        if st.form_submit_button("🚀 Crear Mesa", type="primary"):
            if not descripcion.strip():
                st.error("La descripción es obligatoria.")
            else:
                nueva_mesa = {
                    "descripcion": descripcion.strip(),
                    "capacidad": int(capacidad),
                    "area": area,
                    "activo": 1 if activo else 0,
                    "fecha_creacion": datetime.now(timezone.utc).isoformat(timespec='milliseconds')
                }
                
                if couchdb_utils.save_document_with_partition(db, nueva_mesa, CURRENT_PARTITION_KEY, 'descripcion'):
                    st.success(f"✅ Mesa '{descripcion}' creada exitosamente en el área {area}!")
                    
                    # LOGGING
                    logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                    couchdb_utils.log_action(db, logged_in_user, f"Mesa '{descripcion}' agregada en área {area}.")
                    
                    st.rerun()
                else:
                    st.error("Error al crear la mesa. Inténtalo nuevamente.")

def render_mesa_list(db):
    """Renderiza la lista tradicional de mesas"""
    st.header("📋 Lista Completa de Mesas")
    
    # Initialize session state for dialogs
    if 'show_edit_mesa_dialog' not in st.session_state:
        st.session_state.show_edit_mesa_dialog = False
    if 'selected_mesa_doc' not in st.session_state: 
        st.session_state.selected_mesa_doc = None

    col_filter_desc, col_refresh_btn = st.columns([2, 1])
    with col_filter_desc:
        filter_desc = st.text_input("Filtrar por Descripción:", help="Escribe parte de la descripción para filtrar.", key="filter_mesa_desc").strip().lower()
    with col_refresh_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Actualizar Lista de Mesas", key="refresh_mesa_table_btn"):
            st.session_state.selected_mesa_doc = None
            st.rerun()

    all_mesas_raw = couchdb_utils.get_documents_by_partition(db, CURRENT_PARTITION_KEY)
    
    active_mesas = [
        dict(item) for item in all_mesas_raw 
        if item.get('activo', 0) == 1 
        and (not filter_desc or filter_desc in item.get('descripcion', '').lower())
    ]
    
    disabled_mesas = [
        dict(item) for item in all_mesas_raw 
        if item.get('activo', 0) == 0 
        and (not filter_desc or filter_desc in item.get('descripcion', '').lower())
    ]

    # --- Función para el diálogo de edición de mesa ---
    @st.dialog("Editar Mesa")
    def edit_mesa_dialog_content():
        if 'selected_mesa_doc' not in st.session_state or not st.session_state.selected_mesa_doc:
            st.error("No se ha seleccionado ninguna mesa para editar.")
            return

        mesa_to_edit = st.session_state.selected_mesa_doc.copy()

        st.markdown(f"### Editar Mesa: {mesa_to_edit.get('descripcion', 'N/A')}")
        st.markdown("---")

        with st.form("edit_mesa_form", clear_on_submit=False):
            st.caption(f"ID: `{mesa_to_edit.get('_id', 'N/A')}`")
            st.caption(f"Revisión: `{mesa_to_edit.get('_rev', 'N/A')}`")

            edited_descripcion = st.text_input("Descripción:", value=mesa_to_edit.get("descripcion", ""), key="edit_mesa_descripcion")
            
            edited_capacidad = st.number_input(
                "Capacidad (personas):", 
                min_value=1, 
                max_value=20, 
                step=1, 
                value=int(mesa_to_edit.get("capacidad", 2)),
                key="edit_mesa_capacidad"
            )
            
            area_options = ["VIP", "General", "Fumadores", "Sillones", "Terraza", "Barra"]
            current_area_index = area_options.index(mesa_to_edit.get("area", "General")) if mesa_to_edit.get("area", "General") in area_options else 0
            edited_area = st.selectbox(
                "Área:", 
                options=area_options,
                index=current_area_index,
                key="edit_mesa_area"
            )
            
            edited_activo = st.checkbox("Activo", value=bool(mesa_to_edit.get("activo", 0)), key="edit_mesa_activo")
            
            st.markdown("---")
            col_submit, col_cancel, col_toggle_active = st.columns(3)
            
            with col_submit:
                save_button = st.form_submit_button("Guardar Cambios", type="primary")
            with col_cancel:
                cancel_button = st.form_submit_button("Cancelar")
            with col_toggle_active:
                toggle_active_label = "🚫 Deshabilitar" if bool(mesa_to_edit.get("activo", 0)) else "✅ Habilitar"
                toggle_active_button = st.form_submit_button(toggle_active_label)

            if save_button:
                # PREPARAMOS EL DOCUMENTO ACTUALIZADO MANTENIENDO LOS METADATOS ORIGINALES
                updated_doc = {
                    "_id": mesa_to_edit["_id"],
                    "_rev": mesa_to_edit["_rev"],
                    "descripcion": edited_descripcion,
                    "capacidad": int(edited_capacidad),
                    "area": edited_area,
                    "activo": 1 if edited_activo else 0,
                    "fecha_creacion": mesa_to_edit.get("fecha_creacion"),  # Mantenemos la fecha original
                    "type": CURRENT_PARTITION_KEY  # Asegurar que el type se mantenga
                }
                
                try:
                    # ACTUALIZAMOS DIRECTAMENTE EN LA BASE DE DATOS
                    db.save(updated_doc)
                    st.success(f"Mesa '{edited_descripcion}' actualizada exitosamente.")
                    
                    # LOGGING
                    logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                    couchdb_utils.log_action(db, logged_in_user, f"Mesa '{edited_descripcion}' actualizada satisfactoriamente.")

                    st.session_state.selected_mesa_doc = None
                    st.session_state.show_edit_mesa_dialog = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar los cambios: {str(e)}")
            
            if cancel_button:
                st.session_state.selected_mesa_doc = None
                st.session_state.show_edit_mesa_dialog = False
                st.rerun()

            if toggle_active_button:
                try:
                    # PARA CAMBIAR ESTADO TAMBIÉN MANTENEMOS LOS METADATOS
                    toggled_doc = {
                        "_id": mesa_to_edit["_id"],
                        "_rev": mesa_to_edit["_rev"],
                        "descripcion": mesa_to_edit["descripcion"],
                        "capacidad": mesa_to_edit["capacidad"],
                        "area": mesa_to_edit["area"],
                        "activo": 0 if bool(mesa_to_edit.get("activo", 0)) else 1,
                        "fecha_creacion": mesa_to_edit.get("fecha_creacion"),
                        "type": CURRENT_PARTITION_KEY
                    }
                    
                    db.save(toggled_doc)
                    status_text = "deshabilitada" if toggled_doc["activo"] == 0 else "habilitada"
                    st.success(f"Mesa '{toggled_doc['descripcion']}' {status_text} exitosamente.")
                    
                    # LOGGING
                    logged_in_user = st.session_state.get('user_data', {}).get('usuario', 'Desconocido')
                    couchdb_utils.log_action(db, logged_in_user, f"Mesa '{toggled_doc['descripcion']}' {status_text} satisfactoriamente.")

                    st.session_state.selected_mesa_doc = None
                    st.session_state.show_edit_mesa_dialog = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al cambiar estado: {str(e)}")

    # Función para manejar el clic en el botón "Editar"
    def on_edit_button_click(mesa_doc):
        st.session_state.selected_mesa_doc = mesa_doc
        st.session_state.show_edit_mesa_dialog = True
        st.rerun()

    # Mostrar diálogo de edición si está activo
    if st.session_state.show_edit_mesa_dialog:
        edit_mesa_dialog_content()

    # Mostrar mesas activas
    st.subheader("Mesas Activas")
    if active_mesas:
        # Encabezados de la tabla
        col_id_header, col_desc_header, col_capacidad_header, col_area_header, col_activo_header, col_edit_header = st.columns([1, 2, 1, 1, 0.5, 0.7])
        with col_id_header:
            st.markdown("**ID**")
        with col_desc_header:
            st.markdown("**Descripción**")
        with col_capacidad_header:
            st.markdown("**Capacidad**")
        with col_area_header:
            st.markdown("**Área**")
        with col_activo_header:
            st.markdown("**Activo**")
        with col_edit_header:
            st.markdown("**Acciones**")
        st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)

        for mesa in active_mesas:
            with st.container():
                col_id, col_desc, col_capacidad, col_area, col_activo, col_edit = st.columns([1, 2, 1, 1, 0.5, 0.7])
                with col_id:
                    st.caption(mesa.get('_id', 'N/A'))
                with col_desc:
                    st.write(mesa.get('descripcion', 'N/A'))
                with col_capacidad:
                    st.write(f"{mesa.get('capacidad', 'N/A')} pers.")
                with col_area:
                    st.write(mesa.get('area', 'N/A'))
                with col_activo:
                    st.checkbox("Activo", value=bool(mesa.get('activo', 0)), disabled=True, key=f"activo_{mesa.get('_id')}", label_visibility="collapsed")
                with col_edit:
                    if st.button("Editar", key=f"edit_btn_{mesa.get('_id')}"):
                        on_edit_button_click(mesa)
                st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)
    else:
        st.info("No hay mesas activas en la base de datos o no coinciden con el filtro.")

    # --- Sección de Mesas Deshabilitadas ---
    st.subheader("Mesas Deshabilitadas")

    if disabled_mesas:
        # Encabezados de la tabla
        col_id_header_dis, col_desc_header_dis, col_capacidad_header_dis, col_area_header_dis, col_activo_header_dis, col_edit_header_dis = st.columns([1, 2, 1, 1, 0.5, 0.7])
        with col_id_header_dis:
            st.markdown("**ID**")
        with col_desc_header_dis:
            st.markdown("**Descripción**")
        with col_capacidad_header_dis:
            st.markdown("**Capacidad**")
        with col_area_header_dis:
            st.markdown("**Área**")
        with col_activo_header_dis:
            st.markdown("**Activo**")
        with col_edit_header_dis:
            st.markdown("**Acciones**")
        st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)

        for mesa in disabled_mesas:
            with st.container():
                col_id, col_desc, col_capacidad, col_area, col_activo, col_edit = st.columns([1, 2, 1, 1, 0.5, 0.7])
                with col_id:
                    st.caption(mesa.get('_id', 'N/A'))
                with col_desc:
                    st.write(mesa.get('descripcion', 'N/A'))
                with col_capacidad:
                    st.write(f"{mesa.get('capacidad', 'N/A')} pers.")
                with col_area:
                    st.write(mesa.get('area', 'N/A'))
                with col_activo:
                    st.checkbox("Activo", value=bool(mesa.get('activo', 0)), disabled=True, key=f"dis_activo_{mesa.get('_id')}", label_visibility="collapsed")
                with col_edit:
                    if st.button("Editar", key=f"dis_edit_btn_{mesa.get('_id')}"):
                        on_edit_button_click(mesa)
                st.markdown("<div class='compact-hr'></div>", unsafe_allow_html=True)
    else:
        st.info("No hay mesas deshabilitadas en la base de datos o no coinciden con el filtro.")

if 'usuario' in st.session_state:
    db = couchdb_utils.get_database_instance()

    if db:
        # --- Pestañas principales ---
        tab_visual, tab_lista, tab_crear = st.tabs(["🗺️ Vista del Restaurante", "📋 Lista de Mesas", "➕ Crear Mesa"])
        
        with tab_visual:
            render_restaurant_layout(db)
        
        with tab_lista:
            render_mesa_list(db)
            
        with tab_crear:
            render_create_mesa_form(db)
    else:
        st.error("No se pudo conectar o configurar la base de datos. Revisa los mensajes de conexión.")
else:
    st.info("Por favor, inicia sesión para acceder a esta página.")
