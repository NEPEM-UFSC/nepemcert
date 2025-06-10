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

def test_extract_placeholders(template_manager):
    """Testa o método extract_placeholders"""
    content = "Olá {{nome}}, bem-vindo ao {{evento}}! Data: {{data}}."
    placeholders = template_manager.extract_placeholders(content)
    assert sorted(placeholders) == sorted(["nome", "evento", "data"])

    content_sem_placeholders = "Olá mundo."
    placeholders = template_manager.extract_placeholders(content_sem_placeholders)
    assert len(placeholders) == 0

def test_validate_template(template_manager):
    """Testa o método validate_template"""
    valid_content = "<p>{{nome}}</p>"
    warnings = template_manager.validate_template(valid_content)
    assert len(warnings) == 0

    problematic_content = "<iframe src='test'></iframe> <p>{{nome}}</p> <style>display:flex;</style>"
    warnings = template_manager.validate_template(problematic_content)
    assert len(warnings) == 2
    assert "Tags <iframe> não são suportadas" in warnings
    assert "display:flex pode não funcionar como esperado" in warnings

def test_render_template(template_manager, sample_template, tmp_path):
    """Testa o método render_template"""
    template_name = "render_test.html"
    template_manager.templates_dir = str(tmp_path) # Usar tmp_path para este teste
    os.makedirs(os.path.join(str(tmp_path), "docs"), exist_ok=True) # Criar subdir docs
    template_manager.save_template(template_name, sample_template)
    
    data = {"nome": "Convidado", "curso": "Teste de Renderização", "data": "Hoje"}
    rendered_html = template_manager.render_template(template_name, data)
    
    assert "Convidado" in rendered_html
    assert "Teste de Renderização" in rendered_html
    assert "Hoje" in rendered_html

    with pytest.raises(FileNotFoundError):
        template_manager.render_template("inexistente.html", data)

def test_template_documentation(template_manager, tmp_path):
    """Testa salvar e carregar documentação do template"""
    template_name = "doc_test.html"
    # Configurar o template_manager para usar tmp_path para este teste específico
    original_templates_dir = template_manager.templates_dir
    original_docs_dir = template_manager.docs_dir
    template_manager.templates_dir = str(tmp_path)
    template_manager.docs_dir = os.path.join(str(tmp_path), "docs")
    os.makedirs(template_manager.docs_dir, exist_ok=True)

    template_manager.save_template(template_name, "{{placeholder1}} {{placeholder2}}")
    
    docs_data = {"placeholder1": "Descrição 1", "placeholder2": "Descrição 2"}
    doc_path = template_manager.save_template_documentation(template_name, docs_data)
    assert os.path.exists(doc_path)
    
    loaded_docs = template_manager.load_template_documentation(template_name)
    assert loaded_docs == docs_data

    # Restaurar dirs originais para não afetar outros testes
    template_manager.templates_dir = original_templates_dir
    template_manager.docs_dir = original_docs_dir


def test_validate_template_with_docs(template_manager):
    """Testa o método validate_template_with_docs"""
    content = "{{nome}} {{evento}}"
    docs = {"nome": "Nome do participante"}
    validation = template_manager.validate_template_with_docs(content, docs)
    assert not validation["valid"]
    assert "evento" in validation["missing_docs"]
    
    docs_completas = {"nome": "Nome", "evento": "Evento"}
    validation = template_manager.validate_template_with_docs(content, docs_completas)
    assert validation["valid"]
    assert len(validation["missing_docs"]) == 0

def test_validate_placeholders_against_csv(template_manager):
    """Testa o método validate_placeholders_against_csv"""
    placeholders = ["nome", "evento", "data_nao_existe"]
    csv_columns = ["nome", "evento", "local"]
    missing = template_manager.validate_placeholders_against_csv(placeholders, csv_columns)
    assert "data_nao_existe" in missing
    assert len(missing) == 1

    missing = template_manager.validate_placeholders_against_csv(placeholders, [])
    assert len(missing) == 3


@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_templates(request):
    """Limpa o diretório de templates temporário após a sessão de testes."""
    temp_dir_path = Path("tests/temp_templates")
    
    def finalizer():
        if temp_dir_path.exists():
            import shutil
            # Remover subdiretório docs primeiro se existir
            docs_subdir = temp_dir_path / "docs"
            if docs_subdir.exists() and docs_subdir.is_dir():
                shutil.rmtree(docs_subdir)

            # Remover arquivos .html no diretório principal
            for item in temp_dir_path.iterdir():
                if item.is_file() and item.suffix == '.html':
                    item.unlink()
            # Tentar remover o diretório principal se estiver vazio
            try:
                temp_dir_path.rmdir() 
            except OSError: # Pode não estar vazio se outros arquivos foram criados
                pass
                
    request.addfinalizer(finalizer)
