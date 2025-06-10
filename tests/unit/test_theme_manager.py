"""
Testes de unidade para o módulo theme_manager.py
"""
import os
import sys
import json
import pytest
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

    # Os temas pré-definidos mockados devem estar na lista
    # mais os temas salvos (Tema A, Tema B)
    # e os temas mapeados em self.theme_files cujos arquivos foram criados por _ensure_theme_files_exist
    
    # Nomes de arquivos mapeados em ThemeManager
    mapped_theme_names = list(manager.theme_files.keys())
    
    expected_themes = sorted(list(set(mapped_theme_names + ["Tema A", "Tema B"])))
    
    # Filtrar temas da lista que realmente existem (ou foram criados/mockados)
    actual_themes_in_list = [t for t in themes if t in manager.all_themes or t in predefined_theme_names_from_files(manager)]
    
    # Compara os conjuntos para flexibilidade na ordem e para incluir apenas temas existentes
    assert set(actual_themes_in_list) == set(expected_themes)


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

def test_apply_theme_to_template(theme_manager, sample_theme_settings):
    """Testa a aplicação de um tema a um template HTML."""
    html_content = """
    <body style="font-family: Test; background-color: #000; border: 1px solid #111;">
        <div class="title" style="color: #222;"></div>
        <div class="content" style="color: #333;"></div>
        <div class="participant-name" style="color: #444; border-bottom: 1px solid #555;"></div>
        <div class="event-name" style="color: #666;"></div>
        <div class="signature-line" style="border-top: 1px solid #777;"></div>
        <div class="signature-name" style="color: #888;"></div>
        <a class="nepemcert-link" style="color: #999;"></a>
    </body>
    """
    # Usar cores e fontes diferentes no sample_theme_settings para ver a mudança
    theme_settings = {
        "font_family": "Arial, sans-serif", "text_color": "#CCC", "background_color": "#FFF",
        "border_color": "#AAA", "border_width": "2px", "border_style": "dashed",
        "name_color": "#BBB", "title_color": "#DDD", "signature_color": "#EEE",
        "event_name_color": "#123", "link_color": "#456", "background_image": None
    }
    
    modified_html = theme_manager.apply_theme_to_template(html_content, theme_settings)
    
    assert 'font-family: Arial, sans-serif;' in modified_html
    assert 'background-color: #FFF;' in modified_html
    assert 'border: 2px dashed #AAA;' in modified_html
    assert 'color: #DDD;' in modified_html # title
    assert 'color: #CCC;' in modified_html # content
    assert '.participant-name{[^}]*color: #BBB;[^}]*border-bottom: 2px solid #BBB;'.replace("{[", "{").replace("]}","}") in modified_html.replace("\n","").replace(" ","")
    assert 'color: #123;' in modified_html # event-name
    assert 'border-top: 1px solid #EEE;' in modified_html # signature-line
    assert '.signature-name{[^}]*color: #EEE;'.replace("{[", "{").replace("]}","}") in modified_html.replace("\n","").replace(" ","") # signature-name
    assert 'color: #456;' in modified_html # link

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
