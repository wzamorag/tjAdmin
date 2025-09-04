import streamlit as st
import os
from datetime import datetime, timezone, timedelta
import couchdb_utils
import pandas as pd


# Obtener la ruta relativa de la página para la validación
archivo_actual_relativo = os.path.join(os.path.basename(os.path.dirname(__file__)), os.path.basename(__file__))

# Llama a la función de login/menú/validación con la ruta corregida
couchdb_utils.generarLogin(archivo_actual_relativo) 

# Configuración de la página
st.set_page_config(layout="wide", page_title="Registros de Actividad", page_icon="../assets/LOGO.png")

if 'usuario' in st.session_state:
    st.title("📊 Registros de Actividad")
    db = couchdb_utils.get_database_instance()

    if db:

        # Filtros de búsqueda
        col_filter_user_log, col_refresh_log = st.columns([2, 1])
        with col_filter_user_log:
            filter_user_log = st.text_input("Filtrar por Usuario:", help="Escribe el nombre de usuario para filtrar los registros.", key="filter_user_log_input").strip()
        with col_refresh_log:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Actualizar Registros", key="refresh_logs_btn"):
                st.rerun()

        # st.markdown("---")
        # st.subheader("Filtros de Fecha")
        col_date_start, col_date_end = st.columns(2)
        with col_date_start:
            # Usar fecha local para que coincida con la percepción del usuario
            fecha_local_hoy = datetime.now(timezone.utc).astimezone().date()
            start_date = st.date_input("Fecha Inicio:", value=fecha_local_hoy - timedelta(days=30), key="log_start_date")
        with col_date_end:
            # Usar fecha local + 1 día para asegurar que incluya logs de hoy
            end_date = st.date_input("Fecha Fin:", value=fecha_local_hoy + timedelta(days=1), key="log_end_date")

        # Convertir las fechas de entrada a objetos datetime con zona horaria UTC
        # La fecha de inicio se establece al principio del día
        start_datetime_utc = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
        # La fecha de fin se establece al final del día (23:59:59.999999)
        end_datetime_utc = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)



        all_logs_raw = couchdb_utils.get_documents_by_partition(db, couchdb_utils.LOGS_PARTITION_KEY)
        
        # Ordenar logs por fecha antes del filtrado (más reciente primero)
        def get_log_datetime(log):
            try:
                fecha_str = log.get('fecha', '')
                if fecha_str.endswith('Z'):
                    fecha_str = fecha_str[:-1]
                return datetime.fromisoformat(fecha_str)
            except:
                return datetime.min
        
        all_logs_raw.sort(key=get_log_datetime, reverse=True)

        filtered_logs = []
        for log in all_logs_raw:
            log_usuario = (log.get('usuario') or '').lower()
            log_fecha_str = log.get('fecha')

            # Filtrar por usuario
            user_match = (not filter_user_log) or (log_usuario == filter_user_log.lower())

            # Filtrar por fecha
            date_match = True
            if log_fecha_str:
                try:
                    # Clean the date string for robust parsing
                    # Handle the problematic '+00:00Z' format and simple 'Z'
                    clean_log_fecha_str = log_fecha_str
                    if log_fecha_str.endswith('+00:00Z'):
                        clean_log_fecha_str = log_fecha_str.replace('+00:00Z', '+00:00')
                    elif log_fecha_str.endswith('Z'):
                        clean_log_fecha_str = log_fecha_str[:-1]
                    
                    log_datetime = datetime.fromisoformat(clean_log_fecha_str)

                    # Ensure the datetime object is UTC for consistent comparison
                    if log_datetime.tzinfo is None:
                        log_datetime = log_datetime.replace(tzinfo=timezone.utc)
                    else:
                        log_datetime = log_datetime.astimezone(timezone.utc)

                    is_after_start = (log_datetime >= start_datetime_utc)
                    is_before_end = (log_datetime <= end_datetime_utc)
                    date_match = is_after_start and is_before_end

                except ValueError as e:
                    st.warning(f"Error al parsear la fecha del log '{log_fecha_str}' (limpiada a '{clean_log_fecha_str}'): {e}. Este registro será omitido.")
                    date_match = False # If parsing fails, it doesn't match the date filter
            else:
                date_match = False # If there's no date field, it doesn't match the date filter

            if user_match and date_match:
                filtered_logs.append(log)


        if filtered_logs:
            # Paginación
            if 'current_log_page' not in st.session_state:
                st.session_state.current_log_page = 0
            if 'logs_per_page' not in st.session_state:
                st.session_state.logs_per_page = 50

            total_logs = len(filtered_logs)
            total_pages = (total_logs + st.session_state.logs_per_page - 1) // st.session_state.logs_per_page

            start_idx = st.session_state.current_log_page * st.session_state.logs_per_page
            end_idx = min(start_idx + st.session_state.logs_per_page, total_logs)

            logs_to_display = filtered_logs[start_idx:end_idx]

            # Convertir la lista de documentos a DataFrame
            df_logs = pd.DataFrame(logs_to_display)

            # Seleccionar y reordenar columnas para la visualización
            log_columns_order = ['fecha', 'usuario', 'descripcion', '_id', '_rev']
            
            # Filtrar solo las columnas que existen en el DataFrame
            display_cols = [col for col in log_columns_order if col in df_logs.columns]
            
            df_logs_display = df_logs[display_cols]
 
            # Formatear la columna 'fecha' para visualización y ordenar
            if 'fecha' in df_logs_display.columns:
                # Pre-limpiar la columna de fecha para asegurar que pd.to_datetime la maneje bien
                # This regex handles both '+00:00Z' and just 'Z'
                df_logs_display['fecha'] = df_logs_display['fecha'].astype(str).str.replace(r'(\+00:00)?Z$', r'\1', regex=True)
                df_logs_display['fecha'] = pd.to_datetime(df_logs_display['fecha'],utc=True)
                # Ordenar por fecha descendente (más reciente primero)
                df_logs_display = df_logs_display.sort_values('fecha', ascending=False)
                # Formatear para visualización después del ordenamiento
                df_logs_display['fecha'] = df_logs_display['fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')

            st.dataframe(
                df_logs_display,
                column_config={
                    "fecha": st.column_config.DatetimeColumn("Fecha", format="YYYY-MM-DD HH:mm:ss", width="medium",timezone='America/El_Salvador'),
                    "usuario": st.column_config.Column("Usuario", width="small"),
                    "descripcion": st.column_config.Column("Descripción", width="large"),
                    "_id": st.column_config.Column("ID Documento", width="medium"),
                    "_rev": st.column_config.Column("Revisión", width="small"),
                },
                hide_index=True,
                use_container_width=True
            )
            # Controles de paginación
            col_prev, col_page_info, col_next = st.columns([1, 2, 1])
            with col_prev:
                if st.button("Página Anterior", key="prev_log_page_btn", disabled=st.session_state.current_log_page == 0):
                    st.session_state.current_log_page -= 1
                    st.rerun()
            with col_page_info:
                st.markdown(f"Página {st.session_state.current_log_page + 1} de {total_pages} (Total: {total_logs} registros)")
            with col_next:
                if st.button("Página Siguiente", key="next_log_page_btn", disabled=st.session_state.current_log_page >= total_pages - 1):
                    st.session_state.current_log_page += 1
                    st.rerun()
        else:
            st.info("No hay registros de actividad que coincidan con los criterios de búsqueda.")

    else:
        st.error("No se pudo conectar o configurar la base de datos 'tiajuana'. Revisa los mensajes de conexión.")
