# menu_utils.py
from datetime import time
import streamlit as st
import pandas as pd
import couchdb_utils 
from auth import get_controller

# El controlador se obtiene dinámicamente para cada sesión
# controller = get_controller()  # Comentado - se obtiene dinámicamente según sea necesario

def render_sidebar_content(user_data, rol_id):
    """
    Renderiza el contenido del sidebar (menú de navegación y botón de salir).
    Esta función se llamará solo si el usuario está autenticado.
    """
    nombre = user_data.get('nombre', 'N/A')
    
    st.write(f"Hola **:blue-background[{nombre}]** ")
    st.caption(f"Rol ID: {rol_id}")
    
    st.subheader("Tia Juana") 
    
    # Cargar el archivo CSV
    try:
        dfPaginas = pd.read_csv('rol_paginas.csv')
    except FileNotFoundError:
        st.error("Archivo 'rol_paginas.csv' no encontrado. Asegúrate de que existe para la gestión de permisos de menú.")
        return

    # Convertir rol_id a string para una comparación consistente con los roles del CSV
    user_roles = [str(rol_id)]
    if rol_id == 1: # Si es admin, tiene todos los permisos
        user_roles.append('1') # Asegurarse de que '1' esté en los roles si es admin
        # Añadir todos los roles únicos del CSV para que el admin vea todas las opciones
        all_csv_roles = set()
        for roles_str in dfPaginas['roles'].dropna():
            all_csv_roles.update(str(roles_str).split('|'))
        user_roles.extend(list(all_csv_roles))
        user_roles = list(set(user_roles)) # Eliminar duplicados

    # Función auxiliar para verificar si una página es accesible
    def is_page_accessible(page_roles_str):
        if rol_id == 1: # El admin siempre tiene acceso
            return True
        if pd.isna(page_roles_str) or str(page_roles_str).strip() == '':
            return False # Si no hay roles definidos, no es accesible a menos que sea admin
        allowed_roles_for_page = str(page_roles_str).split('|')
        return any(role in user_roles for role in allowed_roles_for_page)

    # Aplicar la verificación de accesibilidad a cada fila del DataFrame
    dfPaginas['is_accessible'] = dfPaginas['roles'].apply(is_page_accessible)

    # Separar menús principales y submenús
    # Un menú principal es aquel cuyo 'menu_padre' es NaN, vacío, o 'admin'
    main_menus = dfPaginas[
        dfPaginas['menu_padre'].isna() |
        (dfPaginas['menu_padre'] == '') |
        (dfPaginas['menu_padre'] == 'admin')
    ].copy()
    
    # Los submenús son aquellos cuyo 'menu_padre' NO es NaN, NO es vacío, y NO es 'admin'
    submenus = dfPaginas[
        dfPaginas['menu_padre'].notna() &
        (dfPaginas['menu_padre'] != '') &
        (dfPaginas['menu_padre'] != 'admin')
    ].copy()

    # Ordenar menús y submenús por nombre para una visualización consistente
    main_menus = main_menus.sort_values(by='nombre').reset_index(drop=True)
    submenus = submenus.sort_values(by='nombre').reset_index(drop=True)

    # Lógica de visualización basada en st.secrets.get("ocultarOpciones")
    if st.secrets.get("ocultarOpciones") == "True":
        for _, menu_item in main_menus.iterrows():
            if menu_item['is_accessible']:
                # Encontrar submenús accesibles para este menú principal
                current_submenus = submenus[
                    (submenus['menu_padre'] == menu_item['nombre']) &
                    submenus['is_accessible']
                ]

                if not current_submenus.empty:
                    # Si tiene submenús accesibles, mostrar un expander
                    with st.expander(f"{menu_item['nombre']} :material/{menu_item['icono']}:"):
                        for _, submenu_item in current_submenus.iterrows():
                            st.page_link(
                                submenu_item['pagina'],
                                label=submenu_item['nombre'],
                                icon=f":material/{submenu_item['icono']}:"
                            )
                else:
                    # Si no tiene submenús accesibles, o si el propio menú principal es una página,
                    # mostrar el page_link directamente
                    st.page_link(
                        menu_item['pagina'],
                        label=menu_item['nombre'],
                        icon=f":material/{menu_item['icono']}:"
                    )
    else: # st.secrets.get("ocultarOpciones") is False or not set (deshabilitar opciones)
        for _, menu_item in main_menus.iterrows():
            # Encontrar todos los submenús para este menú principal (sin filtrar por accesibilidad aquí)
            current_submenus = submenus[submenus['menu_padre'] == menu_item['nombre']]

            if not current_submenus.empty:
                # Si tiene submenús, usar un expander. El expander en sí no es un page_link.
                with st.expander(f"{menu_item['nombre']} :material/{menu_item['icono']}:", expanded=False):
                    for _, submenu_item in current_submenus.iterrows():
                        disabled = not submenu_item['is_accessible']
                        st.page_link(
                            submenu_item['pagina'],
                            label=submenu_item['nombre'],
                            icon=f":material/{submenu_item['icono']}:",
                            disabled=disabled
                        )
            else:
                # Si no tiene submenús, mostrar el page_link directamente con el estado de deshabilitado
                disabled = not menu_item['is_accessible']
                st.page_link(
                    menu_item['pagina'],
                    label=menu_item['nombre'],
                    icon=f":material/{menu_item['icono']}:",
                    disabled=disabled
                )
    # btnSalir = st.button("Salir")
    btnSalir = st.button("Salir", key="unique_logout_button_key")
    if btnSalir:
        # Usar la nueva función de logout segura
        couchdb_utils.logout_user()

        js = """
        <script>
            // 1. Limpiar el historial del navegador
            window.history.replaceState({}, '', '/');
            
            // 2. Forzar recarga completa sin caché
            const timestamp = new Date().getTime();
            const newUrl = window.location.origin + '/login_page.py?nocache=' + timestamp;
            
            // 3. Dos métodos de redirección como respaldo
            if (window.location.href !== newUrl) {
                window.location.replace(newUrl);
                window.location.href = newUrl;
            }
            
            // 4. Forzar recarga si todo falla
            setTimeout(() => {
                if (!window.location.href.includes('login_page')) {
                    window.location.reload(true);
                }
            }, 100);
        </script>
        """
        st.components.v1.html(js, height=0)
        
        st.stop()
