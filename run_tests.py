#!/usr/bin/env python
"""
Script para executar testes de unidade e integração com relatório de cobertura.
Uso: python run_tests.py [--unit|--integration|--all]
"""

import os
import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Executa os testes de unidade e integração")
    parser.add_argument('--unit', action='store_true', help='Executa apenas os testes de unidade')
    parser.add_argument('--integration', action='store_true', help='Executa apenas os testes de integração')
    parser.add_argument('--all', action='store_true', help='Executa todos os testes')
    parser.add_argument('--coverage', action='store_true', help='Gera relatório de cobertura')
    parser.add_argument('--cli', action='store_true', help='Executa apenas os testes relacionados ao CLI')
    parser.add_argument('--core', action='store_true', help='Executa apenas os testes dos módulos principais')
    parser.add_argument('--module', type=str, help='Executa testes de um módulo específico (ex: connectivity_manager)')
    
    args = parser.parse_args()
    
    # Se nenhuma opção for especificada, executa todos os testes
    if not (args.unit or args.integration or args.all or args.cli or args.core or args.module):
        args.all = True
    
    # Base do comando pytest
    cmd = ["pytest", "-v"]
    
    # Adiciona opções de cobertura se solicitado
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    # Filtragem dos testes
    if args.module:
        cmd.append(f"tests/*/test_{args.module}.py")
        print(f"Executando testes do módulo {args.module}...")
    elif args.cli:
        cmd.append("-k")
        cmd.append("cli")
        print("Executando testes relacionados ao CLI...")
    elif args.core:
        cmd.append("-k")
        cmd.append("not cli")
        print("Executando testes dos módulos principais...")
    elif args.unit and not args.integration and not args.all:
        cmd.append("-m")
        cmd.append("unit")
        print("Executando testes de unidade...")
    elif args.integration and not args.unit and not args.all:
        cmd.append("-m")
        cmd.append("integration")
        print("Executando testes de integração...")
    else:
        print("Executando todos os testes...")
    
    # Executa o pytest com as opções configuradas
    result = subprocess.run(cmd)
    
    # Retorna o código de saída para uso em scripts
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
