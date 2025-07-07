"""
Utilidades diversas para o sistema NEPEMCERT.

Este módulo contém funções úteis que são usadas em várias partes do sistema.
"""
import re
import json

def load_json_with_comments(file_path):
    """
    Carrega um arquivo JSON que pode conter comentários.
    Os comentários são removidos antes da análise JSON.
    
    Args:
        file_path (str): Caminho para o arquivo JSON
        
    Returns:
        dict: Dados JSON carregados
        
    Raises:
        json.JSONDecodeError: Se o JSON não puder ser decodificado
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remover comentários de linha única (// ...)
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    
    # Remover comentários de múltiplas linhas (/* ... */)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Analisar o JSON
    return json.loads(content)
