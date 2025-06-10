"""
Testes de unidade para o módulo zip_exporter.py
"""

import os
import sys
import zipfile
import pytest
from io import BytesIO
from pathlib import Path

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def zip_exporter():
    """Fixture que retorna uma instância do ZipExporter"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.zip_exporter import ZipExporter
    return ZipExporter()

@pytest.fixture
def temp_files(tmp_path):
    """Fixture que cria arquivos temporários para teste"""
    files = []
    for i in range(3):
        file_path = tmp_path / f"file_{i}.txt"
        with open(file_path, 'w') as f:
            f.write(f"Conteúdo do arquivo {i}")
        files.append(file_path)
    return files

def test_create_zip_from_files(zip_exporter, temp_files):
    """Testa o método create_zip_from_files"""
    # Criar ZIP com nomes de arquivo padrão
    zip_bytes = zip_exporter.create_zip_from_files(temp_files)
    
    # Verificar se os bytes resultantes são um arquivo ZIP válido
    assert len(zip_bytes) > 0
    
    # Extrair o ZIP e verificar seu conteúdo
    with BytesIO(zip_bytes) as zip_buffer:
        with zipfile.ZipFile(zip_buffer) as zip_file:
            # Verificar se o ZIP contém os arquivos esperados
            file_list = zip_file.namelist()
            assert len(file_list) == 3
            
            # Verificar se os arquivos têm os nomes esperados (basename)
            for i, path in enumerate(temp_files):
                expected_name = os.path.basename(path)
                assert expected_name in file_list
                
                # Verificar o conteúdo - não decodificar como UTF-8 para evitar erros
                content = zip_file.read(expected_name)
                expected_content = f"Conteúdo do arquivo {i}".encode('utf-8')
                assert content == expected_content

def test_create_zip_from_files_with_arcnames(zip_exporter, temp_files):
    """Testa o método create_zip_from_files com nomes personalizados"""
    # Nomes personalizados para os arquivos no ZIP
    arcnames = ["doc1.txt", "doc2.txt", "doc3.txt"]
    
    # Criar ZIP com nomes personalizados
    zip_bytes = zip_exporter.create_zip_from_files(temp_files, arcnames=arcnames)
    
    # Verificar o ZIP e seus conteúdos
    with BytesIO(zip_bytes) as zip_buffer:
        with zipfile.ZipFile(zip_buffer) as zip_file:
            # Verificar se o ZIP contém os arquivos com os nomes personalizados
            file_list = zip_file.namelist()
            assert len(file_list) == 3
            
            # Verificar se os arquivos têm os nomes personalizados
            for i, name in enumerate(arcnames):
                assert name in file_list
                
                # Verificar o conteúdo - não decodificar como UTF-8
                content = zip_file.read(name)
                expected_content = f"Conteúdo do arquivo {i}".encode('utf-8')
                assert content == expected_content

def test_create_zip_from_files_error(zip_exporter, temp_files):
    """Testa o método create_zip_from_files com erro de tamanho"""
    # Número diferente de caminhos e nomes
    arcnames = ["doc1.txt", "doc2.txt"]  # Faltando um nome
    
    # Deve lançar ValueError
    with pytest.raises(ValueError):
        zip_exporter.create_zip_from_files(temp_files, arcnames=arcnames)

def test_create_zip_from_bytes(zip_exporter):
    """Testa o método create_zip_from_bytes"""
    # Dados em bytes
    file_contents = [
        b"Conteudo do arquivo 1",
        b"Conteudo do arquivo 2",
        b"Conteudo do arquivo 3"
    ]
    
    # Nomes dos arquivos
    file_names = [
        "arquivo1.txt",
        "arquivo2.txt",
        "arquivo3.txt"
    ]
    
    # Criar ZIP
    zip_bytes = zip_exporter.create_zip_from_bytes(file_contents, file_names)
    
    # Verificar o ZIP e seus conteúdos
    with BytesIO(zip_bytes) as zip_buffer:
        with zipfile.ZipFile(zip_buffer) as zip_file:
            # Verificar se o ZIP contém os arquivos esperados
            file_list = zip_file.namelist()
            assert len(file_list) == 3
            
            # Verificar se os arquivos têm os nomes esperados
            for i, name in enumerate(file_names):
                assert name in file_list
                
                # Verificar o conteúdo
                content = zip_file.read(name)
                assert content == file_contents[i]
