"""
Testes de unidade para o aplicativo principal nepemcert.py
"""

import os
import sys
import pytest
from pathlib import Path
from click.testing import CliRunner

# Marca todos os testes neste arquivo como testes de unidade e CLI
pytestmark = [pytest.mark.unit, pytest.mark.cli]

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

@pytest.fixture
def temp_workspace(tmp_path):
    """Fixture que cria um espaço de trabalho temporário com arquivos de exemplo"""
    # Criar diretório de saída
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Criar arquivo CSV de exemplo
    csv_file = tmp_path / "participantes.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("nome,email,curso\n")
        f.write("João Silva,joao@exemplo.com,Python\n")
        f.write("Maria Souza,maria@exemplo.com,Python\n")
    
    # Criar template HTML de exemplo
    template_file = tmp_path / "modelo.html"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Certificado</title>
</head>
<body>
    <h1>Certificado de Participação</h1>
    <p>Certificamos que <strong>{{nome}}</strong> participou do curso de {{curso}}.</p>
</body>
</html>""")
    
    return {
        "workspace_dir": tmp_path,
        "output_dir": output_dir,
        "csv_file": csv_file,
        "template_file": template_file
    }

def test_command_help(cli_runner, nepemcert_cli):
    """Testa o comando de ajuda"""
    result = cli_runner.invoke(nepemcert_cli, ["--help"])
    assert result.exit_code == 0
    assert "NEPEM Certificados" in result.output
    assert "interactive" in result.output
    assert "generate" in result.output
    assert "config" in result.output
    assert "server" in result.output

def test_command_version(cli_runner, nepemcert_cli):
    """Testa o comando de versão"""
    result = cli_runner.invoke(nepemcert_cli, ["--version"])
    assert result.exit_code == 0
    assert "NEPEM Certificados, version" in result.output

def test_command_generate(cli_runner, nepemcert_cli, temp_workspace, monkeypatch):
    """Testa o comando generate com arquivos de exemplo"""
    # Configurar ambiente temporário
    csv_path = str(temp_workspace["csv_file"])
    template_path = str(temp_workspace["template_file"])
    output_path = str(temp_workspace["output_dir"])
    
    # Executar o comando
    result = cli_runner.invoke(nepemcert_cli, [
        "generate",
        csv_path,
        template_path,
        "--output", output_path
    ])
    
    # Verificar resultado
    assert result.exit_code == 0
    assert "Gerando certificados" in result.output
    
    # Verificar se os PDFs foram gerados (pelo menos um arquivo deve existir)
    files = list(os.listdir(output_path))
    assert len(files) > 0, "Nenhum certificado foi gerado"
    assert any(file.endswith('.pdf') for file in files), "Nenhum arquivo PDF foi encontrado"

def test_command_generate_with_zip(cli_runner, nepemcert_cli, temp_workspace):
    """Testa o comando generate com a opção de ZIP"""
    # Configurar ambiente temporário
    csv_path = str(temp_workspace["csv_file"])
    template_path = str(temp_workspace["template_file"])
    output_path = str(temp_workspace["output_dir"])
    
    # Executar o comando com a opção --zip
    result = cli_runner.invoke(nepemcert_cli, [
        "generate",
        csv_path,
        template_path,
        "--output", output_path,
        "--zip",
        "--zip-name", "certificados_teste.zip"
    ])
    
    # Verificar resultado
    assert result.exit_code == 0
    assert "Gerando certificados" in result.output
    assert "Arquivo ZIP criado" in result.output
    
    # Verificar se o arquivo ZIP foi gerado
    zip_path = os.path.join(output_path, "certificados_teste.zip")
    assert os.path.exists(zip_path), "Arquivo ZIP não foi encontrado"

def test_command_server_status(cli_runner, nepemcert_cli):
    """Testa o comando server --status"""
    # Executar o comando
    result = cli_runner.invoke(nepemcert_cli, ["server", "--status"])
    
    # Verificar resultado
    assert result.exit_code == 0
    assert "Verificando status da conexão" in result.output
    assert "Status:" in result.output

def test_command_config(cli_runner, nepemcert_cli):
    """Testa o comando config"""
    # Executar o comando
    result = cli_runner.invoke(nepemcert_cli, ["config"])
    
    # Verificar resultado
    assert result.exit_code == 0
    assert "Gerenciando configurações" in result.output
    assert "modo interativo" in result.output
