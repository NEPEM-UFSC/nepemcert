"""
Módulo de diagnóstico para o sistema NEPEMCERT.
Fornece funcionalidades para verificar a integridade do sistema e diagnosticar problemas.
"""

import os
import sys
from pathlib import Path

def list_files(directory):
    """Lista todos os arquivos em um diretório."""
    try:
        return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except FileNotFoundError:
        return []

def check_system_health():
    """Verifica a saúde geral do sistema."""
    issues = []
    
    # Verificar diretórios principais
    required_dirs = ['app', 'templates', 'uploads', 'output', 'config']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            issues.append(f"Diretório obrigatório não encontrado: {dir_name}")
    
    # Verificar arquivos principais
    required_files = ['nepemcert.py', 'cli.py']
    for file_name in required_files:
        if not os.path.exists(file_name):
            issues.append(f"Arquivo principal não encontrado: {file_name}")
    
    return issues

if __name__ == "__main__":
    print("Executando diagnóstico do sistema NEPEMCERT...")
    issues = check_system_health()
    
    if not issues:
        print("✅ Sistema está funcionando corretamente.")
    else:
        print("❌ Problemas encontrados:")
        for issue in issues:
            print(f"  - {issue}")
