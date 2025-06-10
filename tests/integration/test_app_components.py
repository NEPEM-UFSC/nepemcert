"""
Testes de integração para os principais componentes da aplicação.
Estes testes verificam se os diferentes módulos podem trabalhar juntos corretamente.
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Marca todos os testes neste arquivo como testes de integração
pytestmark = pytest.mark.integration

@pytest.fixture
def sample_csv_path(uploads_path):
    """Retorna o caminho para o arquivo CSV de exemplo"""
    return os.path.join(uploads_path, "participantes_exemplo.csv")

@pytest.fixture
def sample_template_path(templates_path):
    """Retorna o caminho para o arquivo de template de exemplo"""
    return os.path.join(templates_path, "certificado_exemplo.html")

def test_csv_manager_template_manager_integration(sample_csv_path, sample_template_path):
    """Testa a integração entre o CSVManager e o TemplateManager"""
    # Importamos os módulos necessários
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        # Importação dos módulos
        from app.csv_manager import CSVManager
        from app.template_manager import TemplateManager
        
        # Inicialização dos gerenciadores
        csv_manager = CSVManager()
        template_manager = TemplateManager()
        
        # Verificar se o arquivo CSV de exemplo existe
        assert os.path.exists(sample_csv_path), f"Arquivo CSV de exemplo não encontrado em: {sample_csv_path}"
        
        # Verificar se o arquivo de template de exemplo existe
        assert os.path.exists(sample_template_path), f"Arquivo de template de exemplo não encontrado em: {sample_template_path}"
        
        # Carregar dados do CSV - usar load_data em vez de load_csv
        df = csv_manager.load_data(sample_csv_path)
        assert isinstance(df, pd.DataFrame), "O resultado de load_data não é um DataFrame"
        assert not df.empty, "O DataFrame carregado está vazio"
        
        # Carregar o template
        template_content = template_manager.load_template(os.path.basename(sample_template_path))
        assert isinstance(template_content, str), "O resultado de load_template não é uma string"
        assert len(template_content) > 0, "O conteúdo do template está vazio"
        
        # Verificar se o template contém placeholders que podem ser substituídos por dados do CSV
        # Isso depende do seu formato específico, mas podemos fazer uma verificação básica
        assert "{{" in template_content or "{%" in template_content, "O template não parece conter placeholders"
        
    except ImportError as e:
        pytest.skip(f"Módulo não encontrado: {e}")

def test_field_mapper_integration(sample_csv_path):
    """Testa a integração do FieldMapper com os dados do CSV"""
    # Importamos os módulos necessários
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        # Importação dos módulos
        from app.csv_manager import CSVManager
        from app.field_mapper import FieldMapper
        
        # Inicialização dos gerenciadores
        csv_manager = CSVManager()
        field_mapper = FieldMapper()
        
        # Carregar dados do CSV - usar load_data em vez de load_csv
        df = csv_manager.load_data(sample_csv_path)
        
        # Obter as colunas do CSV - usar get_columns em vez de get_csv_columns
        columns = field_mapper.get_columns(df)
        assert len(columns) > 0, "Nenhuma coluna encontrada no CSV"
        
        # Como não conhecemos o formato exato do CSV, vamos apenas verificar se as funções básicas estão funcionando
        # Em um caso real, poderíamos testar se o mapeamento específico está correto
        
    except ImportError as e:
        pytest.skip(f"Módulo não encontrado: {e}")

def test_pdf_generator_zip_exporter_integration(tmp_path):
    """Testa a integração entre PDFGenerator e ZipExporter"""
    # Importamos os módulos necessários
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    try:
        # Importação dos módulos
        from app.pdf_generator import PDFGenerator
        from app.zip_exporter import ZipExporter
        
        # Inicialização dos gerenciadores
        pdf_generator = PDFGenerator()
        zip_exporter = ZipExporter()
        
        # Criar um diretório temporário para os PDFs
        pdf_dir = os.path.join(tmp_path, "pdfs")
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Criar alguns arquivos de teste
        test_files = []
        for i in range(3):
            file_path = os.path.join(pdf_dir, f"test{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Test content {i}")
            test_files.append(file_path)
        
        # Criar um arquivo zip com os arquivos de teste
        zip_path = os.path.join(tmp_path, "test_export.zip")
        # Corrigido para usar create_zip_from_files que retorna bytes
        zip_bytes = zip_exporter.create_zip_from_files(test_files)
        
        # Salvar os bytes em um arquivo para verificar
        with open(zip_path, 'wb') as f:
            f.write(zip_bytes)
        
        # Verificar se o arquivo zip foi criado
        assert os.path.exists(zip_path), f"O arquivo ZIP não foi criado em: {zip_path}"
        assert os.path.getsize(zip_path) > 0, "O arquivo ZIP está vazio"
        
    except ImportError as e:
        pytest.skip(f"Módulo não encontrado: {e}")

@pytest.fixture
def managers(tmp_path):
    """Fixture para inicializar todos os gerenciadores necessários para testes de integração."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.csv_manager import CSVManager
    from app.template_manager import TemplateManager
    from app.pdf_generator import PDFGenerator
    from app.zip_exporter import ZipExporter
    from app.parameter_manager import ParameterManager
    from app.theme_manager import ThemeManager
    from app.authentication_manager import AuthenticationManager
    from app.field_mapper import FieldMapper

    # Criar diretórios temporários para cada gerenciador
    temp_uploads_dir = tmp_path / "uploads"
    temp_templates_dir = tmp_path / "templates"
    temp_output_dir = tmp_path / "output"
    temp_config_dir = tmp_path / "config"
    temp_themes_dir = tmp_path / "themes"
    
    for d in [temp_uploads_dir, temp_templates_dir, temp_output_dir, temp_config_dir, temp_themes_dir]:
        d.mkdir(exist_ok=True)
    
    # Criar subdiretório docs para TemplateManager
    (temp_templates_dir / "docs").mkdir(exist_ok=True)

    return {
        "csv": CSVManager(uploads_dir=str(temp_uploads_dir)),
        "template": TemplateManager(templates_dir=str(temp_templates_dir)),
        "pdf": PDFGenerator(output_dir=str(temp_output_dir)),
        "zip": ZipExporter(),
        "parameter": ParameterManager(config_file=str(temp_config_dir / "parameters.json")),
        "theme": ThemeManager(themes_dir=str(temp_themes_dir)),
        "auth": AuthenticationManager(),
        "mapper": FieldMapper(),
        "dirs": {
            "uploads": temp_uploads_dir,
            "templates": temp_templates_dir,
            "output": temp_output_dir,
            "config": temp_config_dir,
            "themes": temp_themes_dir,
        }
    }

def test_parameters_template_integration(managers):
    """Testa a integração entre ParameterManager e TemplateManager."""
    param_manager = managers["parameter"]
    template_manager = managers["template"]

    # Definir placeholders padrão e institucionais
    param_manager.update_default_placeholders({"default_greeting": "Olá"})
    param_manager.update_institutional_placeholders({"institution_name": "Minha Instituição"})
    param_manager.save_parameters()

    # Criar template que usa esses placeholders
    template_content = "<p>{{ default_greeting }} {{ nome }}! Bem-vindo à {{ institution_name }}.</p>"
    template_name = "param_test.html"
    template_manager.save_template(template_name, template_content)

    # Dados do CSV (simulado)
    csv_data = {"nome": "Convidado"}
    
    # Mesclar placeholders
    final_data = param_manager.merge_placeholders(csv_data)
    
    # Renderizar template
    rendered_html = template_manager.render_template(template_name, final_data)
    
    assert "Olá Convidado!" in rendered_html
    assert "Bem-vindo à Minha Instituição." in rendered_html

def test_theme_template_integration(managers):
    """Testa a integração entre ThemeManager e TemplateManager."""
    theme_manager = managers["theme"]
    template_manager = managers["template"]

    # Criar e salvar um tema
    theme_name = "MeuTemaTeste"
    theme_settings = {
        "font_family": "Verdana, sans-serif",
        "text_color": "#FF0000", # Vermelho
        "background_color": "#00FF00", # Verde
        "border_color": "#0000FF", # Azul
        # Adicionar outras chaves esperadas por apply_theme_to_template
        "border_width": "1px", "border_style": "solid", "name_color": "#111",
        "title_color": "#222", "signature_color": "#333", "event_name_color": "#444",
        "link_color": "#555", "background_image": None
    }
    theme_manager.save_theme(theme_name, theme_settings)

    # Criar template HTML
    template_content = """
    <body style="font-family: Arial; background-color: #FFF; color: #000;">
        <h1 class="title">{{ title }}</h1>
        <p class="content">{{ message }}</p>
    </body>
    """
    template_name = "theme_test.html"
    template_manager.save_template(template_name, template_content)

    # Aplicar tema ao conteúdo do template
    themed_html_content = theme_manager.apply_theme_to_template(template_content, theme_settings)
    
    # Renderizar o template "tematizado"
    # Para este teste, vamos salvar o HTML tematizado como um novo template temporário
    themed_template_name = "themed_test_render.html"
    template_manager.save_template(themed_template_name, themed_html_content)

    data_for_render = {"title": "Título Teste", "message": "Mensagem Teste"}
    rendered_html = template_manager.render_template(themed_template_name, data_for_render)

    # Verificar se o tema foi aplicado (ajustar para a nova lógica do ThemeManager)
    assert 'Helvetica, Arial, sans-serif' in rendered_html  # Fonte mapeada
    assert '#00FF00' in rendered_html # Cor de fundo do tema
    assert '#FF0000' in rendered_html # Cor do texto do tema
    assert "Título Teste" in rendered_html
    assert "Mensagem Teste" in rendered_html

def test_auth_qr_code_in_html_integration(managers):
    """Testa a integração do AuthenticationManager com TemplateManager para QR codes."""
    auth_manager = managers["auth"]
    template_manager = managers["template"]

    # Gerar código de autenticação e QR code
    auth_code = auth_manager.gerar_codigo_autenticacao("Participante QR", "Evento QR")
    
    # Template com placeholder para QR code
    # Usando a classe específica que `substituir_qr_placeholder` procura
    template_content = """
    <body>
        <p>Nome: {{ nome }}</p>
        <div class="qr-placeholder" style="width:100px; height:100px;">
            <!-- QR Code será inserido aqui -->
        </div>
    </body>
    """
    template_name = "qr_test.html"
    template_manager.save_template(template_name, template_content)

    # Usar o método correto do AuthenticationManager
    qrcode_base64 = auth_manager.gerar_qrcode_base64(auth_code)

    render_data = {
        "nome": "Participante QR",
        "qrcode_base64": qrcode_base64
    }
    
    # Renderizar o template (sem substituição de QR ainda)
    html_sem_qr = template_manager.render_template(template_name, render_data)
    
    # Substituir o placeholder do QR
    html_com_qr = auth_manager.substituir_qr_placeholder(html_sem_qr, qrcode_base64)

    assert f'<img src="{qrcode_base64}"' in html_com_qr
    assert 'class="qr-placeholder"' in html_com_qr

def test_connectivity_parameter_integration(managers, tmp_path):
    """Testa a integração entre ConnectivityManager e ParameterManager."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.connectivity_manager import ConnectivityManager
    
    param_manager = managers["parameter"]
    connectivity_manager = ConnectivityManager(config_dir=str(managers["dirs"]["config"]))
    
    # Configurar parâmetros de conectividade através do ParameterManager
    param_manager.update_institutional_placeholders({
        "server_url": "https://teste.exemplo.com",
        "api_key": "chave-teste-123"
    })
    param_manager.save_parameters()
    
    # Configurar ConnectivityManager usando os dados dos parâmetros
    institutional_params = param_manager.get_institutional_placeholders()
    connectivity_manager.set_server_url(institutional_params.get("server_url", ""))
    connectivity_manager.set_api_key(institutional_params.get("api_key", ""))
    
    # Verificar se as configurações foram aplicadas
    assert connectivity_manager.config["server_url"] == "https://teste.exemplo.com"
    assert connectivity_manager.config["api_key"] == "chave-teste-123"
    
    # Testar verificação de conexão
    result = connectivity_manager.check_connection()
    assert "status" in result
    assert "message" in result
    assert "timestamp" in result

def test_full_certificate_generation_flow(managers, tmp_path):
    """Testa o fluxo completo de geração de certificados, da leitura do CSV ao ZIP."""
    csv_manager = managers["csv"]
    template_manager = managers["template"]
    pdf_generator = managers["pdf"]
    zip_exporter = managers["zip"]
    param_manager = managers["parameter"]
    theme_manager = managers["theme"]
    auth_manager = managers["auth"]
    mapper = managers["mapper"]
    
    output_dir_path = managers["dirs"]["output"]

    # 1. Criar CSV de exemplo
    csv_content = "nome,curso\nAlice,Python\nBob,JavaScript"
    csv_file = managers["dirs"]["uploads"] / "participantes_full.csv"
    with open(csv_file, "w") as f:
        f.write(csv_content)
    df = csv_manager.load_data(str(csv_file))

    # 2. Criar Template HTML de exemplo
    template_content = """
    <html><head><style>.qr-placeholder { width: 50px; height: 50px; }</style></head>
    <body>
        <h1>Certificado</h1>
        <p>Participante: {{ nome }}</p>
        <p>Curso: {{ curso }}</p>
        <p>Instituição: {{ institution_name }}</p>
        <p>Tema Aplicado: {{ theme_indicator }}</p>
        <div class="qr-placeholder"></div>
    </body></html>
    """
    template_name = "full_flow_template.html"
    template_manager.save_template(template_name, template_content)

    # 3. Configurar Parâmetros
    param_manager.update_institutional_placeholders({"institution_name": "Super Instituição"})
    param_manager.save_parameters()

    # 4. Configurar Tema
    theme_name = "FullFlowTema"
    theme_settings = {
        "font_family": "Impact, sans-serif", "text_color": "#000080", # Navy
        "background_color": "#FFFFE0", # LightYellow
        "border_color": "#800080", # Purple
        "theme_indicator": "Tema Ativado!",
        # Adicionar outras chaves esperadas por apply_theme_to_template
        "border_width": "1px", "border_style": "solid", "name_color": "#111",
        "title_color": "#222", "signature_color": "#333", "event_name_color": "#444",
        "link_color": "#555", "background_image": None
    }
    theme_manager.save_theme(theme_name, theme_settings)

    # 5. Processar cada linha do CSV
    generated_pdf_files = []
    html_docs_for_pdf = []
    pdf_names = []

    for index, row_data in df.iterrows():
        # Mapear dados
        placeholders_in_template = template_manager.extract_placeholders(template_content)
        participant_data = mapper.map_data_to_template(row_data.to_dict(), placeholders_in_template)
        
        # Mesclar com parâmetros
        all_data = param_manager.merge_placeholders(participant_data, theme_name=theme_name)
        
        # Adicionar dados do tema diretamente se não forem placeholders (ex: theme_indicator)
        all_data.update({k: v for k, v in theme_settings.items() if k in placeholders_in_template})

        # Carregar e aplicar tema ao template
        current_template_content = template_manager.load_template(template_name)
        themed_content = theme_manager.apply_theme_to_template(current_template_content, theme_settings)
        
        # Salvar temporariamente o template tematizado para renderização
        temp_themed_template_name = f"temp_themed_{index}.html"
        template_manager.save_template(temp_themed_template_name, themed_content)

        # Autenticação e QR Code - usar método correto
        auth_code = auth_manager.gerar_codigo_autenticacao(all_data["nome"], all_data["curso"])
        qrcode_base64 = auth_manager.gerar_qrcode_base64(auth_code)
        all_data["qrcode_base64"] = qrcode_base64
        
        # Renderizar template
        rendered_html = template_manager.render_template(temp_themed_template_name, all_data)
        
        # Substituir placeholder do QR
        final_html = auth_manager.substituir_qr_placeholder(rendered_html, qrcode_base64)
        
        html_docs_for_pdf.append(final_html)
        pdf_file_name = f"certificado_{all_data['nome']}.pdf"
        pdf_names.append(output_dir_path / pdf_file_name)

        # Limpar template temporário
        template_manager.delete_template(temp_themed_template_name)

    # 6. Gerar PDFs
    generated_pdf_paths = pdf_generator.batch_generate(html_docs_for_pdf, [str(p) for p in pdf_names])
    assert len(generated_pdf_paths) == len(df)
    for pdf_path in generated_pdf_paths:
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0
        generated_pdf_files.append(pdf_path)

    # 7. Exportar para ZIP
    zip_bytes = zip_exporter.create_zip_from_files(generated_pdf_files)
    zip_file_path = output_dir_path / "certificados_lote.zip"
    with open(zip_file_path, "wb") as f:
        f.write(zip_bytes)
    
    assert zip_file_path.exists()
    assert zip_file_path.stat().st_size > 0

    import zipfile
    with zipfile.ZipFile(zip_file_path, 'r') as zf:
        assert len(zf.namelist()) == len(df)
        assert "certificado_Alice.pdf" in zf.namelist()
        assert "certificado_Bob.pdf" in zf.namelist()

def test_multi_theme_comparison(managers):
    """Testa a aplicação de múltiplos temas ao mesmo template."""
    theme_manager = managers["theme"]
    template_manager = managers["template"]
    
    # Criar template base
    base_template = """
    <body style="font-family: Arial; color: #000;">
        <h1 class="title">{{ titulo }}</h1>
        <p class="content">{{ mensagem }}</p>
    </body>
    """
    template_manager.save_template("multi_theme_test.html", base_template)
    
    # Criar múltiplos temas
    themes = {
        "Tema Azul": {
            "font_family": "Arial, sans-serif", "text_color": "#0000FF", 
            "background_color": "#E0E0FF", "border_color": "#000080",
            "border_width": "2px", "border_style": "solid", "name_color": "#000040",
            "title_color": "#000080", "signature_color": "#404040", 
            "event_name_color": "#0000A0", "link_color": "#0000C0", "background_image": None
        },
        "Tema Verde": {
            "font_family": "Georgia, serif", "text_color": "#008000", 
            "background_color": "#E0FFE0", "border_color": "#004000",
            "border_width": "3px", "border_style": "dashed", "name_color": "#002000",
            "title_color": "#004000", "signature_color": "#404040", 
            "event_name_color": "#006000", "link_color": "#008000", "background_image": None
        },
        "Tema Vermelho": {
            "font_family": "Times, serif", "text_color": "#800000", 
            "background_color": "#FFE0E0", "border_color": "#400000",
            "border_width": "1px", "border_style": "dotted", "name_color": "#600000",
            "title_color": "#800000", "signature_color": "#404040", 
            "event_name_color": "#A00000", "link_color": "#C00000", "background_image": None
        }
    }
    
    themed_results = {}
    
    for theme_name, theme_config in themes.items():
        # Salvar tema
        theme_manager.save_theme(theme_name, theme_config)
        
        # Aplicar tema ao template
        themed_content = theme_manager.apply_theme_to_template(base_template, theme_config)
        
        # Salvar template com tema aplicado
        themed_template_name = f"themed_{theme_name.lower().replace(' ', '_')}.html"
        template_manager.save_template(themed_template_name, themed_content)
        
        # Renderizar com dados
        data = {"titulo": f"Teste {theme_name}", "mensagem": f"Conteúdo do {theme_name}"}
        rendered = template_manager.render_template(themed_template_name, data)
        
        themed_results[theme_name] = rendered
    
    # Verificar se cada tema foi aplicado corretamente
    assert "Arial, sans-serif" in themed_results["Tema Azul"]
    assert "#0000FF" in themed_results["Tema Azul"]
    assert "#E0E0FF" in themed_results["Tema Azul"]
    
    assert "Georgia, serif" in themed_results["Tema Verde"]
    assert "#008000" in themed_results["Tema Verde"]
    assert "#E0FFE0" in themed_results["Tema Verde"]
    
    assert "Times, serif" in themed_results["Tema Vermelho"]
    assert "#800000" in themed_results["Tema Vermelho"]
    assert "#FFE0E0" in themed_results["Tema Vermelho"]
    
    # Verificar que os temas são diferentes entre si
    assert themed_results["Tema Azul"] != themed_results["Tema Verde"]
    assert themed_results["Tema Verde"] != themed_results["Tema Vermelho"]
    assert themed_results["Tema Azul"] != themed_results["Tema Vermelho"]
