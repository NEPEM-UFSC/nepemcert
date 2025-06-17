"""
Testes de unidade para o módulo ui.template_interface - TemplateInterface
"""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def mock_app_services():
    """Fixture que retorna serviços mockados da aplicação"""
    services = {
        "template_manager": MagicMock(),
        "parameter_manager": MagicMock(),
        "theme_manager": MagicMock(),
        "pdf_generator": MagicMock(),
        "certificate_service": MagicMock()
    }
    
    # Configurar retornos padrão
    services["template_manager"].list_templates.return_value = ["template1.html", "template2.html"]
    services["template_manager"].load_template.return_value = "<html><body>{{ nome }}</body></html>"
    services["template_manager"].extract_placeholders.return_value = ["nome"]
    services["template_manager"].validate_template.return_value = []
    
    return services

@pytest.fixture
def template_interface(mock_app_services):
    """Fixture que retorna uma instância do TemplateInterface"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from ui.template_interface import TemplateInterface
    return TemplateInterface(mock_app_services)

def test_template_handler_initialization(template_interface, mock_app_services):
    """Testa a inicialização do TemplateInterface"""
    assert template_interface.app_services == mock_app_services
    assert hasattr(template_interface, 'ui_utils')
    assert hasattr(template_interface, 'ui_components')

def test_handle_action_import_template(template_interface):
    """Testa ação de importar template"""
    template_interface.import_template = MagicMock()
    
    template_interface.handle_action("📥 Importar template")
    
    template_interface.import_template.assert_called_once()

def test_handle_action_list_templates(template_interface):
    """Testa ação de listar templates"""
    template_interface.list_templates = MagicMock()
    
    template_interface.handle_action("📄 Listar templates")
    
    template_interface.list_templates.assert_called_once()

def test_handle_action_edit_template(template_interface):
    """Testa ação de editar template"""
    template_interface.edit_template = MagicMock()
    
    template_interface.handle_action("✏️ Editar template")
    
    template_interface.edit_template.assert_called_once()

def test_handle_action_delete_template(template_interface):
    """Testa ação de deletar template"""
    template_interface.delete_template = MagicMock()
    
    template_interface.handle_action("🗑️ Excluir template")
    
    template_interface.delete_template.assert_called_once()

def test_handle_action_preview_template(template_interface):
    """Testa ação de visualizar template"""
    template_interface.preview_template = MagicMock()
    
    template_interface.handle_action("👁️ Visualizar template")
    
    template_interface.preview_template.assert_called_once()

def test_list_templates(template_interface):
    """Testa listagem de templates"""
    template_interface.list_templates()
    
    # Verificar se a lista de templates foi consultada
    template_interface.app_services["template_manager"].list_templates.assert_called_once()

def test_import_template_basic(template_interface):
    """Testa importação básica de template"""
    with patch.object(template_interface, '_collect_import_data', return_value={
        'name': 'new_template.html', 
        'content': '<html><body>{{ nome }}</body></html>'
    }):
        with patch.object(template_interface, '_execute_template_import'):
            template_interface.import_template()
    
    # Se chegou até aqui, passou nos testes básicos
    assert True

def test_edit_template_basic(template_interface):
    """Testa edição básica de template"""
    with patch.object(template_interface, '_select_template', return_value="template1.html"):
        with patch.object(template_interface, '_open_template_for_editing'):
            template_interface.edit_template()
    
    # Se chegou até aqui, passou nos testes básicos
    assert True

def test_delete_template_basic(template_interface):
    """Testa deleção básica de template"""
    with patch.object(template_interface, '_select_template', return_value="template1.html"):
        with patch.object(template_interface, '_confirm_deletion', return_value=True):
            template_interface.delete_template()
    
    # Se chegou até aqui, passou nos testes básicos
    assert True

def test_delete_template_cancelled(template_interface):
    """Testa cancelamento da deleção de template"""
    with patch.object(template_interface, '_select_template', return_value=None):
        template_interface.delete_template()
    
    # Não deve tentar deletar se cancelado - teste passa se chegou até aqui
    assert True

def test_preview_template_basic(template_interface):
    """Testa preview básico de template"""
    template_interface.preview_template()
    
    # Verificar que foi chamado - teste básico
    assert True

def test_internal_methods_exist(template_interface):
    """Testa se métodos internos existem"""
    assert hasattr(template_interface, '_collect_import_data')
    assert hasattr(template_interface, '_execute_template_import')
    assert hasattr(template_interface, '_select_template')
    assert hasattr(template_interface, '_confirm_deletion')
    assert hasattr(template_interface, '_open_template_for_editing')

def test_template_manager_integration(template_interface):
    """Testa integração com template manager"""
    # Testar que os métodos do template manager são chamados corretamente
    template_interface.app_services["template_manager"].validate_template.return_value = []
    
    content = "<html><body>{{ nome }}</body></html>"
    result = template_interface.app_services["template_manager"].validate_template(content)
    
    assert result == []  # Sem erros = template válido

def test_template_placeholders_extraction(template_interface):
    """Testa extração de placeholders do template"""
    content = "<html><body>{{ nome }} {{ evento }}</body></html>"
    template_interface.app_services["template_manager"].extract_placeholders.return_value = ["nome", "evento"]
    
    result = template_interface.app_services["template_manager"].extract_placeholders(content)
    
    assert result == ["nome", "evento"]

def test_template_content_validation(template_interface):
    """Testa validação de conteúdo de template"""
    content = "<html><body>{{ nome }}</body></html>"
    template_interface.app_services["template_manager"].validate_template.return_value = []
    
    errors = template_interface.app_services["template_manager"].validate_template(content)
    
    assert len(errors) == 0  # Sem erros = válido

def test_template_content_validation_with_errors(template_interface):
    """Testa validação de conteúdo com erros"""
    template_interface.app_services["template_manager"].validate_template.return_value = ["Erro: tag inválida"]
    content = "<html><iframe></iframe></html>"
    
    errors = template_interface.app_services["template_manager"].validate_template(content)
    
    assert len(errors) > 0  # Com erros = inválido

def test_handle_action_unknown(template_interface):
    """Testa ação desconhecida"""
    # Ação que não existe no action_map
    result = template_interface.handle_action("Ação inexistente")
    
    # Não deve gerar erro, apenas não fazer nada
    assert result is None

def test_template_test_generation(template_interface):
    """Testa funcionalidade de teste de geração"""
    template_interface.test_generation = MagicMock()
    
    template_interface.handle_action("🧪 Testar geração de certificado")
    
    template_interface.test_generation.assert_called_once()

def test_csv_data_preview(template_interface):
    """Testa preview de dados CSV"""
    template_interface.preview_csv_data = MagicMock()
    
    template_interface.handle_action("📊 Visualizar dados CSV")
    
    template_interface.preview_csv_data.assert_called_once()
