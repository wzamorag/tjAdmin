import subprocess
import os

def run_streamlit():
    """Inicia la aplicación Streamlit"""
    streamlit_path = os.path.join(os.path.dirname(__file__), "inicio.py")
    subprocess.run(["streamlit", "run", streamlit_path])

if __name__ == "__main__":
    run_streamlit()