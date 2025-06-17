"""
Testes de unidade para o módulo ui.cli_interface
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def mock_app_services():
    """Fixture que retorna serviços mockados da aplicação"""
    services = {
        "template_manager": MagicMock(),
        "theme_manager": MagicMock(),
        "parameter_manager": MagicMock(),
        "connectivity_manager": MagicMock(),
        "certificate_service": MagicMock(),
        "zip_exporter": MagicMock()
    }
    
    # Configurar retornos padrão
    services["template_manager"].list_templates.return_value = ["template1.html", "template2.html"]
    services["theme_manager"].list_themes.return_value = ["Clássico", "Moderno"]
    services["parameter_manager"].get_institutional_placeholders.return_value = {
        "coordenador": "Prof. João",
        "diretor": "Prof. Maria"
    }
    services["connectivity_manager"].check_connection.return_value = {
        "status": "success",
        "message": "Conectado"
    }
    
    return services

@pytest.fixture
def cli_interface(mock_app_services):
    """Fixture que retorna uma instância do CLIInterface"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from ui.cli_interface import CLIInterface
    return CLIInterface(mock_app_services)

def test_cli_interface_initialization(cli_interface, mock_app_services):
    """Testa a inicialização do CLIInterface"""
    # Corrigir para usar app_services em vez de services
    assert cli_interface.app_services == mock_app_services
    assert hasattr(cli_interface, 'ui_utils')
    assert hasattr(cli_interface, 'generator_interface')
    assert hasattr(cli_interface, 'template_interface')

@patch('questionary.select')
def test_show_main_menu_certificate_generation(mock_select, cli_interface):
    """Testa seleção de geração de certificados no menu principal"""
    mock_select.return_value.ask.return_value = "🔖 Gerar Certificados"
    cli_interface.generator_interface.handle_action = MagicMock()
    
    cli_interface.show_main_menu()
    
    cli_interface.generator_interface.handle_action.assert_called_once_with("🔖 Gerar Certificados")

@patch('questionary.select')
def test_show_main_menu_template_management(mock_select, cli_interface):
    """Testa seleção de gerenciamento de templates no menu principal"""
    mock_select.return_value.ask.return_value = "📋 Gerenciar Templates"
    cli_interface.template_interface.handle_action = MagicMock()
    
    cli_interface.show_main_menu()
    
    cli_interface.template_interface.handle_action.assert_called_once_with("📋 Gerenciar Templates")

@patch('questionary.select')
def test_show_main_menu_settings(mock_select, cli_interface):
    """Testa seleção de configurações no menu principal"""
    mock_select.return_value.ask.return_value = "⚙️ Configurações"
    cli_interface.show_settings_menu = MagicMock()
    
    cli_interface.show_main_menu()
    
    cli_interface.show_settings_menu.assert_called_once()

@patch('questionary.select')
def test_show_main_menu_exit(mock_select, cli_interface):
    """Testa seleção de sair no menu principal"""
    mock_select.return_value.ask.return_value = "🚪 Sair"
    
    result = cli_interface.show_main_menu()
    
    assert result == "exit"

@patch('questionary.select')
def test_show_main_menu_with_debug(mock_select, cli_interface, mock_app_services):
    """Testa menu principal com modo debug"""
    mock_select.return_value.ask.return_value = "🔧 Debug/Testes"
    cli_interface.show_debug_menu = MagicMock()
    
    # Simular modo debug
    cli_interface.debug_mode = True
    
    cli_interface.show_main_menu()
    
    cli_interface.show_debug_menu.assert_called_once()

@patch('questionary.select')
def test_show_settings_menu_parameters(mock_select, cli_interface):
    """Testa seleção de parâmetros no menu de configurações"""
    mock_select.return_value.ask.return_value = "📝 Gerenciar Parâmetros"
    cli_interface.show_parameters_menu = MagicMock()
    
    cli_interface.show_settings_menu()
    
    cli_interface.show_parameters_menu.assert_called_once()

@patch('questionary.select')
def test_show_settings_menu_themes(mock_select, cli_interface):
    """Testa seleção de temas no menu de configurações"""
    mock_select.return_value.ask.return_value = "🎨 Gerenciar Temas"
    cli_interface.show_themes_menu = MagicMock()
    
    cli_interface.show_settings_menu()
    
    cli_interface.show_themes_menu.assert_called_once()

@patch('questionary.select')
def test_show_settings_menu_connectivity(mock_select, cli_interface):
    """Testa seleção de conectividade no menu de configurações"""
    mock_select.return_value.ask.return_value = "🌐 Conectividade"
    cli_interface.show_connectivity_menu = MagicMock()
    
    cli_interface.show_settings_menu()
    
    cli_interface.show_connectivity_menu.assert_called_once()

@patch('questionary.select')
def test_show_debug_menu_test_generation(mock_select, cli_interface):
    """Testa seleção de teste de geração no menu debug"""
    mock_select.return_value.ask.return_value = "🧪 Teste de Geração"
    cli_interface.run_generation_test = MagicMock()
    
    cli_interface.show_debug_menu()
    
    cli_interface.run_generation_test.assert_called_once()

@patch('questionary.select')
def test_show_debug_menu_test_templates(mock_select, cli_interface):
    """Testa seleção de teste de templates no menu debug"""
    mock_select.return_value.ask.return_value = "📋 Teste de Templates"
    cli_interface.run_template_test = MagicMock()
    
    cli_interface.show_debug_menu()
    
    cli_interface.run_template_test.assert_called_once()

def test_run_generation_test(cli_interface):
    """Testa execução de teste de geração"""
    # Mock do serviço de certificados
    cli_interface.app_services["certificate_service"].generate_single_certificate = MagicMock(
        return_value={"success": True, "file_path": "test_cert.pdf"}
    )
    
    cli_interface.run_generation_test()
    
    # Verificar se o serviço foi chamado
    cli_interface.app_services["certificate_service"].generate_single_certificate.assert_called_once()

def test_run_template_test(cli_interface):
    """Testa execução de teste de templates"""
    # Mock do gerenciador de templates
    cli_interface.app_services["template_manager"].list_templates = MagicMock(
        return_value=["template1.html", "template2.html"]
    )
    
    cli_interface.run_template_test()
    
    # Verificar se o serviço foi chamado
    cli_interface.app_services["template_manager"].list_templates.assert_called_once()

@patch('questionary.select')
def test_show_parameters_menu_view(mock_select, cli_interface):
    """Testa visualização de parâmetros"""
    mock_select.return_value.ask.return_value = "👁️ Visualizar Parâmetros"
    cli_interface.view_parameters = MagicMock()
    
    cli_interface.show_parameters_menu()
    
    cli_interface.view_parameters.assert_called_once()

@patch('questionary.select')
def test_show_parameters_menu_edit_institutional(mock_select, cli_interface):
    """Testa edição de parâmetros institucionais"""
    mock_select.return_value.ask.return_value = "🏢 Editar Parâmetros Institucionais"
    cli_interface.edit_institutional_parameters = MagicMock()
    
    cli_interface.show_parameters_menu()
    
    cli_interface.edit_institutional_parameters.assert_called_once()

# @patch('questionary.select')
# def test_show_themes_menu_list(mock_select, cli_interface):
#     """Testa listagem de temas"""
#     mock_select.return_value.ask.return_value = "👁️ Listar Temas"
#     cli_interface.list_themes = MagicMock()
    
#     cli_interface.show_themes_menu()
    
#     cli_interface.list_themes.assert_called_once()

@patch('questionary.select')
def test_show_themes_menu_create(mock_select, cli_interface):
    """Testa criação de novo tema"""
    mock_select.return_value.ask.return_value = "➕ Criar Novo Tema"
    cli_interface.create_new_theme = MagicMock()
    
    cli_interface.show_themes_menu()
    
    cli_interface.create_new_theme.assert_called_once()

@patch('questionary.select')
def test_show_connectivity_menu_status(mock_select, cli_interface):
    """Testa verificação de status de conectividade"""
    mock_select.return_value.ask.return_value = "📊 Verificar Status"
    cli_interface.check_connectivity_status = MagicMock()
    
    cli_interface.show_connectivity_menu()
    
    cli_interface.check_connectivity_status.assert_called_once()

def test_check_connectivity_status(cli_interface):
    """Testa verificação de status de conectividade"""
    # Mock do resultado da verificação
    cli_interface.app_services["connectivity_manager"].check_connection.return_value = {
        "status": "success",
        "message": "Conectado com sucesso",
        "timestamp": "2025-01-20 10:00:00"
    }
    
    cli_interface.check_connectivity_status()
    
    # Verificar se o serviço foi chamado
    cli_interface.app_services["connectivity_manager"].check_connection.assert_called_once()

def test_view_parameters(cli_interface):
    """Testa visualização de parâmetros"""
    # Mock dos parâmetros
    cli_interface.app_services["parameter_manager"].get_all_parameters = MagicMock(
        return_value={
            "institutional": {"coordenador": "Prof. João"},
            "default": {"title_text": "Certificado"}
        }
    )
    
    cli_interface.view_parameters()
    
    # Verificar se o serviço foi chamado
    cli_interface.app_services["parameter_manager"].get_all_parameters.assert_called_once()

@patch('questionary.text')
def test_edit_institutional_parameters(mock_text, cli_interface):
    """Testa edição de parâmetros institucionais"""
    mock_text.return_value.ask.side_effect = ["Prof. Maria", "Dra. Ana"]
    
    # Mock dos parâmetros atuais
    cli_interface.app_services["parameter_manager"].get_institutional_placeholders.return_value = {
        "coordenador": "Prof. João",
        "diretor": "Prof. Carlos"
    }
    
    cli_interface.edit_institutional_parameters()
    
    # Verificar se os métodos foram chamados
    cli_interface.app_services["parameter_manager"].get_institutional_placeholders.assert_called_once()
    cli_interface.app_services["parameter_manager"].update_institutional_placeholders.assert_called_once()

def test_list_themes(cli_interface):
    """Testa listagem de temas"""
    # Mock da lista de temas
    cli_interface.app_services["theme_manager"].list_themes.return_value = ["Clássico", "Moderno", "Minimalista"]
    
    cli_interface.list_themes()
    
    # Verificar se o serviço foi chamado
    cli_interface.app_services["theme_manager"].list_themes.assert_called_once()

@patch('questionary.text')
@patch('questionary.select')
def test_create_new_theme(mock_select, mock_text, cli_interface):
    """Testa criação de novo tema"""
    mock_text.return_value.ask.side_effect = ["Meu Tema Personalizado"]
    mock_select.return_value.ask.side_effect = ["Arial", "#000000", "#FFFFFF"]
    
    cli_interface.create_new_theme()
    
    # Verificar se o método de salvamento foi chamado
    cli_interface.app_services["theme_manager"].save_theme.assert_called_once()

def test_start_interface(cli_interface):
    """Testa inicialização da interface"""
    cli_interface.show_main_menu = MagicMock(return_value="exit")
    
    result = cli_interface.start()
    
    # Verificar se o menu principal foi exibido
    cli_interface.show_main_menu.assert_called_once()
    assert result == "exit"

@patch('questionary.select')
def test_show_main_menu_cancel_exit(mock_select, cli_interface):
    """Testa cancelamento de saída no menu principal"""
    mock_select.return_value.ask.side_effect = ["🚪 Sair", "🔖 Gerar Certificados"]
    cli_interface.generator_interface.handle_action = MagicMock()
    
    # Mock para questionary.confirm para simular cancelamento
    with patch('questionary.confirm') as mock_confirm:
        mock_confirm.return_value.ask.return_value = False  # Usuário cancela a saída
        
        cli_interface.show_main_menu()
        
        # Como o usuário cancelou, o menu deve continuar e processar a próxima opção
        cli_interface.generator_interface.handle_action.assert_called_with("🔖 Gerar Certificados")

@patch('questionary.select')
def test_menu_navigation_back_option(mock_select, cli_interface):
    """Testa opção de voltar nos submenus"""
    mock_select.return_value.ask.return_value = "↩️ Voltar"
    
    # Teste no menu de configurações
    result = cli_interface.show_settings_menu()
    
    # A função deve retornar sem fazer nada quando escolher voltar
    assert result is None

def test_error_handling_in_services(cli_interface):
    """Testa tratamento de erros nos serviços"""
    # Mock para simular erro no serviço
    cli_interface.app_services["connectivity_manager"].check_connection.side_effect = Exception("Erro de conexão")
    
    # Verificar se a interface não trava com erro no serviço
    try:
        cli_interface.check_connectivity_status()
        # Se chegou aqui, não houve exceção não tratada
        assert True
    except Exception:
        pytest.fail("Interface não tratou erro do serviço adequadamente")
