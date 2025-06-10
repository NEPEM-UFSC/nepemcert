"""
Testes de unidade para o módulo field_mapper.py
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def field_mapper():
    """Fixture que retorna uma instância do FieldMapper"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.field_mapper import FieldMapper
    return FieldMapper()

@pytest.fixture
def sample_data_row():
    """Fixture que retorna uma linha de dados de exemplo"""
    return {
        "nome": "João Silva",
        "email": "joao@exemplo.com",
        "curso": "Python Básico",
        "data": "01/01/2025",
        "carga_horaria": "40h",
        "instrutor": "Maria Oliveira"
    }

@pytest.fixture
def sample_df():
    """Fixture que retorna um DataFrame de exemplo"""
    data = {
        "nome": ["João Silva", "Maria Oliveira", "Carlos Santos", None],
        "email": ["joao@exemplo.com", "maria@exemplo.com", "carlos@exemplo.com", "ana@exemplo.com"],
        "curso": ["Python Básico", "Python Avançado", "Ciência de Dados", "Machine Learning"],
        "data": ["01/01/2025", "02/01/2025", "03/01/2025", "04/01/2025"],
        "carga_horaria": ["40h", "60h", "80h", "40h"],
        "concluido": [True, True, False, True]
    }
    return pd.DataFrame(data)

def test_map_data_to_template(field_mapper, sample_data_row):
    """Testa o método map_data_to_template"""
    # Caso com todos os placeholders presentes nos dados
    placeholders = ["nome", "curso", "data"]
    result = field_mapper.map_data_to_template(sample_data_row, placeholders)
    
    assert len(result) == 3
    assert result["nome"] == "João Silva"
    assert result["curso"] == "Python Básico"
    assert result["data"] == "01/01/2025"
    
    # Caso com alguns placeholders que não existem nos dados
    placeholders = ["nome", "curso", "campo_inexistente"]
    result = field_mapper.map_data_to_template(sample_data_row, placeholders)
    
    assert len(result) == 2
    assert "campo_inexistente" not in result
    
    # Caso com placeholders que não existem nos dados
    placeholders = ["campo1", "campo2"]
    result = field_mapper.map_data_to_template(sample_data_row, placeholders)
    
    assert len(result) == 0

def test_validate_mapping(field_mapper):
    """Testa o método validate_mapping"""
    csv_columns = ["nome", "email", "curso", "data"]
    
    # Caso onde todos os placeholders existem no CSV
    template_placeholders = ["nome", "curso"]
    missing = field_mapper.validate_mapping(csv_columns, template_placeholders)
    assert len(missing) == 0
    
    # Caso onde alguns placeholders não existem no CSV
    template_placeholders = ["nome", "instituicao", "curso"]
    missing = field_mapper.validate_mapping(csv_columns, template_placeholders)
    assert len(missing) == 1
    assert "instituicao" in missing
    
    # Caso onde nenhum placeholder existe no CSV
    template_placeholders = ["instituicao", "cidade"]
    missing = field_mapper.validate_mapping(csv_columns, template_placeholders)
    assert len(missing) == 2
    assert "instituicao" in missing
    assert "cidade" in missing
    
    # Caso com listas vazias
    assert len(field_mapper.validate_mapping([], [])) == 0
    assert len(field_mapper.validate_mapping(csv_columns, [])) == 0
    assert len(field_mapper.validate_mapping([], template_placeholders)) == len(template_placeholders)

def test_create_sample_data(field_mapper):
    """Testa o método create_sample_data"""
    # Lista de placeholders
    placeholders = ["nome", "curso", "data"]
    sample_data = field_mapper.create_sample_data(placeholders)
    
    assert len(sample_data) == 3
    assert sample_data["nome"] == "Exemplo de nome"
    assert sample_data["curso"] == "Exemplo de curso"
    assert sample_data["data"] == "Exemplo de data"
    
    # Lista vazia
    assert len(field_mapper.create_sample_data([])) == 0

def test_get_field_info(field_mapper, sample_df):
    """Testa o método get_field_info"""
    field_info = field_mapper.get_field_info(sample_df, "nome")
    
    # Verificar se o dicionário retornado contém as chaves esperadas
    expected_keys = ["field_name", "data_type", "sample_values"]
    for key in expected_keys:
        assert key in field_info
    
    # Verificar se há pelo menos 2 valores de amostra (conforme sample_df)
    assert len(field_info["sample_values"]) >= 2
    
    # Campo com valores únicos limitados
    info = field_mapper.get_field_info("curso", sample_df)
    assert len(info["sample_values"]) <= 5
    
    # Campo booleano
    info = field_mapper.get_field_info("concluido", sample_df)
    assert info["type"] == "bool"
    assert info["unique_values"] == 2
    
    # Campo inexistente
    info = field_mapper.get_field_info("campo_inexistente", sample_df)
    assert info is None
