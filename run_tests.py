#!/usr/bin/env python
"""
Script para executar testes de unidade e integração com relatório de cobertura.
Uso: python run_tests.py [--unit|--integration|--all|--coverage]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def check_pytest_installed():
    """Verifica se o pytest está instalado."""
    try:
        import pytest
        return True
    except ImportError:
        print("❌ pytest não está instalado. Execute: pip install pytest pytest-cov")
        return False

def check_test_files():
    """Verifica se os arquivos de teste existem."""
    project_root = Path(__file__).parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print(f"❌ Diretório de testes não encontrado: {tests_dir}")
        return False
    
    unit_tests = list((tests_dir / "unit").glob("test_*.py"))
    integration_tests = list((tests_dir / "integration").glob("test_*.py"))
    
    print(f"📋 Encontrados {len(unit_tests)} testes de unidade")
    print(f"📋 Encontrados {len(integration_tests)} testes de integração")
    
    if len(unit_tests) == 0 and len(integration_tests) == 0:
        print("❌ Nenhum arquivo de teste encontrado")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Executa os testes de unidade e integração do NEPEMCERT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run_tests.py --all                          # Executa todos os testes
  python run_tests.py --unit                         # Apenas testes de unidade
  python run_tests.py --integration                  # Apenas testes de integração
  python run_tests.py --module csv_manager           # Testa módulo específico
  python run_tests.py --coverage                     # Com relatório de cobertura
  python run_tests.py --cli                          # Apenas testes CLI
  python run_tests.py --unit --coverage              # Unidade com cobertura
        """
    )
    
    parser.add_argument('--unit', action='store_true', 
                       help='Executa apenas os testes de unidade')
    parser.add_argument('--integration', action='store_true', 
                       help='Executa apenas os testes de integração')
    parser.add_argument('--all', action='store_true', 
                       help='Executa todos os testes (padrão se nenhuma opção for especificada)')
    parser.add_argument('--coverage', action='store_true', 
                       help='Gera relatório de cobertura')
    parser.add_argument('--cli', action='store_true', 
                       help='Executa apenas os testes relacionados ao CLI')
    parser.add_argument('--core', action='store_true', 
                       help='Executa apenas os testes dos módulos principais')
    parser.add_argument('--module', type=str, 
                       help='Executa testes de um módulo específico (ex: csv_manager)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Saída detalhada')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Saída mínima')
    parser.add_argument('--failfast', '-x', action='store_true',
                       help='Para na primeira falha')
    
    args = parser.parse_args()
    
    # Verificações iniciais
    if not check_pytest_installed():
        return 1
    
    if not check_test_files():
        return 1
    
    # Se nenhuma opção for especificada, executa todos os testes
    if not (args.unit or args.integration or args.all or args.cli or args.core or args.module):
        args.all = True
    
    # Configurar o diretório de trabalho
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Base do comando pytest
    cmd = ["python", "-m", "pytest"]
    
    # Opções de verbosidade
    if args.verbose:
        cmd.append("-v")
    elif args.quiet:
        cmd.append("-q")
    else:
        cmd.append("-v")  # Padrão: verboso
    
    # Opção de parar na primeira falha
    if args.failfast:
        cmd.append("-x")
    
    # Adiciona opções de cobertura se solicitado
    if args.coverage:
        cmd.extend([
            "--cov=app", 
            "--cov-report=html", 
            "--cov-report=term-missing",
            "--cov-fail-under=70"  # Falha se cobertura < 70%
        ])
        print("📊 Relatório de cobertura será gerado...")
    
    # Filtragem dos testes
    if args.module:
        # Busca por testes do módulo específico em ambos os diretórios
        test_patterns = [
            f"tests/unit/test_{args.module}.py",
            f"tests/integration/test_{args.module}*.py"
        ]
        
        found_tests = []
        for pattern in test_patterns:
            pattern_path = project_root / pattern.replace('*', '')
            if '*' in pattern:
                # Para padrões com wildcard, usar glob
                parent_dir = pattern_path.parent
                if parent_dir.exists():
                    found_tests.extend(list(parent_dir.glob(f"test_{args.module}*.py")))
            else:
                if pattern_path.exists():
                    found_tests.append(pattern_path)
        
        if found_tests:
            cmd.extend([str(f) for f in found_tests])
            print(f"🎯 Executando testes do módulo '{args.module}'...")
        else:
            print(f"❌ Nenhum teste encontrado para o módulo '{args.module}'")
            return 1
            
    elif args.cli:
        cmd.extend(["-m", "cli"])
        print("🖥️  Executando testes relacionados ao CLI...")
        
    elif args.core:
        cmd.extend(["-m", "core"])
        print("⚙️  Executando testes dos módulos principais...")
        
    elif args.unit and not args.integration and not args.all:
        cmd.extend(["-m", "unit"])
        print("🧪 Executando testes de unidade...")
        
    elif args.integration and not args.unit and not args.all:
        cmd.extend(["-m", "integration"])
        print("🔗 Executando testes de integração...")
        
    else:
        # Executa todos os testes
        cmd.append("tests/")
        print("🚀 Executando todos os testes...")
    
    # Adiciona configurações adicionais
    cmd.extend([
        "--tb=short",  # Traceback mais limpo
        "--strict-markers",  # Falha se marcadores não definidos
        "--disable-warnings"  # Desabilita warnings para saída mais limpa
    ])
    
    print(f"📋 Comando a ser executado: {' '.join(cmd)}")
    print("=" * 60)
    
    # Executa o pytest
    try:
        result = subprocess.run(cmd, check=False)
        
        print("=" * 60)
        if result.returncode == 0:
            print("✅ Todos os testes passaram!")
            if args.coverage:
                print("📊 Relatório de cobertura salvo em htmlcov/index.html")
        else:
            print("❌ Alguns testes falharam.")
            
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⏹️  Execução interrompida pelo usuário")
        return 130
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
