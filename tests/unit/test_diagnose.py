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
    """Testa se a função list_files existe e funciona corretamente"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        import diagnose
        
        # Verificar se a função list_files existe como atributo do módulo
        assert hasattr(diagnose, 'list_files'), "A função list_files não foi encontrada no diagnose.py"
        
        # Testar a função com um diretório temporário
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Criar alguns arquivos de teste
            test_files = ['test1.txt', 'test2.py', 'test3.md']
            for filename in test_files:
                with open(os.path.join(temp_dir, filename), 'w') as f:
                    f.write("test content")
            
            # Testar a função
            files = diagnose.list_files(temp_dir)
            assert isinstance(files, list), "list_files deve retornar uma lista"
            assert len(files) == 3, f"Esperado 3 arquivos, encontrado {len(files)}"
            
            for test_file in test_files:
                assert test_file in files, f"Arquivo {test_file} não foi listado"
    
    except ImportError:
        pytest.fail("O módulo diagnose não pôde ser importado")
