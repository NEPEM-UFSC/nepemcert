"""
Testes de unidade para o módulo csv_manager.py
"""

import os
import sys
import pytest
import pandas as pd
import io
from pathlib import Path

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def csv_manager():
    """Fixture que retorna uma instância do CSVManager"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.csv_manager import CSVManager
    
    # Use um diretório temporário para testes
    return CSVManager(uploads_dir="tests/temp_uploads")

@pytest.fixture
def sample_df():
    """Fixture que retorna um DataFrame de exemplo"""
    data = {
        "nome": ["João Silva", "Maria Oliveira", "Carlos Santos"],
        "email": ["joao@exemplo.com", "maria@exemplo.com", "carlos@exemplo.com"],
        "curso": ["Python Básico", "Python Avançado", "Ciência de Dados"],
        "data": ["01/01/2025", "02/01/2025", "03/01/2025"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_uploaded_file(sample_df, tmp_path):
    """Fixture que simula um arquivo carregado"""
    class MockUploadedFile:
        def __init__(self, name, content):
            self.name = name
            self._content = content
        
        def getbuffer(self):
            return self._content
    
    # Criar conteúdo do CSV
    csv_content = sample_df.to_csv(index=False).encode('utf-8')
    
    return MockUploadedFile("test_upload.csv", csv_content)

def test_init(csv_manager):
    """Testa a inicialização do CSVManager"""
    assert csv_manager.uploads_dir == "tests/temp_uploads"
    assert os.path.exists("tests/temp_uploads")

def test_save_csv(csv_manager, mock_uploaded_file):
    """Testa o método save_csv"""
    file_path = csv_manager.save_csv(mock_uploaded_file)
    
    assert os.path.exists(file_path)
    assert os.path.basename(file_path) == "test_upload.csv"
    
    # Limpar após o teste
    os.remove(file_path)

def test_load_data(csv_manager, sample_df, tmp_path):
    """Testa o método load_data"""
    # Criar um arquivo CSV temporário
    file_path = tmp_path / "test_data.csv"
    sample_df.to_csv(file_path, index=False)
    
    # Carregar os dados
    loaded_df = csv_manager.load_data(file_path)
    
    # Verificar se os dados foram carregados corretamente
    assert not loaded_df.empty
    assert list(loaded_df.columns) == list(sample_df.columns)
    assert len(loaded_df) == len(sample_df)

def test_load_data_invalid_file(csv_manager, tmp_path):
    """Testa o método load_data com um arquivo inválido"""
    # Criar um arquivo inválido
    file_path = tmp_path / "invalid.txt"
    with open(file_path, "w") as f:
        f.write("Este não é um CSV válido!")
    
    # Tentar carregar o arquivo inválido
    with pytest.raises(ValueError):
        csv_manager.load_data(file_path)

def test_validate_data(csv_manager, sample_df):
    """Testa o método validate_data"""
    # Validação sem colunas obrigatórias
    errors = csv_manager.validate_data(sample_df)
    assert len(errors) == 0
    
    # Validação com colunas obrigatórias válidas
    errors = csv_manager.validate_data(sample_df, required_columns=["nome", "email"])
    assert len(errors) == 0
    
    # Validação com colunas obrigatórias inválidas
    errors = csv_manager.validate_data(sample_df, required_columns=["nome", "telefone"])
    assert len(errors) > 0
    assert "telefone" in errors[0]
    
    # Validação com DataFrame vazio
    empty_df = pd.DataFrame()
    errors = csv_manager.validate_data(empty_df)
    assert len(errors) > 0
    assert "vazio" in errors[0]

def test_get_sample_data(csv_manager, sample_df):
    """Testa o método get_sample_data"""
    # Obter a primeira linha
    row_0 = csv_manager.get_sample_data(sample_df, row_index=0)
    assert row_0["nome"] == "João Silva"
    assert row_0["email"] == "joao@exemplo.com"
    
    # Obter a segunda linha
    row_1 = csv_manager.get_sample_data(sample_df, row_index=1)
    assert row_1["nome"] == "Maria Oliveira"
    assert row_1["email"] == "maria@exemplo.com"
    
    # Índice inválido
    invalid_row = csv_manager.get_sample_data(sample_df, row_index=999)
    assert invalid_row == {}
    
    # DataFrame vazio
    empty_df = pd.DataFrame()
    empty_row = csv_manager.get_sample_data(empty_df)
    assert empty_row == {}

def test_get_columns(csv_manager, sample_df):
    """Testa o método get_columns"""
    columns = csv_manager.get_columns(sample_df)
    assert columns == ["nome", "email", "curso", "data"]

def test_export_to_csv(csv_manager, sample_df):
    """Testa o método export_to_csv"""
    csv_str = csv_manager.export_to_csv(sample_df)
    
    # Verificar se a string CSV contém os dados corretos
    assert isinstance(csv_str, str)
    assert "nome,email,curso,data" in csv_str
    assert "João Silva,joao@exemplo.com" in csv_str

def test_save_uploaded_file(csv_manager, mock_uploaded_file, tmp_path):
    """Testa o método save_uploaded_file"""
    dir_path = tmp_path / "uploaded_files"
    
    file_path = csv_manager.save_uploaded_file(mock_uploaded_file, dir_path)
    
    assert os.path.exists(file_path)
    assert os.path.basename(file_path) == "test_upload.csv"

# Limpar o diretório de uploads após todos os testes
@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_uploads():
    yield
    import shutil
    if os.path.exists("tests/temp_uploads"):
        shutil.rmtree("tests/temp_uploads")
