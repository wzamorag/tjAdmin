# pages/manual.py
import streamlit as st
import os

# Configuración de la página
st.set_page_config(
    page_title="Manual del Sistema", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="../assets/LOGO.png"
)

# CSS personalizado para el manual
st.markdown("""
<style>
    .manual-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    .manual-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .manual-section {
        background: white;
        padding: 25px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
    }
    .index-item {
        padding: 10px 0;
        border-bottom: 1px solid #eee;
    }
    .index-item:last-child {
        border-bottom: none;
    }
    .index-item a {
        text-decoration: none;
        color: #333;
        font-weight: 500;
    }
    .index-item a:hover {
        color: #667eea;
    }
    .back-to-login {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #667eea;
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        text-decoration: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        z-index: 1000;
    }
    .back-to-login:hover {
        background: #5a67d8;
        text-decoration: none;
        color: white;
    }
    .stApp {
        background-color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# Botón de regreso al login
st.markdown("""
<a href="/login_page.py" class="back-to-login">
    🔙 Volver al Login
</a>
""", unsafe_allow_html=True)

# Contenedor principal
st.markdown('<div class="manual-container">', unsafe_allow_html=True)

# Header del manual
st.markdown("""
<div class="manual-header">
    <h1>📖 Manual del Sistema de Restaurante Tía Juana</h1>
    <p>Guía completa para el uso del sistema de gestión integral</p>
</div>
""", unsafe_allow_html=True)

# Leer y mostrar el contenido del manual
manual_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'manual.md')

try:
    with open(manual_path, 'r', encoding='utf-8') as file:
        manual_content = file.read()
    
    # Mostrar el contenido del manual usando markdown de Streamlit
    st.markdown(manual_content)
    
except FileNotFoundError:
    st.error("❌ No se pudo encontrar el archivo del manual.")
    st.info("📝 El manual debería estar ubicado en la raíz del proyecto como 'manual.md'")
    
except Exception as e:
    st.error(f"❌ Error al cargar el manual: {str(e)}")

# Pie de página
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #666;">
    <p><strong>Sistema de Restaurante Tía Juana</strong> - Manual de Usuario v1.0</p>
    <p>Para soporte técnico, contacte al administrador del sistema</p>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# JavaScript para scroll suave en enlaces internos
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Scroll suave para enlaces internos
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});
</script>
""", unsafe_allow_html=True)