"""
Script principal para executar o NEPEMCERT.
Este arquivo fornece uma interface simplificada para iniciar a aplicação.
"""

import os
import sys

def custom_style():
    """Aplica estilo personalizado ao terminal."""
    # Configurações de estilo para o terminal
    if os.name == 'nt':  # Windows
        os.system('color 0A')  # Fundo preto, texto verde
    return "Estilo aplicado com sucesso"

def main():
    """Função principal para executar o NEPEMCERT."""
    print("🚀 Iniciando NEPEMCERT...")
    
    # Aplicar estilo personalizado
    style_result = custom_style()
    print(f"Estilo: {style_result}")
    
    # Importar e executar o CLI principal
    try:
        from nepemcert import cli
        cli()
    except ImportError as e:
        print("❌ Erro: Não foi possível importar o módulo principal.")
        print(f"Detalhes: {e}")
        print("Verifique se o arquivo 'nepemcert.py' existe e suas dependências estão instaladas.")
        sys.exit(1)

if __name__ == "__main__":
    main()
