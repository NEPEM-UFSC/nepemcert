"""
Módulo para gerenciamento e validação de dados CSV para certificados.
"""
import os
import pandas as pd
from io import StringIO, BytesIO

class CSVManager:
    def __init__(self, uploads_dir="uploads"):
        self.uploads_dir = uploads_dir
        os.makedirs(uploads_dir, exist_ok=True)
    
    def save_csv(self, uploaded_file):
        """Salva um arquivo CSV carregado"""
        file_path = os.path.join(self.uploads_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    
    def load_data(self, file_path):
        """Carrega dados de um arquivo CSV"""
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Erro ao ler o CSV: {str(e)}")
    
    def validate_data(self, df, required_columns=None):
        """Valida dados CSV para garantir que contém as colunas necessárias"""
        errors = []
        
        # Verificar se o DataFrame está vazio
        if df.empty:
            errors.append("O arquivo CSV está vazio")
            
        # Verificar colunas obrigatórias
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                errors.append(f"Colunas obrigatórias não encontradas: {', '.join(missing_columns)}")
        
        return errors
    
    def get_sample_data(self, df, row_index=0):
        """Obtém uma linha de amostra para preview"""
        if df.empty or row_index >= len(df):
            return {}
        
        return df.iloc[row_index].to_dict()
    
    def get_columns(self, df):
        """Retorna a lista de colunas do DataFrame"""
        return df.columns.tolist()
    
    def export_to_csv(self, df):
        """Exporta um DataFrame para CSV em memória"""
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        return buffer.getvalue()
    
    def save_uploaded_file(self, uploaded_file, dir_path):
        """Salva um arquivo carregado pelo usuário"""
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
