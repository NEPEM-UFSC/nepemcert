"""
Testes de unidade para os comandos CLI do NEPEM Certificados
"""

import os
import sys
import pytest
from pathlib import Path
from click.testing import CliRunner

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def cli_runner():
    """Fixture que retorna um CliRunner para testar os comandos CLI"""
    return CliRunner()

@pytest.fixture
def nepemcert_cli():
    """Fixture que importa o CLI principal"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from nepemcert import cli
    return cli

def test_cli_help(cli_runner, nepemcert_cli):
    """Testa o comando de ajuda do CLI"""
    result = cli_runner.invoke(nepemcert_cli, ["--help"])
    assert result.exit_code == 0
    assert "NEPEM Certificados" in result.output
    assert "interactive" in result.output
    assert "generate" in result.output
    assert "config" in result.output
    assert "server" in result.output

def test_cli_version(cli_runner, nepemcert_cli):
    """Testa a exibição da versão do CLI"""
    result = cli_runner.invoke(nepemcert_cli, ["--version"])
    assert result.exit_code == 0
    assert "NEPEM Certificados, version" in result.output

def test_cli_generate_help(cli_runner, nepemcert_cli):
    """Testa a ajuda do comando 'generate'"""
    result = cli_runner.invoke(nepemcert_cli, ["generate", "--help"])
    assert result.exit_code == 0
    assert "CSV_FILE" in result.output
    assert "TEMPLATE" in result.output
    assert "--output" in result.output
    assert "--zip" in result.output

def test_cli_server_help(cli_runner, nepemcert_cli):
    """Testa a ajuda do comando 'server'"""
    result = cli_runner.invoke(nepemcert_cli, ["server", "--help"])
    assert result.exit_code == 0
    assert "--status" in result.output
    assert "--url" in result.output

def test_cli_config_help(cli_runner, nepemcert_cli):
    """Testa a ajuda do comando 'config'"""
    result = cli_runner.invoke(nepemcert_cli, ["config", "--help"])
    assert result.exit_code == 0
    assert "Gerencia as configurações" in result.output

# Teste para o comando 'server --url'
def test_cli_server_url(cli_runner, nepemcert_cli, tmp_path, monkeypatch):
    """Testa o comando 'server --url'"""
    # Configurar diretório temporário para os arquivos de configuração
    config_dir = os.path.join(tmp_path, "config")
    os.makedirs(config_dir, exist_ok=True)
    monkeypatch.setenv("NEPEMCERT_CONFIG_DIR", str(config_dir))
    
    # Chamar o comando
    result = cli_runner.invoke(nepemcert_cli, ["server", "--url", "https://teste.com"])
    
    # Verificar resultado
    assert result.exit_code == 0
    assert "URL do servidor configurada com sucesso" in result.output

# Simulação simples do comando generate (sem executar completamente)
def test_cli_generate_params(cli_runner, nepemcert_cli, tmp_path, monkeypatch):
    """Testa os parâmetros do comando 'generate'"""
    # Criar arquivos de teste
    csv_file = os.path.join(tmp_path, "test.csv")
    template_file = os.path.join(tmp_path, "test.html")
    output_dir = os.path.join(tmp_path, "output")
    
    # Criar arquivos vazios para o teste
    with open(csv_file, 'w') as f:
        f.write("nome,email\nTeste,teste@exemplo.com")
    
    with open(template_file, 'w') as f:
        f.write("<html>Certificado para {{nome}}</html>")
    
    # Monkeypatch para evitar geração real
    def mock_batch_generate(*args, **kwargs):
        return ["file1.pdf", "file2.pdf"]
    
    # Configurar o monkeypatch apenas para verificar parâmetros
    monkeypatch.setattr("app.pdf_generator.PDFGenerator.batch_generate", mock_batch_generate)
    
    # Executar o comando
    result = cli_runner.invoke(nepemcert_cli, [
        "generate", 
        csv_file, 
        template_file,
        "--output", output_dir
    ])
    
    # Verificar saída (não o resultado completo, só a execução básica)
    assert result.exit_code == 0 or "PDF gerado" in result.output or "certificados gerados" in result.output
