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
    # Verificar se pelo menos um PDF foi gerado para cada nome no CSV
    assert len(pdf_files) == 2 # Baseado no CSV de exemplo

    # Verificar se os nomes dos participantes estão nos nomes dos arquivos PDF (aproximado)
    assert any("joao" in f.lower() for f in pdf_files)
    assert any("maria" in f.lower() for f in pdf_files)

def test_cli_generate_with_zip_integration(cli_runner, nepemcert_cli, temp_workspace, monkeypatch):
    """
    Teste de integração do comando generate com a opção --zip.
    """
    monkeypatch.chdir(temp_workspace)
    
    csv_path = os.path.join(temp_workspace, "uploads", "participantes.csv")
    template_path = os.path.join(temp_workspace, "templates", "certificado.html")
    output_dir = os.path.join(temp_workspace, "output")
    
    result = cli_runner.invoke(nepemcert_cli, [
        "generate",
        csv_path,
        template_path,
        "--output", output_dir,
        "--zip"
    ])
    
    assert result.exit_code == 0
    assert "Gerando certificados" in result.output
    assert "Arquivo ZIP gerado em" in result.output
    
    # Verificar se o arquivo ZIP foi gerado
    zip_files = [f for f in os.listdir(output_dir) if f.endswith(".zip")]
    assert len(zip_files) == 1, "Nenhum arquivo ZIP ou mais de um foi gerado"
    
    zip_file_path = os.path.join(output_dir, zip_files[0])
    import zipfile
    with zipfile.ZipFile(zip_file_path, 'r') as zf:
        # Verificar se o ZIP contém os PDFs esperados
        pdf_in_zip = [name for name in zf.namelist() if name.endswith(".pdf")]
        assert len(pdf_in_zip) == 2 # Baseado no CSV de exemplo

def test_cli_config_integration(cli_runner, nepemcert_cli, temp_workspace, monkeypatch):
    """
    Teste de integração para comandos de configuração (exemplo: definir parâmetro).
    """
    monkeypatch.chdir(temp_workspace)
    config_dir = os.path.join(temp_workspace, "config")
    os.makedirs(config_dir, exist_ok=True)
    
    # Criar um ParameterManager para verificar o arquivo
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.parameter_manager import ParameterManager
    param_manager = ParameterManager(config_file=os.path.join(config_dir, "parameters.json"))
    
    # Antes de qualquer comando config, o valor não deve existir ou ser padrão
    assert param_manager.get_institutional_placeholders().get("test_param") is None

    # Como o comando 'config set' não está definido nas instruções, vamos testar diretamente o ParameterManager
    param_manager.update_institutional_placeholders({"cli_test_param": "CLI Value"})
    param_manager.save_parameters()

    reloaded_param_manager = ParameterManager(config_file=os.path.join(config_dir, "parameters.json"))
    assert reloaded_param_manager.get_institutional_placeholders().get("cli_test_param") == "CLI Value"

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
    # Ajustar regex para pegar apenas o nome do placeholder, sem os espaços ou chaves
    placeholders = re.findall(r'{{\s*([\w_]+)\s*}}', template_content)
    placeholders = list(set(placeholders)) # Remover duplicatas
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

def test_complete_certificate_generation_flow(temp_workspace):
    """
    Teste do fluxo completo de geração de certificados incluindo autenticação e QR codes
    """
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.csv_manager import CSVManager
    from app.template_manager import TemplateManager
    from app.pdf_generator import PDFGenerator
    from app.parameter_manager import ParameterManager
    from app.authentication_manager import AuthenticationManager
    from app.field_mapper import FieldMapper
    from app.zip_exporter import ZipExporter
    
    # Configurar diretórios
    uploads_dir = os.path.join(temp_workspace, "uploads")
    template_dir = os.path.join(temp_workspace, "templates")
    output_dir = os.path.join(temp_workspace, "output")
    config_dir = os.path.join(temp_workspace, "config")
    
    # Inicializar gerenciadores
    csv_manager = CSVManager(uploads_dir=uploads_dir)
    template_manager = TemplateManager(templates_dir=template_dir)
    pdf_generator = PDFGenerator(output_dir=output_dir)
    param_manager = ParameterManager(config_file=os.path.join(config_dir, "parameters.json"))
    auth_manager = AuthenticationManager()
    field_mapper = FieldMapper()
    zip_exporter = ZipExporter()
    
    # Configurar parâmetros institucionais
    param_manager.update_institutional_placeholders({
        "instituicao": "Universidade Teste",
        "coordenador": "Dr. João Silva",
        "diretor": "Profa. Maria Santos"
    })
    param_manager.save_parameters()
    
    # Criar template com placeholder para QR code
    template_with_qr = """<!DOCTYPE html>
<html>
<head>
    <title>Certificado</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .certificado { border: 2px solid #000; padding: 30px; }
        .qr-placeholder { position: absolute; bottom: 20px; right: 20px; width: 80px; height: 80px; }
    </style>
</head>
<body>
    <div class="certificado">
        <h1>CERTIFICADO</h1>
        <p>Certificamos que <strong>{{nome}}</strong> participou do curso <strong>{{curso}}</strong></p>
        <p>Realizado em {{data}} com carga horária de {{carga_horaria}}</p>
        <p>Instituição: {{instituicao}}</p>
        <div class="qr-placeholder"><!-- QR Code --></div>
    </div>
</body>
</html>"""
    
    template_manager.save_template("certificado_com_qr.html", template_with_qr)
    
    # Carregar dados do CSV
    csv_path = os.path.join(uploads_dir, "participantes.csv")
    df = csv_manager.load_data(csv_path)
    
    generated_files = []
    
    # Processar cada participante
    for index, row in df.iterrows():
        participant_data = row.to_dict()
        
        # Gerar código de autenticação
        auth_code = auth_manager.gerar_codigo_autenticacao(
            participant_data["nome"],
            participant_data["curso"]
        )
        
        # Salvar código
        auth_manager.salvar_codigo(
            auth_code,
            participant_data["nome"],
            participant_data["curso"],
            participant_data["data"],
            "Local Teste",
            participant_data["carga_horaria"]
        )
        
        # Mesclar dados com parâmetros
        final_data = param_manager.merge_placeholders(participant_data)
        
        # Gerar QR code
        qr_base64 = auth_manager.gerar_qrcode_base64(auth_code)
        
        # Renderizar template
        html_content = template_manager.render_template("certificado_com_qr.html", final_data)
        
        # Substituir placeholder do QR
        html_with_qr = auth_manager.substituir_qr_placeholder(html_content, qr_base64)
        
        # Gerar PDF
        pdf_name = f"certificado_{participant_data['nome'].replace(' ', '_')}.pdf"
        pdf_path = os.path.join(output_dir, pdf_name)
        pdf_generator.generate_pdf(html_with_qr, pdf_path)
        
        generated_files.append(pdf_path)
        
        # Verificar se o arquivo foi criado
        assert os.path.exists(pdf_path), f"PDF não foi gerado: {pdf_path}"
    
    # Criar arquivo ZIP com todos os certificados
    zip_bytes = zip_exporter.create_zip_from_files(generated_files)
    zip_path = os.path.join(output_dir, "certificados_lote.zip")
    
    with open(zip_path, 'wb') as f:
        f.write(zip_bytes)
    
    # Verificar ZIP
    assert os.path.exists(zip_path), "Arquivo ZIP não foi criado"
    assert os.path.getsize(zip_path) > 0, "Arquivo ZIP está vazio"
    
    # Verificar conteúdo do ZIP
    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zip_contents = zf.namelist()
        assert len(zip_contents) == len(df), "Número de arquivos no ZIP não confere"
        for pdf_file in generated_files:
            assert os.path.basename(pdf_file) in zip_contents, f"Arquivo {pdf_file} não está no ZIP"

def test_theme_parameter_integration(temp_workspace):
    """
    Teste da integração entre ThemeManager e ParameterManager
    """
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.theme_manager import ThemeManager
    from app.parameter_manager import ParameterManager
    from app.template_manager import TemplateManager
    
    # Configurar diretórios
    config_dir = os.path.join(temp_workspace, "config")
    themes_dir = os.path.join(temp_workspace, "themes")
    template_dir = os.path.join(temp_workspace, "templates")
    
    os.makedirs(themes_dir, exist_ok=True)
    
    # Inicializar gerenciadores
    theme_manager = ThemeManager(themes_dir=themes_dir)
    param_manager = ParameterManager(config_file=os.path.join(config_dir, "parameters.json"))
    template_manager = TemplateManager(templates_dir=template_dir)
    
    # Criar um tema personalizado
    custom_theme = {
        "font_family": "Georgia, serif",
        "text_color": "#2c3e50",
        "background_color": "#ecf0f1",
        "border_color": "#3498db",
        "border_width": "3px",
        "border_style": "solid",
        "name_color": "#e74c3c",
        "title_color": "#2980b9",
        "signature_color": "#34495e",
        "event_name_color": "#27ae60",
        "link_color": "#9b59b6",
        "background_image": None
    }
    
    theme_name = "Tema Personalizado"
    theme_manager.save_theme(theme_name, custom_theme)
    
    # Configurar placeholders específicos do tema
    param_manager.update_theme_placeholders(theme_name, {
        "tema_aplicado": "Sim",
        "estilo_especial": "Tema Personalizado Ativado"
    })
    param_manager.save_parameters()
    
    # Criar template que usa placeholders do tema
    template_content = """
    <body style="font-family: Arial; color: #000;">
        <h1 class="title">{{titulo}}</h1>
        <p class="content">{{tema_aplicado}} - {{estilo_especial}}</p>
    </body>
    """
    
    template_manager.save_template("tema_test.html", template_content)
    
    # Aplicar tema ao template
    themed_content = theme_manager.apply_theme_to_template(template_content, custom_theme)
    
    # Verificar se o tema foi aplicado
    assert "Georgia, serif" in themed_content
    assert "#2c3e50" in themed_content
    assert "#ecf0f1" in themed_content
    
    # Criar template temporário com tema aplicado
    template_manager.save_template("tema_applied.html", themed_content)
    
    # Mesclar dados com placeholders do tema
    data = {"titulo": "Teste de Tema"}
    final_data = param_manager.merge_placeholders(data, theme_name=theme_name)
    
    # Verificar se os placeholders do tema foram incluídos
    assert final_data["tema_aplicado"] == "Sim"
    assert final_data["estilo_especial"] == "Tema Personalizado Ativado"
    
    # Renderizar template final
    rendered_html = template_manager.render_template("tema_applied.html", final_data)
    
    # Verificar conteúdo renderizado
    assert "Teste de Tema" in rendered_html
    assert "Sim - Tema Personalizado Ativado" in rendered_html
    assert "Georgia, serif" in rendered_html

def test_error_handling_integration(temp_workspace):
    """
    Teste de tratamento de erros na integração entre componentes
    """
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.csv_manager import CSVManager
    from app.template_manager import TemplateManager
    from app.pdf_generator import PDFGenerator
    
    # Configurar diretórios
    uploads_dir = os.path.join(temp_workspace, "uploads")
    template_dir = os.path.join(temp_workspace, "templates")
    output_dir = os.path.join(temp_workspace, "output")
    
    # Inicializar gerenciadores
    csv_manager = CSVManager(uploads_dir=uploads_dir)
    template_manager = TemplateManager(templates_dir=template_dir)
    pdf_generator = PDFGenerator(output_dir=output_dir)
    
    # Teste 1: CSV com dados inválidos
    invalid_csv_path = os.path.join(uploads_dir, "invalid.csv")
    with open(invalid_csv_path, 'w') as f:
        f.write("dados,malformados\n\"sem,fechamento\noutralinha")
    
    with pytest.raises(ValueError):
        csv_manager.load_data(invalid_csv_path)
    
    # Teste 2: Template inexistente
    assert template_manager.load_template("inexistente.html") is None
    
    with pytest.raises(FileNotFoundError):
        template_manager.render_template("inexistente.html", {"dados": "teste"})
    
    # Teste 3: HTML problemático para PDF
    problematic_html = """
    <html>
        <body>
            <iframe src="test"></iframe>
            <div style="display: flex;">Flexbox não suportado</div>
        </body>
    </html>
    """
    
    # Verificar se o template detecta problemas
    warnings = template_manager.validate_template(problematic_html)
    assert len(warnings) > 0
    assert any("iframe" in warning.lower() for warning in warnings)
    assert any("flex" in warning.lower() for warning in warnings)
    
    # Teste 4: PDF com HTML vazio ou inválido
    with pytest.raises(RuntimeError):
        pdf_generator.generate_pdf("", os.path.join(output_dir, "empty.pdf"))
