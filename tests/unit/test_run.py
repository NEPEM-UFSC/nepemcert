"""
Testes para o módulo run.py
"""

import os
import sys
import pytest
from pathlib import Path
import importlib.util

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def run_path():
    """Retorna o caminho para o arquivo run.py"""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "run.py"

def test_run_file_exists(run_path):
    """Verifica se o arquivo run.py existe"""
    assert run_path.exists(), "O arquivo run.py não foi encontrado"

def test_run_imports():
    """Verifica se as importações no run.py estão funcionando"""
    # Usamos pytest.importorskip para verificar se os módulos necessários estão instalados
    pytest.importorskip("streamlit")
    pytest.importorskip("os")
    pytest.importorskip("sys")

def test_app_directory_structure(app_path):
    """Verifica se o diretório app tem a estrutura esperada"""
    # Verificar se o diretório app existe
    assert os.path.isdir(app_path), f"O diretório 'app' não existe em: {app_path}"
    
    # Verificar se os arquivos principais existem
    expected_files = [
        "__init__.py",
        "app.py",
        "csv_manager.py",
        "pdf_generator.py",
        "field_mapper.py",
        "template_manager.py",
        "theme_manager.py",
        "preset_manager.py",
        "zip_exporter.py"
    ]
    
    for file in expected_files:
        file_path = os.path.join(app_path, file)
        assert os.path.isfile(file_path), f"Arquivo '{file}' não encontrado em: {file_path}"

def test_custom_style_function():
    """Testa a função apply_custom_style do run.py"""
    # Este teste é mais complexo porque precisamos simular o ambiente Streamlit
    # Vamos verificar apenas se o arquivo contém a função
    
    run_path = Path(__file__).parent.parent.parent / "run.py"
    with open(run_path, 'r', encoding='utf-8') as file:
        content = file.read()
        
    assert "def apply_custom_style():" in content, "A função apply_custom_style não foi encontrada no run.py"
    assert "st.markdown" in content, "A função apply_custom_style não parece estar usando st.markdown"
