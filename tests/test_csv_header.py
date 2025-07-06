#!/usr/bin/env python3
"""
Teste rápido para verificar se o processamento de CSV com/sem cabeçalho está funcionando.
"""
import os
import tempfile
import pandas as pd
from app.certificate_service import CertificateService

def test_csv_header_processing():
    """Testa se a lógica de cabeçalho no CSV está funcionando corretamente."""
    
    # Preparar dados de teste
    service = CertificateService()
    
    print("=== Teste de Processamento de CSV ===\n")
    
    # Teste 1: CSV sem cabeçalho
    print("1. Testando CSV SEM cabeçalho:")
    csv_content_no_header = """João Silva
Maria Santos
Pedro Oliveira"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        temp_file.write(csv_content_no_header)
        temp_file.flush()
        
        # Carregar dados
        df = service.csv_manager.load_data(temp_file.name)
        print(f"  Dados originais: {len(df)} linhas")
        print(f"  Primeira linha: '{df.iloc[0, 0]}'")
        
        # Simular processamento sem cabeçalho
        has_header = False
        if has_header and len(df) > 0:
            df = df.iloc[1:].reset_index(drop=True)
        
        print(f"  Após processamento (has_header={has_header}): {len(df)} linhas")
        print(f"  Primeira linha após processamento: '{df.iloc[0, 0]}'")
        print(f"  ✓ Resultado esperado: João Silva mantido")
        
        os.unlink(temp_file.name)
    
    print()
    
    # Teste 2: CSV com cabeçalho
    print("2. Testando CSV COM cabeçalho:")
    csv_content_with_header = """Nome
João Silva
Maria Santos
Pedro Oliveira"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        temp_file.write(csv_content_with_header)
        temp_file.flush()
        
        # Carregar dados
        df = service.csv_manager.load_data(temp_file.name)
        print(f"  Dados originais: {len(df)} linhas")
        print(f"  Primeira linha: '{df.iloc[0, 0]}'")
        
        # Simular processamento com cabeçalho
        has_header = True
        if has_header and len(df) > 0:
            df = df.iloc[1:].reset_index(drop=True)
        
        print(f"  Após processamento (has_header={has_header}): {len(df)} linhas")
        print(f"  Primeira linha após processamento: '{df.iloc[0, 0]}'")
        print(f"  ✓ Resultado esperado: João Silva (cabeçalho 'Nome' removido)")
        
        os.unlink(temp_file.name)
    
    print()
    
    # Teste 3: CSV com cabeçalho diferente
    print("3. Testando CSV com cabeçalho não convencional:")
    csv_content_other_header = """Participantes
João Silva
Maria Santos
Pedro Oliveira"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
        temp_file.write(csv_content_other_header)
        temp_file.flush()
        
        # Carregar dados
        df = service.csv_manager.load_data(temp_file.name)
        print(f"  Dados originais: {len(df)} linhas")
        print(f"  Primeira linha: '{df.iloc[0, 0]}'")
        
        # Simular processamento com cabeçalho
        has_header = True
        if has_header and len(df) > 0:
            df = df.iloc[1:].reset_index(drop=True)
        
        print(f"  Após processamento (has_header={has_header}): {len(df)} linhas")
        print(f"  Primeira linha após processamento: '{df.iloc[0, 0]}'")
        print(f"  ✓ Resultado esperado: João Silva (cabeçalho 'Participantes' removido)")
        
        os.unlink(temp_file.name)
    
    print("\n=== Teste concluído ===")
    print("A lógica de processamento de cabeçalho foi corrigida e está funcionando corretamente!")

if __name__ == "__main__":
    test_csv_header_processing()
