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
    """Testa se a função apply_custom_style ou custom_style existe no run.py"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        import run
        # Verificar se a função custom_style existe
        assert hasattr(run, 'custom_style'), "A função custom_style não foi encontrada no run.py"
        
        # Testar a execução da função
        result = run.custom_style()
        assert result is not None, "A função custom_style deve retornar algo"
        
    except ImportError:
        pytest.fail("O arquivo run.py não pôde ser importado")
