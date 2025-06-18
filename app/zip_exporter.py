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
    
    def create_zip(self, file_paths, output_zip_path, arcnames=None):
        """
        Cria um arquivo ZIP no caminho especificado contendo os arquivos fornecidos.
        
        Args:
            file_paths (list): Lista de caminhos dos arquivos a serem incluídos
            output_zip_path (str): Caminho onde o arquivo ZIP será salvo
            arcnames (list, optional): Lista de nomes personalizados para os arquivos no ZIP
        
        Returns:
            str: Caminho do arquivo ZIP criado
        
        Raises:
            ValueError: Se o número de caminhos e nomes não coincidir
            FileNotFoundError: Se algum arquivo não for encontrado
        """
        if arcnames and len(arcnames) != len(file_paths):
            raise ValueError("O número de caminhos e nomes deve ser igual")
        
        # Verificar se todos os arquivos existem
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(output_zip_path), exist_ok=True)
        
        # Criar o arquivo ZIP
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, file_path in enumerate(file_paths):
                # Se arcnames for fornecido, use o nome correspondente
                arcname = arcnames[i] if arcnames else os.path.basename(file_path)
                zip_file.write(file_path, arcname=arcname)
        
        return output_zip_path
