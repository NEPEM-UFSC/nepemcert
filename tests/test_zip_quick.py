# -*- coding: utf-8 -*-
"""
Teste rápido do ZipExporter para verificar se o método create_zip funciona.
"""

import os
import sys
import tempfile

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.zip_exporter import ZipExporter

def test_create_zip():
    """Testa o método create_zip do ZipExporter."""
    print("🧪 Testando ZipExporter.create_zip...")
    
    # Criar alguns arquivos temporários
    with tempfile.TemporaryDirectory() as temp_dir:
        # Criar arquivos de teste
        test_files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"teste_{i}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Conteúdo do arquivo {i}")
            test_files.append(file_path)
        
        # Testar ZipExporter
        zip_exporter = ZipExporter()
        zip_path = os.path.join(temp_dir, "teste.zip")
        
        try:
            result = zip_exporter.create_zip(test_files, zip_path)
            
            if os.path.exists(zip_path):
                file_size = os.path.getsize(zip_path)
                print(f"✅ ZIP criado com sucesso: {result}")
                print(f"📁 Tamanho: {file_size} bytes")
                return True
            else:
                print("❌ Arquivo ZIP não foi criado")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao criar ZIP: {e}")
            return False

if __name__ == "__main__":
    success = test_create_zip()
    sys.exit(0 if success else 1)
