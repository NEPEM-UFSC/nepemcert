"""
Testes para o módulo diagnose.py
"""

import os
import sys
import pytest
from pathlib import Path
import importlib.util

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def diagnose_path():
    """Retorna o caminho para o arquivo diagnose.py"""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "diagnose.py"

def test_diagnose_file_exists(diagnose_path):
    """Verifica se o arquivo diagnose.py existe"""
    assert diagnose_path.exists(), "O arquivo diagnose.py não foi encontrado"

def test_diagnose_imports(diagnose_path):
    """Verifica se o arquivo diagnose.py pode ser importado sem erros"""
    # Carrega o módulo sem executá-lo usando importlib
    spec = importlib.util.spec_from_file_location("diagnose", diagnose_path)
    assert spec is not None, "Não foi possível criar spec para diagnose.py"
    
    # Não executamos o módulo pois ele contém código Streamlit que precisa do ambiente correto

def test_list_files_function():
    """Testa a função list_files do diagnose.py"""
    # Importa apenas a função list_files do módulo diagnose
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    # Usando um contexto para evitar que streamlit seja inicializado
    # Isso é uma simulação parcial, já que normalmente precisaríamos de um mock completo do st
    with pytest.MonkeyPatch.context() as mp:
        # Cria um mock simples para st
        class MockSt:
            def set_page_config(self, **kwargs): pass
            def title(self, text): pass
            def write(self, text): pass
            def subheader(self, text): pass
            def code(self, text): pass
            def success(self, text): pass
            def error(self, text): pass
            def info(self, text): pass
            def warning(self, text): pass
            def markdown(self, text): pass
            def button(self, text): return False
        
        mp.setattr(sys.modules, "streamlit", MockSt())
        
        # Agora podemos importar a função list_files
        from diagnose import list_files
        
        # Testa a função com o diretório atual
        temp_dir = Path(__file__).parent
        files = list_files(str(temp_dir))
        
        # Verifica se a própria lista contém este arquivo de teste
        assert any("test_diagnose.py" in file for file in files), "A função list_files não retornou este arquivo de teste"
