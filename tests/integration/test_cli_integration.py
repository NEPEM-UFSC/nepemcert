"""
Testes de integração para os componentes da interface CLI.
Estes testes verificam se os diferentes módulos podem trabalhar juntos 
corretamente na interface de linha de comando.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from click.testing import CliRunner

# Marca todos os testes neste arquivo como testes de integração
pytestmark = pytest.mark.integration

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
def temp_workspace():
    """Cria um espaço de trabalho temporário com estrutura básica"""
    workspace = tempfile.mkdtemp()
    
    # Criar estrutura básica de diretórios
    os.makedirs(os.path.join(workspace, "templates"), exist_ok=True)
    os.makedirs(os.path.join(workspace, "uploads"), exist_ok=True)
    os.makedirs(os.path.join(workspace, "output"), exist_ok=True)
    os.makedirs(os.path.join(workspace, "config"), exist_ok=True)
    
    # Criar arquivo CSV de exemplo
    csv_content = """nome,email,curso,data,carga_horaria
João Silva,joao@exemplo.com,Python Básico,2025-05-20,40h
Maria Oliveira,maria@exemplo.com,Python Avançado,2025-05-21,60h
"""
    
    with open(os.path.join(workspace, "uploads", "participantes.csv"), "w", encoding="utf-8") as f:
        f.write(csv_content)
    
    # Criar template de exemplo
    template_content = """<!DOCTYPE html>
<html>
<head>
    <title>Certificado</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .certificado { border: 1px solid #000; padding: 20px; width: 800px; }
        .titulo { font-size: 24px; text-align: center; margin-bottom: 30px; }
        .conteudo { font-size: 16px; text-align: justify; margin-bottom: 30px; }
        .assinatura { text-align: center; margin-top: 50px; }
    </style>
</head>
<body>
    <div class="certificado">
        <div class="titulo">CERTIFICADO</div>
        <div class="conteudo">
            Certificamos que <strong>{{nome}}</strong> participou do curso <strong>{{curso}}</strong>,
            realizado em <strong>{{data}}</strong>, com carga horária de <strong>{{carga_horaria}}</strong>.
        </div>
        <div class="assinatura">
            <div>____________________________</div>
            <div>Diretor</div>
        </div>
    </div>
</body>
</html>
"""
    
    with open(os.path.join(workspace, "templates", "certificado.html"), "w", encoding="utf-8") as f:
        f.write(template_content)
    
    yield workspace
    
    # Limpar após uso
    shutil.rmtree(workspace, ignore_errors=True)

def test_cli_generate_integration(cli_runner, nepemcert_cli, temp_workspace, monkeypatch):
    """
    Teste de integração do comando generate para verificar a integração
    entre CSV Manager, Template Manager e PDF Generator
    """
    # Configurar variáveis de ambiente para usar o workspace temporário
    monkeypatch.chdir(temp_workspace)
    
    # Caminhos para arquivos no workspace
    csv_path = os.path.join(temp_workspace, "uploads", "participantes.csv")
    template_path = os.path.join(temp_workspace, "templates", "certificado.html")
    output_dir = os.path.join(temp_workspace, "output")
    
    # Executar o comando
    result = cli_runner.invoke(nepemcert_cli, [
        "generate",
        csv_path,
        template_path,
        "--output", output_dir
    ])
    
    # Verificar saída
    assert result.exit_code == 0
    assert "Gerando certificados" in result.output
    
    # Verificar se os certificados foram gerados
    pdf_files = [f for f in os.listdir(output_dir) if f.endswith(".pdf")]
    assert len(pdf_files) > 0, "Nenhum arquivo PDF foi gerado"

def test_cli_server_integration(cli_runner, nepemcert_cli, temp_workspace, monkeypatch):
    """
    Teste de integração do comando server para verificar a integração
    com ConnectivityManager
    """
    # Configurar variáveis de ambiente para usar o workspace temporário
    monkeypatch.chdir(temp_workspace)
    monkeypatch.setenv("HOME", temp_workspace)
    monkeypatch.setenv("USERPROFILE", temp_workspace)
    
    # Configurar URL do servidor
    url_result = cli_runner.invoke(nepemcert_cli, [
        "server",
        "--url", "https://exemplo.com/api"
    ])
    
    assert url_result.exit_code == 0
    assert "URL do servidor configurada com sucesso" in url_result.output
    
    # Verificar status
    status_result = cli_runner.invoke(nepemcert_cli, [
        "server",
        "--status"
    ])
    
    assert status_result.exit_code == 0
    assert "Status:" in status_result.output
    assert "Mensagem:" in status_result.output

def test_template_pdf_integration(temp_workspace):
    """
    Teste a integração direta entre TemplateManager e PDFGenerator
    """
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.template_manager import TemplateManager
    from app.pdf_generator import PDFGenerator
    
    # Inicializar gerenciadores
    template_dir = os.path.join(temp_workspace, "templates")
    output_dir = os.path.join(temp_workspace, "output")
    
    template_manager = TemplateManager(templates_dir=template_dir)
    pdf_generator = PDFGenerator(output_dir=output_dir)
    
    # Carregar template
    template_path = os.path.join(template_dir, "certificado.html")
    template_content = template_manager.load_template("certificado.html")
    assert template_content is not None, "Template não pôde ser carregado"
    
    # Substituir placeholders
    test_data = {
        "nome": "Participante de Teste",
        "curso": "Curso de Teste",
        "data": "22/05/2025",
        "carga_horaria": "10h"
    }
    
    html_content = template_content
    for key, value in test_data.items():
        placeholder = f"{{{{{key}}}}}"
        html_content = html_content.replace(placeholder, str(value))
    
    # Gerar PDF
    output_path = os.path.join(output_dir, "certificado_teste.pdf")
    pdf_path = pdf_generator.generate_pdf(html_content, output_path)
    
    # Verificar se o PDF foi gerado
    assert os.path.exists(pdf_path), "O PDF não foi gerado"
    assert os.path.getsize(pdf_path) > 0, "O arquivo PDF está vazio"

def test_csv_template_field_integration(temp_workspace):
    """
    Teste a integração entre CSVManager, TemplateManager e FieldMapper
    """
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.csv_manager import CSVManager
    from app.template_manager import TemplateManager
    from app.field_mapper import FieldMapper
    
    # Inicializar gerenciadores
    uploads_dir = os.path.join(temp_workspace, "uploads")
    template_dir = os.path.join(temp_workspace, "templates")
    
    csv_manager = CSVManager(uploads_dir=uploads_dir)
    template_manager = TemplateManager(templates_dir=template_dir)
    field_mapper = FieldMapper()
    
    # Carregar CSV
    csv_path = os.path.join(uploads_dir, "participantes.csv")
    df = csv_manager.load_data(csv_path)
    assert not df.empty, "O DataFrame está vazio"
    
    # Obter colunas do CSV
    csv_columns = field_mapper.get_columns(df)
    assert len(csv_columns) > 0, "Nenhuma coluna encontrada no CSV"
    
    # Carregar template
    template_content = template_manager.load_template("certificado.html")
    assert template_content is not None, "Template não pôde ser carregado"
    
    # Encontrar placeholders no template
    import re
    placeholders = re.findall(r'{{([^}]+)}}', template_content)
    assert len(placeholders) > 0, "Nenhum placeholder encontrado no template"
    
    # Verificar mapeamento entre colunas CSV e placeholders
    missing_fields = field_mapper.validate_mapping(csv_columns, placeholders)
    assert len(missing_fields) == 0, f"Campos não encontrados no CSV: {missing_fields}"
    
    # Testar mapeamento com primeiro registro
    first_row = df.iloc[0].to_dict()
    template_data = field_mapper.map_data_to_template(first_row, placeholders)
    
    # Verificar se todos os placeholders receberam valores
    for placeholder in placeholders:
        assert placeholder in template_data, f"Placeholder {placeholder} não foi mapeado"
        assert template_data[placeholder] is not None, f"Valor para {placeholder} é None"
