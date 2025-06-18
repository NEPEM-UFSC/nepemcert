#!/usr/bin/env python3
"""
Teste rápido para verificar se o CSVManager.load_data está funcionando corretamente.
"""
import tempfile
import os
from app.csv_manager import CSVManager

def test_csv_manager_load_data():
    """Testa se o CSVManager.load_data funciona com o parâmetro has_header."""
    
    csv_manager = CSVManager()
    
    print("=== Teste CSVManager.load_data ===")
    
    # Teste 1: CSV sem cabeçalho
    print("\n1. Testando CSV SEM cabeçalho:")
    csv_content_no_header = """João Silva
Maria Santos
Pedro Oliveira"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        temp_file.write(csv_content_no_header)
        temp_file.flush()
        
        try:
            df = csv_manager.load_data(temp_file.name, has_header=False)
            print(f"  ✓ Carregou CSV sem cabeçalho: {len(df)} linhas")
            print(f"  Primeira linha: '{df.iloc[0, 0]}'")
            print(f"  Colunas: {list(df.columns)}")
        except Exception as e:
            print(f"  ✗ Erro: {e}")
        finally:
            os.unlink(temp_file.name)
    
    # Teste 2: CSV com cabeçalho
    print("\n2. Testando CSV COM cabeçalho:")
    csv_content_with_header = """Nome
João Silva
Maria Santos
Pedro Oliveira"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        temp_file.write(csv_content_with_header)
        temp_file.flush()
        
        try:
            df = csv_manager.load_data(temp_file.name, has_header=True)
            print(f"  ✓ Carregou CSV com cabeçalho: {len(df)} linhas")
            print(f"  Primeira linha: '{df.iloc[0, 0]}'")
            print(f"  Colunas: {list(df.columns)}")
        except Exception as e:
            print(f"  ✗ Erro: {e}")
        finally:
            os.unlink(temp_file.name)
    
    # Teste 3: Compatibilidade (sem parâmetro has_header)
    print("\n3. Testando compatibilidade (padrão):")
    csv_content_default = """Nome
Ana Silva
Carlos Santos"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        temp_file.write(csv_content_default)
        temp_file.flush()
        
        try:
            df = csv_manager.load_data(temp_file.name)  # Sem parâmetro has_header
            print(f"  ✓ Carregou CSV com comportamento padrão: {len(df)} linhas")
            print(f"  Primeira linha: '{df.iloc[0, 0]}'")
            print(f"  Colunas: {list(df.columns)}")
        except Exception as e:
            print(f"  ✗ Erro: {e}")
        finally:
            os.unlink(temp_file.name)
    
    print("\n=== Teste concluído ===")

if __name__ == "__main__":
    test_csv_manager_load_data()
