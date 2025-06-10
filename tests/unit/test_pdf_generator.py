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
    """Testa o método batch_generate com erro (número de arquivos e HTMLs diferente)"""
    html_contents = [sample_html, sample_html]
    file_names = ["certificado1.pdf"] # Apenas um nome de arquivo
    
    with pytest.raises(ValueError):
        pdf_generator.batch_generate(html_contents, file_names)

def test_generate_pdf_error(pdf_generator, monkeypatch):
    """Testa o método generate_pdf quando ocorre um erro na geração"""
    # Mock para simular erro na escrita do PDF
    def mock_write_pdf(*args, **kwargs):
        raise Exception("Erro simulado na escrita do PDF")

    monkeypatch.setattr("weasyprint.HTML.write_pdf", mock_write_pdf)
    
    with pytest.raises(RuntimeError) as excinfo:
        pdf_generator.generate_pdf("<html></html>", "dummy.pdf")
    assert "Erro ao gerar PDF: Erro simulado na escrita do PDF" in str(excinfo.value)

def test_clean_output_directory(pdf_generator, tmp_path):
    """Testa o método clean_output_directory"""
    # Configurar o diretório de saída para tmp_path
    pdf_generator.output_dir = str(tmp_path)
    
    # Criar alguns arquivos no diretório de saída
    (tmp_path / "file1.pdf").touch()
    (tmp_path / "file2.txt").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file3.pdf").touch()

    pdf_generator.clean_output_directory()
    
    # Verificar se os arquivos foram removidos, mas o subdiretório não
    assert not (tmp_path / "file1.pdf").exists()
    assert not (tmp_path / "file2.txt").exists()
    assert (tmp_path / "subdir").exists() # clean_output_directory só remove arquivos
    assert (tmp_path / "subdir" / "file3.pdf").exists()

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

# --- New tests for parallel batch generation ---
from unittest.mock import patch, MagicMock

def test_parallel_batch_generate_success(pdf_generator, sample_html, tmp_path):
    """Testa batch_generate com ProcessPoolExecutor para sucesso."""
    pdf_generator.output_dir = str(tmp_path) # Usar tmp_path para saida
    html_contents = [sample_html] * 3
    file_names_only = ["cert1.pdf", "cert2.pdf", "cert3.pdf"]
    # batch_generate now expects full paths in file_names argument
    full_file_paths = [str(tmp_path / name) for name in file_names_only]

    # Mock generate_pdf para simular sucesso e retornar o caminho do arquivo
    # A função _execute_generate_pdf dentro de batch_generate chama self.generate_pdf
    # Então precisamos mockar PDFGenerator.generate_pdf
    
    # Define what the mocked generate_pdf should return for each call
    # It should return the output_path it was given.
    def mock_generate_pdf_side_effect(html_content, output_path, orientation):
        # Simulate file creation for assertion
        with open(output_path, 'wb') as f:
            f.write(b'%PDF-fake')
        return output_path

    with patch.object(pdf_generator, 'generate_pdf', side_effect=mock_generate_pdf_side_effect) as mock_gen_pdf:
        # Mock os.cpu_count para controlar o número de workers, se necessário para o teste
        with patch('os.cpu_count', return_value=2): 
            generated_paths = pdf_generator.batch_generate(html_contents, full_file_paths)

    assert len(generated_paths) == 3
    # Verificar se generate_pdf foi chamado para cada input
    assert mock_gen_pdf.call_count == 3 
    for path in generated_paths:
        assert os.path.exists(path) # Verifique se o arquivo simulado existe
        assert Path(path).parent == tmp_path


def test_parallel_batch_generate_with_errors(pdf_generator, sample_html, tmp_path, capsys):
    """Testa batch_generate com ProcessPoolExecutor quando alguns PDFs falham."""
    pdf_generator.output_dir = str(tmp_path)
    html_contents = [sample_html] * 4
    file_names_only = ["s1.pdf", "f1.pdf", "s2.pdf", "f2.pdf"]
    full_file_paths = [str(tmp_path / name) for name in file_names_only]

    # Mock generate_pdf para simular sucesso para alguns e erro para outros
    def mock_generate_pdf_side_effect(html_content, output_path, orientation):
        if "f" in Path(output_path).name: # Simular falha para f1.pdf e f2.pdf
            raise RuntimeError(f"Simulated error for {output_path}")
        else: # Sucesso para s1.pdf e s2.pdf
             # Simulate file creation for assertion
            with open(output_path, 'wb') as f:
                f.write(b'%PDF-fake-success')
            return output_path
            
    with patch.object(pdf_generator, 'generate_pdf', side_effect=mock_generate_pdf_side_effect) as mock_gen_pdf:
        with patch('os.cpu_count', return_value=2):
            generated_paths = pdf_generator.batch_generate(html_contents, full_file_paths)
    
    assert len(generated_paths) == 2 # Apenas 2 devem ter sucesso
    assert mock_gen_pdf.call_count == 4 # Chamado para todos os 4
    
    successful_files = [Path(p).name for p in generated_paths]
    assert "s1.pdf" in successful_files
    assert "s2.pdf" in successful_files
    assert "f1.pdf" not in successful_files
    assert "f2.pdf" not in successful_files

    # Verificar a saída de erro capturada (stderr)
    captured = capsys.readouterr()
    assert "Error generating PDF for" in captured.err # Verifica se as mensagens de erro foram impressas
    assert str(tmp_path / "f1.pdf") in captured.err
    assert str(tmp_path / "f2.pdf") in captured.err
    assert "A PDF generation failed:" in captured.err # Verifica a mensagem do loop principal


# Limpar o diretório de saída após todos os testes
@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_output():
    yield
    import shutil
    if os.path.exists("tests/temp_output"):
        shutil.rmtree("tests/temp_output")
