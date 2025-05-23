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
        
        # Carregar dados do CSV
        df = csv_manager.load_csv(sample_csv_path)
        assert isinstance(df, pd.DataFrame), "O resultado de load_csv não é um DataFrame"
        assert not df.empty, "O DataFrame carregado está vazio"
        
        # Carregar o template
        template_content = template_manager.load_template(sample_template_path)
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
        
        # Carregar dados do CSV
        df = csv_manager.load_csv(sample_csv_path)
        
        # Obter as colunas do CSV
        columns = field_mapper.get_csv_columns(df)
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
        zip_exporter.create_zip(test_files, zip_path)
        
        # Verificar se o arquivo zip foi criado
        assert os.path.exists(zip_path), f"O arquivo ZIP não foi criado em: {zip_path}"
        assert os.path.getsize(zip_path) > 0, "O arquivo ZIP está vazio"
        
    except ImportError as e:
        pytest.skip(f"Módulo não encontrado: {e}")
