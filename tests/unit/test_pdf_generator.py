"""
Testes de unidade para o módulo pdf_generator.py
Testa a geração de PDFs usando WeasyPrint
"""

import os
import sys
import pytest
import contextlib
from pathlib import Path
from io import StringIO

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = [pytest.mark.unit, pytest.mark.core]

@contextlib.contextmanager
def suppress_weasyprint_warnings():
    """Context manager para suprimir avisos do WeasyPrint no Windows durante os testes"""
    if sys.platform.startswith('win'):
        original_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            yield
        finally:
            sys.stderr = original_stderr
    else:
        yield

@pytest.fixture
def pdf_generator():
    """Fixture que retorna uma instância do PDFGenerator"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.pdf_generator import PDFGenerator
    
    # Use um diretório temporário para testes
    return PDFGenerator(output_dir="tests/temp_output")

@pytest.fixture
def cli_pdf_generator(tmp_path):
    """Fixture que retorna uma instância do PDFGenerator para testes CLI"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.pdf_generator import PDFGenerator
    
    # Use um diretório temporário específico para CLI
    output_path = tmp_path / "cli_output"
    output_path.mkdir(exist_ok=True)
    return PDFGenerator(output_dir=str(output_path))

@pytest.fixture
def sample_html():
    """Fixture que retorna um HTML de exemplo compatível com WeasyPrint"""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Certificado de Teste</title>
    <style>
        body { font-family: Arial, sans-serif; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Certificado de Teste</h1>
    <p>Este é um certificado de teste para João Silva.</p>
</body>
</html>"""

def test_init(pdf_generator):
    """Testa a inicialização do PDFGenerator"""
    assert pdf_generator.output_dir == "tests/temp_output"
    assert os.path.exists("tests/temp_output")

def test_generate_pdf_bytes(pdf_generator, sample_html):
    """Testa geração de PDF retornando bytes"""
    with suppress_weasyprint_warnings():
        pdf_bytes = pdf_generator.generate_pdf(sample_html)
    
    # Verificar se os bytes resultantes parecem um PDF válido
    assert pdf_bytes.startswith(b'%PDF-')
    assert len(pdf_bytes) > 100  # PDFs têm pelo menos alguns bytes

def test_generate_pdf_file(pdf_generator, sample_html, tmp_path):
    """Testa geração de PDF salvando em arquivo"""
    output_path = tmp_path / "test_output.pdf"
    with suppress_weasyprint_warnings():
        result_path = pdf_generator.generate_pdf(sample_html, output_path)
    
    # Verificar se o arquivo foi criado
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 100  # O arquivo deve ter algum conteúdo
    assert result_path == output_path

def test_generate_pdf_invalid_html(pdf_generator):
    """Testa geração de PDF com HTML inválido"""
    # HTML inválido ainda deve gerar um PDF
    invalid_html = "<htm><body>Inválido</html>"
    with suppress_weasyprint_warnings():
        pdf_bytes = pdf_generator.generate_pdf(invalid_html)
    
    # Mesmo com HTML inválido, deve gerar algo que pareça um PDF
    assert pdf_bytes.startswith(b'%PDF-')

def test_batch_generate(pdf_generator, sample_html, tmp_path):
    """Testa o método batch_generate"""
    # Cria vários conteúdos HTML e nomes de arquivo
    html_contents = [
        sample_html.replace("João Silva", "Pessoa 1"),
        sample_html.replace("João Silva", "Pessoa 2"),
        sample_html.replace("João Silva", "Pessoa 3")
    ]
    
    file_names = [
        "certificado1.pdf",
        "certificado2.pdf",
        "certificado3.pdf"    ]
    
    # Gera os PDFs em lote
    with suppress_weasyprint_warnings():
        pdf_paths = pdf_generator.batch_generate(html_contents, file_names)
    
    # Verifica se todos os arquivos foram criados
    assert len(pdf_paths) == 3
    for path in pdf_paths:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100

def test_batch_generate_error(pdf_generator, sample_html):
    """Testa erro no método batch_generate quando há tamanhos diferentes"""
    html_contents = [sample_html, sample_html]
    file_names = ["certificado1.pdf"]
    
    with pytest.raises(ValueError):
        pdf_generator.batch_generate(html_contents, file_names)

@pytest.mark.cli
def test_cli_pdf_generation(cli_pdf_generator, sample_html):
    """Testa a geração de PDF em contexto CLI"""
    # Gerar um PDF através do gerador CLI
    output_file = os.path.join(cli_pdf_generator.output_dir, "cli_test.pdf")
    with suppress_weasyprint_warnings():
        result = cli_pdf_generator.generate_pdf(sample_html, output_file)
    
    # Verificar se o arquivo foi criado corretamente
    assert os.path.exists(output_file)
    assert os.path.getsize(output_file) > 100
    assert output_file == result

@pytest.mark.cli
def test_cli_batch_pdf_generation(cli_pdf_generator, sample_html):
    """Testa a geração em lote de PDFs em contexto CLI"""
    # Criar dados de teste
    html_contents = [
        sample_html.replace("João Silva", "Usuário CLI 1"),
        sample_html.replace("João Silva", "Usuário CLI 2")
    ]
    
    file_names = [
        "cli_certificado1.pdf",
        "cli_certificado2.pdf"
    ]
    
    # Gerar PDFs em lote
    output_paths = cli_pdf_generator.batch_generate(html_contents, file_names)
    
    # Verificar resultados
    assert len(output_paths) == 2
    for path in output_paths:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 100
    
    # Verificar se os nomes dos arquivos estão corretos
    assert os.path.basename(output_paths[0]) == "cli_certificado1.pdf"
    assert os.path.basename(output_paths[1]) == "cli_certificado2.pdf"

# Limpar o diretório de saída após todos os testes
@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_output():
    yield
    import shutil
    if os.path.exists("tests/temp_output"):
        shutil.rmtree("tests/temp_output")
