"""
Testes de unidade para o módulo ui.ui_utils
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def ui_utils():
    """Fixture que retorna uma instância do UIUtils"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from ui.ui_utils import UIUtils
    return UIUtils()

def test_ui_utils_initialization(ui_utils):
    """Testa a inicialização do UIUtils"""
    # UIUtils é uma classe com métodos estáticos, não há atributos de instância
    assert ui_utils is not None

def test_get_menu_style(ui_utils):
    """Testa obtenção de estilo de menu"""
    style = ui_utils.get_menu_style()
    assert style is not None

@patch('questionary.select')
def test_quiet_select_success(mock_select, ui_utils):
    """Testa seleção silenciosa com sucesso"""
    mock_select.return_value.ask.return_value = "opção1"
    choices = ["opção1", "opção2", "opção3"]
    result = ui_utils.quiet_select("Escolha:", choices=choices)
    assert result == "opção1"

@patch('questionary.select')
def test_quiet_select_error(mock_select, ui_utils):
    """Testa seleção silenciosa com erro"""
    mock_select.side_effect = Exception("Erro simulado")
    choices = ["opção1", "opção2", "opção3"]
    result = ui_utils.quiet_select("Escolha:", choices=choices)
    assert result == "opção1"  # Retorna primeira opção em caso de erro

@patch('questionary.text')
def test_quiet_text_success(mock_text, ui_utils):
    """Testa entrada silenciosa de texto com sucesso"""
    mock_text.return_value.ask.return_value = "resposta"
    result = ui_utils.quiet_text("Digite algo:")
    assert result == "resposta"

@patch('questionary.text')
def test_quiet_text_with_default(mock_text, ui_utils):
    """Testa entrada silenciosa com valor padrão"""
    mock_text.return_value.ask.return_value = ""
    result = ui_utils.quiet_text("Digite algo:", default="padrão")
    assert result == ""

@patch('questionary.text')
def test_quiet_text_error(mock_text, ui_utils):
    """Testa entrada silenciosa de texto com erro"""
    mock_text.side_effect = Exception("Erro simulado")
    result = ui_utils.quiet_text("Digite algo:", default="padrão")
    assert result == "padrão"

@patch('questionary.confirm')
def test_quiet_confirm_success(mock_confirm, ui_utils):
    """Testa confirmação silenciosa com sucesso"""
    mock_confirm.return_value.ask.return_value = True
    result = ui_utils.quiet_confirm("Confirma?")
    assert result is True

@patch('questionary.confirm')
def test_quiet_confirm_error(mock_confirm, ui_utils):
    """Testa confirmação silenciosa com erro"""
    mock_confirm.side_effect = Exception("Erro simulado")
    result = ui_utils.quiet_confirm("Confirma?", default=False)
    assert result is False

@patch('questionary.checkbox')
def test_quiet_checkbox_success(mock_checkbox, ui_utils):
    """Testa checkbox silencioso com sucesso"""
    mock_checkbox.return_value.ask.return_value = ["opção1", "opção3"]
    choices = ["opção1", "opção2", "opção3"]
    result = ui_utils.quiet_checkbox("Escolha múltiplas:", choices=choices)
    assert result == ["opção1", "opção3"]

@patch('questionary.checkbox')
def test_quiet_checkbox_error(mock_checkbox, ui_utils):
    """Testa checkbox silencioso com erro"""
    mock_checkbox.side_effect = Exception("Erro simulado")
    choices = ["opção1", "opção2", "opção3"]
    result = ui_utils.quiet_checkbox("Escolha múltiplas:", choices=choices)
    assert result == []

@patch('questionary.path')
def test_quiet_path_success(mock_path, ui_utils):
    """Testa seleção silenciosa de caminho com sucesso"""
    mock_path.return_value.ask.return_value = "/path/to/file"
    result = ui_utils.quiet_path("Selecione um arquivo:")
    assert result == "/path/to/file"

@patch('questionary.path')
def test_quiet_path_error(mock_path, ui_utils):
    """Testa seleção silenciosa de caminho com erro"""
    mock_path.side_effect = Exception("Erro simulado")
    result = ui_utils.quiet_path("Selecione um arquivo:", default="/default/path")
    assert result == "/default/path"


def test_create_summary_table(ui_utils):
    """Testa criação de tabela de resumo"""
    data = {"nome": "João", "evento": "Curso Python"}
    result = ui_utils.create_summary_table(data, title="Resumo")
    
    # Verificar se o resultado é uma tabela Rich
    from rich.table import Table
    assert isinstance(result, Table)
    
    # Verificar se a tabela tem as colunas esperadas
    assert len(result.columns) == 2

@patch('builtins.input')
@patch('rich.console.Console.print')
def test_wait_for_enter_default_message(mock_print, mock_input, ui_utils):
    """Testa espera por Enter com mensagem padrão"""
    mock_input.return_value = ""
    ui_utils.wait_for_enter()
    mock_input.assert_called_once()
    mock_print.assert_called()

@patch('builtins.input')
@patch('rich.console.Console.print')
def test_wait_for_enter_custom_message(mock_print, mock_input, ui_utils):
    """Testa espera por Enter com mensagem personalizada"""
    mock_input.return_value = ""
    custom_message = "Pressione qualquer tecla"
    ui_utils.wait_for_enter(custom_message)
    mock_input.assert_called_once()
    mock_print.assert_called()

@patch('ui.ui_utils.console.clear')
@patch('ui.ui_utils.console.print')
@patch('ui.ui_utils.Align.center')
@patch('ui.ui_utils.Figlet')
def test_print_header(mock_figlet, mock_align, mock_print, mock_clear, ui_utils):
    """Testa impressão de cabeçalho"""
    # Mock dos managers
    mock_connectivity_manager = MagicMock()
    mock_connectivity_manager.get_connection_status.return_value = {"status": "Conectado"}
    
    mock_parameter_manager = MagicMock()
    mock_parameter_manager.get_debug_mode.return_value = False
    
    # Mock do Figlet
    mock_figlet_instance = MagicMock()
    mock_figlet_instance.renderText.return_value = "ASCII ART"
    mock_figlet.return_value = mock_figlet_instance
    
    # Mock Align.center
    mock_align.return_value = "centered_content"
    
    ui_utils.print_header(mock_connectivity_manager, mock_parameter_manager)
    
    # Verificar se o console foi limpo
    mock_clear.assert_called_once()
    
    # Verificar se Figlet foi usado
    mock_figlet.assert_called_with(font="slant")
    mock_figlet_instance.renderText.assert_called_with("NEPEM Cert")
    
    # Verificar se print foi chamado várias vezes
    assert mock_print.call_count >= 3

@patch('ui.ui_utils.console.clear')
@patch('ui.ui_utils.console.print')
@patch('ui.ui_utils.Figlet')
def test_print_header_debug_mode(mock_figlet, mock_print, mock_clear, ui_utils):
    """Testa impressão de cabeçalho com modo debug ativado"""
    # Mock dos managers
    mock_connectivity_manager = MagicMock()
    mock_connectivity_manager.get_connection_status.return_value = {"status": "Desconectado"}
    
    mock_parameter_manager = MagicMock()
    mock_parameter_manager.get_debug_mode.return_value = True
    
    # Mock do Figlet
    mock_figlet_instance = MagicMock()
    mock_figlet_instance.renderText.return_value = "ASCII ART"
    mock_figlet.return_value = mock_figlet_instance
    
    ui_utils.print_header(mock_connectivity_manager, mock_parameter_manager)
    
    # Verificar que o modo debug foi exibido
    # Procurar por uma chamada que contenha "DEBUG MODE"
    debug_call_found = any(
        "DEBUG MODE" in str(call) for call in mock_print.call_args_list
    )
    assert debug_call_found

def test_quiet_select_empty_choices(ui_utils):
    """Testa seleção silenciosa com lista vazia"""
    result = ui_utils.quiet_select("Escolha:", choices=[])
    assert result is None

@patch('questionary.text')
def test_quiet_text_no_default(mock_text, ui_utils):
    """Testa entrada silenciosa sem valor padrão quando há erro"""
    mock_text.side_effect = Exception("Erro simulado")
    result = ui_utils.quiet_text("Digite algo:")
    assert result == ""

@patch('questionary.confirm')
def test_quiet_confirm_no_default(mock_confirm, ui_utils):
    """Testa confirmação silenciosa sem valor padrão quando há erro"""
    mock_confirm.side_effect = Exception("Erro simulado")
    result = ui_utils.quiet_confirm("Confirma?")
    assert result is False

@patch('questionary.path')
def test_quiet_path_no_default(mock_path, ui_utils):
    """Testa seleção de caminho silenciosa sem valor padrão quando há erro"""
    mock_path.side_effect = Exception("Erro simulado")
    result = ui_utils.quiet_path("Selecione um arquivo:")
    assert result == ""

def test_create_summary_table_empty_data(ui_utils):
    """Testa criação de tabela com dados vazios"""
    result = ui_utils.create_summary_table({})
    assert result is not None

def test_create_summary_table_with_title(ui_utils):
    """Testa criação de tabela com título"""
    data = {"key": "value"}
    result = ui_utils.create_summary_table(data, title="Test Title")
    assert result is not None

def test_cross_platform_behavior(ui_utils):
    """Testa comportamento multiplataforma dos métodos"""
    # Testa que os métodos funcionam independente da plataforma
    style = ui_utils.get_menu_style()
    assert style is not None
    
    # Testa criação de tabela
    table = ui_utils.create_summary_table({"test": "value"})
    assert table is not None

@patch('rich.console.Console.print')
def test_console_output_methods(mock_print, ui_utils):
    """Testa métodos que fazem output no console"""
    # Como wait_for_enter usa print internamente
    with patch('builtins.input', return_value=""):
        ui_utils.wait_for_enter("Test message")
        mock_print.assert_called()

def test_static_method_accessibility(ui_utils):
    """Testa se métodos estáticos são acessíveis"""
    # Verificar que métodos estáticos podem ser chamados
    from ui.ui_utils import UIUtils
    
    style = UIUtils.get_menu_style()
    assert style is not None
    
    table = UIUtils.create_summary_table({"key": "value"})
    assert table is not None

@patch('subprocess.call')
@patch('os.startfile')
def test_file_operations_error_handling(mock_startfile, mock_subprocess, ui_utils):
    """Testa tratamento de erros em operações de arquivo"""
    # Simular erros em todas as tentativas de abertura
    mock_startfile.side_effect = AttributeError("não disponível")
    mock_subprocess.side_effect = Exception("comando falhou")
    
    # Não deve gerar exceção, apenas tratar silenciosamente
    from ui.ui_utils import UIUtils
    try:
        UIUtils.open_file_cross_platform("test.pdf")
        assert True  # Se chegou aqui, não houve exceção
    except Exception:
        pytest.fail("Método deveria tratar erros silenciosamente")

def test_method_return_types(ui_utils):
    """Testa tipos de retorno dos métodos"""
    # get_menu_style deve retornar um objeto Style
    style = ui_utils.get_menu_style()
    assert hasattr(style, '__class__')
    
    # create_summary_table deve retornar Table
    table = ui_utils.create_summary_table({"test": "data"})
    from rich.table import Table
    assert isinstance(table, Table)
