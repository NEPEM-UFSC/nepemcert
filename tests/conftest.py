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

def pytest_configure(config):
    """Configuração do pytest executada antes dos testes."""
    config.addinivalue_line("markers", "unit: marca testes como testes de unidade")
    config.addinivalue_line("markers", "integration: marca testes como testes de integração")
    config.addinivalue_line("markers", "cli: marca testes relacionados à interface CLI")
    config.addinivalue_line("markers", "core: marca testes dos módulos principais")
    config.addinivalue_line("markers", "slow: marca testes que demoram para executar")

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

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Configura o ambiente de teste automaticamente para todos os testes."""
    # Criar diretórios necessários se não existirem
    for directory in ['uploads', 'templates', 'output', 'config']:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
    
    yield
    
    # Cleanup pode ser adicionado aqui se necessário

# Fixtures específicas para testes que precisam de arquivos temporários
@pytest.fixture
def temp_csv_file(tmp_path):
    """Cria um arquivo CSV temporário para testes."""
    csv_content = "nome,email\nTeste,teste@exemplo.com\nOutro,outro@exemplo.com"
    csv_file = tmp_path / "teste.csv"
    csv_file.write_text(csv_content, encoding='utf-8')
    return str(csv_file)

@pytest.fixture
def temp_template_file(tmp_path):
    """Cria um arquivo de template temporário para testes."""
    template_content = """<!DOCTYPE html>
<html>
<head><title>Teste</title></head>
<body>
    <h1>Certificado para {{nome}}</h1>
    <p>Email: {{email}}</p>
</body>
</html>"""
    template_file = tmp_path / "teste.html"
    template_file.write_text(template_content, encoding='utf-8')
    return str(template_file)

# Fixture para criar arquivos de exemplo necessários para testes de integração
@pytest.fixture
def sample_files_setup(uploads_path, templates_path):
    """Cria arquivos de exemplo necessários para testes de integração."""
    # Criar CSV de exemplo
    csv_content = "nome\nJoão Silva\nMaria Oliveira\nCarlos Santos"
    csv_path = os.path.join(uploads_path, "participantes_exemplo.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
    
    # Criar template de exemplo
    template_content = """<!DOCTYPE html>
<html>
<head><title>Certificado</title></head>
<body>
    <h1>CERTIFICADO</h1>
    <p>Certificamos que <strong>{{nome}}</strong> participou do evento.</p>
</body>
</html>"""
    template_path = os.path.join(templates_path, "certificado_exemplo.html")
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(template_content)
    
    return {
        "csv_path": csv_path,
        "template_path": template_path
    }
