"""
Configurações globais para testes do Gerador de Certificados.
Este arquivo contém fixtures e configurações que podem ser usadas por todos os testes.
"""

import os
import sys
import pytest
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PYTHONPATH para importar os módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fixtures globais podem ser definidas aqui
@pytest.fixture
def app_path():
    """Retorna o caminho para o diretório da aplicação."""
    return os.path.join(project_root, 'app')

@pytest.fixture
def templates_path():
    """Retorna o caminho para o diretório de templates."""
    return os.path.join(project_root, 'templates')

@pytest.fixture
def uploads_path():
    """Retorna o caminho para o diretório de uploads."""
    return os.path.join(project_root, 'uploads')

@pytest.fixture
def output_path():
    """Retorna o caminho para o diretório de saída."""
    return os.path.join(project_root, 'output')
