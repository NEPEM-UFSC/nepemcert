"""
Testes de unidade para o módulo theme_manager.py
"""
import os
import sys
import json
import pytest
import base64
from pathlib import Path
from unittest.mock import patch, mock_open

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def temp_themes_dir(tmp_path):
    """Cria um diretório de temas temporário."""
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()
    return str(themes_dir)

@pytest.fixture
def theme_manager(temp_themes_dir):
    """Fixture que retorna uma instância do ThemeManager com um diretório de temas temporário."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    # Mock PREDEFINED_THEMES para isolar dos temas reais
    with patch('app.theme_manager.PREDEFINED_THEMES', {"Acadêmico Clássico": {"font_family": "Times"}, "Minimalista Moderno": {"font_family": "Arial"}}):
        from app.theme_manager import ThemeManager
        return ThemeManager(themes_dir=temp_themes_dir)

@pytest.fixture
def sample_theme_settings():
    return {
        "font_family": "Arial, sans-serif",
        "text_color": "#333333",
        "background_color": "#ffffff",
        "border_color": "#1a5276",
        "name_color": "#1a4971",
        "title_color": "#1a5276",
        "signature_color": "#333333",
        "event_name_color": "#1a5276",
        "link_color": "#1a5276",
        "background_image": None
    }

def test_init_ensure_theme_files_exist(temp_themes_dir):
    """Testa se _ensure_theme_files_exist cria arquivos para temas pré-definidos ausentes."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    predefined_themes_mock = {
        "Meu Tema Predefinido": {"color": "blue"},
        "Acadêmico Clássico": {"font_family": "Times"} # Este deve ter um arquivo mapeado
    }
    # theme_files no ThemeManager mapeia "Acadêmico Clássico" para "academico_classico.json"
    
    with patch('app.theme_manager.PREDEFINED_THEMES', predefined_themes_mock):
        from app.theme_manager import ThemeManager
        manager = ThemeManager(themes_dir=temp_themes_dir)
        
        # Verifica se o arquivo para "Acadêmico Clássico" foi criado
        expected_file = Path(temp_themes_dir) / "academico_classico.json"
        assert expected_file.exists()
        with open(expected_file, 'r') as f:
            data = json.load(f)
            assert data == {"font_family": "Times"}

        # "Meu Tema Predefinido" não está em self.theme_files, então não deve ser criado por _ensure_theme_files_exist
        # mas será carregado por _load_all_themes diretamente do PREDEFINED_THEMES mockado.
        assert "Meu Tema Predefinido" in manager.all_themes 


def test_load_all_themes(theme_manager, temp_themes_dir, sample_theme_settings):
    """Testa o carregamento de todos os temas (arquivos e pré-definidos)."""
    # Salvar um tema personalizado
    custom_theme_name = "meu_tema_customizado"
    custom_theme_file = Path(temp_themes_dir) / f"{custom_theme_name}.json"
    with open(custom_theme_file, 'w') as f:
        json.dump(sample_theme_settings, f)

    # Recarregar os temas (ou criar nova instância)
    from app.theme_manager import ThemeManager
    with patch('app.theme_manager.PREDEFINED_THEMES', {"Acadêmico Clássico": {"font_family": "Times"}}):
         manager = ThemeManager(themes_dir=temp_themes_dir)

    assert "Acadêmico Clássico" in manager.all_themes # Pré-definido (mockado)
    assert "Meu Tema Customizado" in manager.all_themes # Carregado do arquivo
    assert manager.all_themes["Meu Tema Customizado"] == sample_theme_settings

def test_save_and_load_theme(theme_manager, temp_themes_dir, sample_theme_settings):
    """Testa salvar e carregar um tema."""
    theme_name = "Teste Salvar"
    theme_manager.save_theme(theme_name, sample_theme_settings)
    
    loaded_settings = theme_manager.load_theme(theme_name)
    assert loaded_settings == sample_theme_settings
    
    # Testar carregamento de tema pré-definido (mockado)
    assert theme_manager.load_theme("Acadêmico Clássico") == {"font_family": "Times"}
    assert theme_manager.load_theme("Tema Inexistente") is None

def test_list_themes(theme_manager, temp_themes_dir, sample_theme_settings):
    """Testa a listagem de temas."""
    theme_manager.save_theme("Tema A", sample_theme_settings)
    theme_manager.save_theme("Tema B", sample_theme_settings)
    
    # Recriar para forçar releitura dos arquivos
    from app.theme_manager import ThemeManager
    with patch('app.theme_manager.PREDEFINED_THEMES', {"Acadêmico Clássico": {}, "Minimalista Moderno": {}}):
        manager = ThemeManager(themes_dir=temp_themes_dir)
        themes = manager.list_themes()

    # Verificar se os temas salvos estão na lista
    assert "Tema A" in themes
    assert "Tema B" in themes
    # Verificar se pelo menos um tema pré-definido está na lista
    predefined_themes = [t for t in themes if t in ["Acadêmico Clássico", "Minimalista Moderno"]]
    assert len(predefined_themes) > 0


def predefined_theme_names_from_files(manager):
    """Helper para obter nomes de temas pré-definidos que têm arquivos."""
    names = []
    for name, file_name in manager.theme_files.items():
        if (Path(manager.themes_dir) / file_name).exists():
            names.append(name)
    return names


def test_delete_theme(theme_manager, temp_themes_dir, sample_theme_settings):
    """Testa a exclusão de um tema."""
    custom_theme_name = "TemaParaExcluir"
    theme_manager.save_theme(custom_theme_name, sample_theme_settings)
    assert theme_manager.load_theme(custom_theme_name) is not None
    
    assert theme_manager.delete_theme(custom_theme_name)
    assert theme_manager.load_theme(custom_theme_name) is None
    
    # Tentar excluir tema pré-definido (não deve permitir)
    assert not theme_manager.delete_theme("Acadêmico Clássico")
    assert theme_manager.load_theme("Acadêmico Clássico") is not None # Deve continuar existindo

def test_apply_theme_to_template(theme_manager):
    """Testa a aplicação de um tema a um template HTML com a nova lógica de <style> block."""
    html_content_template = """<!DOCTYPE html>
<html>
<head>
    <title>Teste</title>
    <style>
        /* Estilos base do template */
        body {{ font-family: 'Times New Roman'; background-color: #f0f0f0; }}
        .title {{ color: #000000; }}
    </style>
</head>
<body>
    <div class="certificate">
        <h1 class="title">Certificado</h1>
        <p class="content">Participante <span class="participant-name">Nome</span> do evento <span class="event-name">EventoX</span>.</p>
        <div class="signature-line"></div>
        <p class="signature-name">Assinatura</p>
        <a href="#" class="nepemcert-link">Link</a>
    </div>
</body>
</html>"""

    theme_settings = {
        "font_family": "'Montserrat', 'Helvetica Neue', Arial, sans-serif", # Um da lista safe_fonts
        "text_color": "#111111",
        "background_color": "#EEEEEE",
        "border_color": "#CCCCCC",
        "border_width": "5px",
        "border_style": "dotted",
        "title_color": "#222222",
        "name_color": "#333333",
        "event_name_color": "#444444",
        "signature_color": "#555555",
        "link_color": "#666666",
        "background_image": None
    }
    
    modified_html = theme_manager.apply_theme_to_template(html_content_template, theme_settings)
    
    # 1. Verificar se o bloco <style id="nepemcert-theme-styles"> foi injetado antes de </head>
    assert '<style type="text/css" id="nepemcert-theme-styles">' in modified_html
    assert '</style>\n</head>' in modified_html # Checa se o style foi inserido antes de </head>

    # 2. Verificar regras CSS específicas (com !important)
    # Font family (após mapeamento para safe_fonts)
    expected_font_family = "Helvetica, Arial, sans-serif" # Mapeado de 'Montserrat'...
    assert f"body {{ font-family: {expected_font_family} !important; }}" in modified_html
    
    # Text color (aplicado a múltiplos seletores)
    assert f"body, .content, .text, .verification, .footer, p, div {{ color: #111111 !important; }}" in modified_html
    
    # Background color (aplicado a múltiplos seletores)
    assert f"body, .certificate, .certificate-container {{ background-color: #EEEEEE !important; }}" in modified_html
    
    # Border
    assert f"body, .certificate, .certificate-container {{ border: 5px dotted #CCCCCC !important; }}" in modified_html
    
    # Title color
    assert f".title, h1 {{ color: #222222 !important; }}" in modified_html
    
    # Name color
    assert f".name, .participant-name {{ color: #333333 !important; border-bottom-color: #333333 !important; }}" in modified_html
    
    # Event name color
    assert f".event-name, .evento {{ color: #444444 !important; }}" in modified_html
    
    # Signature color
    assert f".signature-line {{ border-top-color: #555555 !important; }}" in modified_html
    assert f".signature-name, .assinatura p, .signature div {{ color: #555555 !important; }}" in modified_html
    
    # Link color
    assert f"a, .nepemcert-link {{ color: #666666 !important; }}" in modified_html

def test_apply_theme_with_background_image(theme_manager):
    """Testa a aplicação de tema com imagem de fundo."""
    html_content_template = """<!DOCTYPE html>
<html><head><title>BG Test</title></head><body>Conteúdo</body></html>"""
    
    # Simular uma imagem base64
    fake_base64_image = "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=" # Exemplo de um GIF pequeno
    
    theme_settings = {
        "background_image": fake_base64_image
    }
    
    modified_html = theme_manager.apply_theme_to_template(html_content_template, theme_settings)
    
    expected_bg_image_css = f"background-image: url('data:image/png;base64,{fake_base64_image}') !important;"
    assert expected_bg_image_css in modified_html
    assert "background-size: cover !important;" in modified_html
    assert "background-position: center !important;" in modified_html
    assert "background-repeat: no-repeat !important;" in modified_html
    assert '<style type="text/css" id="nepemcert-theme-styles">' in modified_html

def test_apply_theme_no_settings(theme_manager):
    """Testa aplicar um tema vazio (sem configurações de estilo)."""
    html_content = "<head></head><body>Teste</body>"
    theme_settings = {} # Tema vazio
    modified_html = theme_manager.apply_theme_to_template(html_content, theme_settings)
    assert modified_html == html_content # HTML não deve mudar se não há regras a aplicar

def test_apply_theme_no_head_tag(theme_manager):
    """Testa a injeção do estilo se não houver tag </head>, mas houver <body>."""
    html_content = "<html><body>Conteúdo</body></html>"
    theme_settings = {"text_color": "#123456"}
    modified_html = theme_manager.apply_theme_to_template(html_content, theme_settings)
    # Corrigir a assertion para a lógica real do ThemeManager
    assert '<style type="text/css" id="nepemcert-theme-styles">' in modified_html
    assert "color: #123456 !important;" in modified_html

def test_apply_theme_no_head_no_body_tag(theme_manager):
    """Testa a injeção do estilo se não houver </head> nem <body> (fragmento HTML)."""
    html_content = "<div>Conteúdo</div>"
    theme_settings = {"text_color": "#ABCDEF"}
    modified_html = theme_manager.apply_theme_to_template(html_content, theme_settings)
    # Corrigir a assertion para verificar se o estilo foi aplicado
    assert '<style type="text/css" id="nepemcert-theme-styles">' in modified_html
    assert "color: #ABCDEF !important;" in modified_html

def test_image_to_base64(theme_manager):
    """Testa a conversão de imagem para base64."""
    mock_file = mock_open(read_data=b"test_image_data")
    mock_file_obj = mock_file.return_value
    mock_file_obj.getvalue = lambda: b"test_image_data" # Simular getvalue

    with patch('builtins.open', mock_file): # Não é necessário aqui, pois image_to_base64 recebe o objeto
        base64_str = theme_manager.image_to_base64(mock_file_obj)
        assert base64_str == base64.b64encode(b"test_image_data").decode('utf-8')
    
    assert theme_manager.image_to_base64(None) is None

def test_create_custom_theme(theme_manager, sample_theme_settings):
    """Testa a criação de um tema personalizado."""
    # Com tema base
    theme_manager.save_theme("BaseTema", {"base_prop": "base_val", "override_prop": "base_override"})
    new_theme_path = theme_manager.create_custom_theme(
        "CustomComBase", 
        base_theme="BaseTema", 
        custom_prop="custom_val",
        override_prop="custom_override"
    )
    assert os.path.exists(new_theme_path)
    loaded_custom = theme_manager.load_theme("CustomComBase")
    assert loaded_custom["base_prop"] == "base_val"
    assert loaded_custom["custom_prop"] == "custom_val"
    assert loaded_custom["override_prop"] == "custom_override"

    # Sem tema base (do zero)
    new_theme_path_zero = theme_manager.create_custom_theme("CustomDoZero", custom_prop_zero="zero_val")
    assert os.path.exists(new_theme_path_zero)
    loaded_zero = theme_manager.load_theme("CustomDoZero")
    assert loaded_zero["custom_prop_zero"] == "zero_val"
    assert "font_family" in loaded_zero # Deve ter defaults

def test_set_theme_background_image(theme_manager, temp_themes_dir, sample_theme_settings):
    """Testa definir uma imagem de fundo para um tema."""
    theme_name = "TemaComFundo"
    theme_manager.save_theme(theme_name, sample_theme_settings)
    
    # Criar um arquivo de imagem falso
    fake_image_path = Path(temp_themes_dir) / "fake_image.png"
    with open(fake_image_path, "wb") as f:
        f.write(b"fake_image_content")
        
    success = theme_manager.set_theme_background_image(theme_name, str(fake_image_path))
    assert success
    
    loaded_theme = theme_manager.load_theme(theme_name)
    assert loaded_theme["background_image"] == base64.b64encode(b"fake_image_content").decode('utf-8')

    assert not theme_manager.set_theme_background_image("TemaInexistente", str(fake_image_path))
