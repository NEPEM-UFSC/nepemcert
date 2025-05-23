"""
Módulo para exportação de múltiplos arquivos em um único ZIP.
"""
import os
import zipfile
from io import BytesIO

class ZipExporter:
    def __init__(self):
        pass
    
    def create_zip_from_files(self, file_paths, arcnames=None):
        """
        Cria um arquivo ZIP contendo os arquivos especificados.
        Retorna os bytes do arquivo ZIP.
        """
        if arcnames and len(arcnames) != len(file_paths):
            raise ValueError("O número de caminhos e nomes deve ser igual")
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, file_path in enumerate(file_paths):
                # Se arcnames for fornecido, use o nome correspondente
                arcname = arcnames[i] if arcnames else os.path.basename(file_path)
                zip_file.write(file_path, arcname=arcname)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def create_zip_from_bytes(self, file_contents, file_names):
        """
        Cria um arquivo ZIP contendo os conteúdos de bytes especificados.
        Útil quando os arquivos só existem em memória.
        """
        if len(file_contents) != len(file_names):
            raise ValueError("O número de conteúdos e nomes deve ser igual")
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, content in enumerate(file_contents):
                zip_file.writestr(file_names[i], content)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
