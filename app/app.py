"""
Módulo principal da aplicação NEPEMCERT.
Coordena todas as funcionalidades do sistema.
"""

import os
import sys
from pathlib import Path

class NEPEMCERTApp:
    """Classe principal da aplicação NEPEMCERT."""
    
    def __init__(self):
        """Inicializa a aplicação."""
        self.name = "NEPEMCERT"
        self.version = "1.0.0"
        self.description = "Sistema de geração de certificados em lote"
    
    def initialize(self):
        """Inicializa todos os componentes da aplicação."""
        # Criar diretórios necessários
        required_dirs = ['templates', 'uploads', 'output', 'config']
        for dir_name in required_dirs:
            os.makedirs(dir_name, exist_ok=True)
        
        return True
    
    def get_info(self):
        """Retorna informações sobre a aplicação."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description
        }

def main():
    """Função principal da aplicação."""
    app = NEPEMCERTApp()
    app.initialize()
    print(f"Aplicação {app.name} v{app.version} inicializada com sucesso!")
    return app

if __name__ == "__main__":
    main()
