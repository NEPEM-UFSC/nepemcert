"""
Testes de unidade para o módulo template_manager.py
Adaptado para uso com a interface CLI
"""

import os
import sys
import pytest
import re
from pathlib import Path

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = [pytest.mark.unit, pytest.mark.core]

@pytest.fixture
def template_manager():
    """Fixture que retorna uma instância do TemplateManager"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.template_manager import TemplateManager
    
    # Use um diretório temporário para testes
    temp_dir = "tests/temp_templates"
    os.makedirs(temp_dir, exist_ok=True)
    return TemplateManager(templates_dir=temp_dir)

@pytest.fixture
def sample_template():
    """Fixture que retorna um template HTML de exemplo"""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Certificado</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .certificado { border: 1px solid #000; padding: 20px; }
        .nome { font-size: 24px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="certificado">
        <h1>Certificado de Conclusão</h1>
        <p class="nome">{{nome}}</p>
        <p>Concluiu com sucesso o curso de <strong>{{curso}}</strong> em {{data}}.</p>
    </div>
</body>
</html>"""

def test_init(template_manager):
    """Testa a inicialização do TemplateManager"""
    assert template_manager.templates_dir == "tests/temp_templates"
    assert os.path.exists("tests/temp_templates")
    assert os.path.exists("tests/temp_templates/docs")

def test_save_template(template_manager, sample_template):
    """Testa o método save_template"""
    # Salvar com extensão .html
    file_path = template_manager.save_template("test_template.html", sample_template)
    assert os.path.exists(file_path)
    assert os.path.basename(file_path) == "test_template.html"
    
    # Salvar sem extensão .html
    file_path = template_manager.save_template("outro_template", sample_template)
    assert os.path.exists(file_path)
    assert os.path.basename(file_path) == "outro_template.html"

def test_load_template(template_manager, sample_template):
    """Testa o método load_template"""
    # Primeiro salva o template
    template_manager.save_template("test_load.html", sample_template)
    
    # Carrega o template com extensão .html
    loaded_template = template_manager.load_template("test_load.html")
    assert loaded_template == sample_template
    
    # Carrega o template sem extensão .html
    loaded_template = template_manager.load_template("test_load")
    assert loaded_template == sample_template
    
    # Tenta carregar um template que não existe
    loaded_template = template_manager.load_template("inexistente")
    assert loaded_template is None

def test_delete_template(template_manager, sample_template):
    """Testa o método delete_template"""
    # Primeiro salva o template
    template_manager.save_template("test_delete.html", sample_template)
    
    # Verifica se o template existe
    template_path = os.path.join(template_manager.templates_dir, "test_delete.html")
    assert os.path.exists(template_path)
    
    # Exclui o template com extensão .html
    result = template_manager.delete_template("test_delete.html")
    assert result is True
    assert not os.path.exists(template_path)
    
    # Tenta excluir um template já excluído
    result = template_manager.delete_template("test_delete")
    assert result is False
    
    # Salva novamente e exclui sem extensão .html
    template_manager.save_template("test_delete.html", sample_template)
    result = template_manager.delete_template("test_delete")
    assert result is True
    assert not os.path.exists(template_path)

def test_list_templates(template_manager, sample_template):
    """Testa o método list_templates"""
    # Garante que o diretório está vazio primeiro
    for item in os.listdir(template_manager.templates_dir):
        if item != "docs":  # Mantém o subdiretório docs
            path = os.path.join(template_manager.templates_dir, item)
            if os.path.isfile(path):
                os.remove(path)
    
    # Lista inicial deve estar vazia
    templates = template_manager.list_templates()
    assert len([t for t in templates if t.endswith('.html')]) == 0
    
    # Salva alguns templates
    template_manager.save_template("template1.html", sample_template)
    template_manager.save_template("template2.html", sample_template)
    template_manager.save_template("template3.html", sample_template)
    
    # Lista deve conter os templates salvos
    templates = template_manager.list_templates()
    html_templates = [t for t in templates if t.endswith('.html')]
    assert len(html_templates) == 3
    assert "template1.html" in html_templates
    assert "template2.html" in html_templates
    assert "template3.html" in html_templates

# Limpar o diretório de templates após todos os testes
@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_templates():
    yield
    import shutil
    if os.path.exists("tests/temp_templates"):
        shutil.rmtree("tests/temp_templates")
