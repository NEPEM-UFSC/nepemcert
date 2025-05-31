#!/usr/bin/env python
"""
NEPEMCERT - Conversor de Imagens de Fundo para Temas

Este script unifica as funcionalidades para:
1. Converter imagens para base64
2. Salvar as imagens em um arquivo JSON
3. Aplicar imagens de fundo aos temas

Uso:
    - Para converter imagens e criar JSON: 
        python conversor_imagens.py converter
    
    - Para adicionar imagem a um tema:
        python conversor_imagens.py aplicar
"""

import os
import json
import base64
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Constantes
VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
JSON_FILENAME = "background_images.json"

def image_to_base64(image_path: str) -> str:
    """Converte uma imagem para base64."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string
    except Exception as e:
        raise Exception(f"Erro ao converter {image_path}: {e}")

def convert_images(image_dir: str) -> Dict[str, str]:
    """
    Converte todas as imagens da pasta especificada para base64.
    
    Args:
        image_dir: Caminho para a pasta com as imagens
        
    Returns:
        Dicionário com os nomes dos arquivos e seus dados em base64
    """
    image_data = {}
    
    print(f"Buscando imagens na pasta: {image_dir}")
    
    # Percorrer todos os arquivos da pasta
    for file_name in os.listdir(image_dir):
        file_path = os.path.join(image_dir, file_name)
        
        # Verificar se é um arquivo e tem extensão suportada
        if os.path.isfile(file_path) and file_path.lower().endswith(VALID_EXTENSIONS):
            try:
                # Converter para base64
                base64_data = image_to_base64(file_path)
                
                # Armazenar no dicionário
                name = os.path.splitext(file_name)[0]
                image_data[name] = base64_data
                print(f"✓ Convertida: {file_name}")
            except Exception as e:
                print(f"✗ Erro: {e}")
    
    return image_data

def save_json(images: Dict[str, str], output_path: str) -> None:
    """Salva o dicionário de imagens como um arquivo JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(images, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Arquivo JSON salvo em: {output_path}")

def load_json(json_path: str) -> Dict[str, str]:
    """Carrega o arquivo JSON com as imagens."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"✗ Erro ao carregar o arquivo JSON: {e}")
        return {}

def list_themes(themes_dir: str) -> List[str]:
    """Lista todos os arquivos de tema disponíveis."""
    return [f for f in os.listdir(themes_dir) 
            if f.endswith('.json') and not f == JSON_FILENAME]

def convert_command(args) -> None:
    """Executa o comando de conversão de imagens."""
    # Pasta atual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Converter imagens
    images = convert_images(current_dir)
    
    if not images:
        print("❌ Nenhuma imagem encontrada para converter.")
        return
    
    # Definir caminho de saída
    output_path = os.path.join(current_dir, JSON_FILENAME)
    
    # Salvar JSON
    save_json(images, output_path)
    
    # Mostrar instruções
    print(f"\n✅ {len(images)} imagens convertidas com sucesso!")
    print("\nPara usar uma imagem em seu tema:")
    print(f"1. Execute: python {os.path.basename(__file__)} aplicar")
    print("2. Selecione o tema e a imagem desejada")

def apply_command(args) -> None:
    """
    Executes the command to apply a background image to a theme.
    This function allows the user to select a background image from a JSON file
    and apply it to a theme file. It provides a list of available images and themes,
    prompts the user to make selections, and updates the selected theme with the
    chosen image.
    Args:
        args: Command-line arguments passed to the function.
    Workflow:
        1. Determines the current directory and the themes directory.
        2. Checks for the existence of a JSON file containing image data.
        3. Loads the JSON file and lists available images.
        4. Lists available theme files in the themes directory.
        5. Prompts the user to select a theme and an image.
        6. Updates the selected theme with the chosen image.
        7. Saves the updated theme back to the file.
    User Interaction:
        - The user is prompted to select a theme and an image by entering their
          respective indices.
        - The user is asked to confirm the operation before the theme is updated.
    Error Handling:
        - Displays error messages if the JSON file or theme files are missing.
        - Handles invalid user input (e.g., out-of-range indices or non-numeric input).
        - Catches and displays unexpected exceptions.
    Notes:
        - The JSON file must contain image data in base64 format.
        - The theme files are expected to be JSON files located in the themes directory.
    """
    """Executa o comando de aplicação de imagem a um tema."""
    # Pasta atual e pasta de temas
    current_dir = os.path.dirname(os.path.abspath(__file__))
    themes_dir = os.path.dirname(current_dir)
    
    # Caminho para o arquivo JSON
    json_path = os.path.join(current_dir, JSON_FILENAME)
    
    # Verificar se o arquivo JSON existe
    if not os.path.exists(json_path):
        print(f"❌ Arquivo {JSON_FILENAME} não encontrado.")
        print(f"Execute primeiro: python {os.path.basename(__file__)} converter")
        return
    
    # Carregar imagens
    images = load_json(json_path)
    
    if not images:
        print("❌ Nenhuma imagem encontrada no arquivo JSON.")
        return
    
    # Listar imagens disponíveis
    print(f"🖼️ {len(images)} imagens disponíveis:")
    for i, name in enumerate(images.keys(), 1):
        print(f"  {i}. {name}")
    
    # Listar temas disponíveis
    theme_files = list_themes(themes_dir)
    
    if not theme_files:
        print("❌ Nenhum arquivo de tema encontrado.")
        return
    
    print(f"\n🎨 {len(theme_files)} temas disponíveis:")
    for i, theme_file in enumerate(theme_files, 1):
        theme_name = os.path.splitext(theme_file)[0].replace('_', ' ').title()
        print(f"  {i}. {theme_name} ({theme_file})")
    
    # Selecionar tema e imagem
    try:
        theme_index = int(input("\nSelecione o número do tema para adicionar imagem de fundo: ")) - 1
        if theme_index < 0 or theme_index >= len(theme_files):
            print("❌ Índice de tema inválido.")
            return
        
        theme_file = theme_files[theme_index]
        theme_path = os.path.join(themes_dir, theme_file)
        
        # Carregar tema
        with open(theme_path, "r", encoding="utf-8") as f:
            theme_data = json.load(f)
        
        # Selecionar imagem
        image_index = int(input("\nSelecione o número da imagem de fundo: ")) - 1
        if image_index < 0 or image_index >= len(images):
            print("❌ Índice de imagem inválido.")
            return
        
        image_name = list(images.keys())[image_index]
        image_base64 = images[image_name]
        
        # Adicionar imagem ao tema
        theme_data["background_image"] = image_base64
        
        # Confirmar a operação
        confirm = input(f"\nAdicionar a imagem '{image_name}' ao tema '{theme_file}'? (s/n): ")
        if confirm.lower() not in ['s', 'sim', 'y', 'yes']:
            print("❌ Operação cancelada pelo usuário.")
            return
        
        # Salvar tema atualizado
        with open(theme_path, "w", encoding="utf-8") as f:
            json.dump(theme_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Imagem '{image_name}' adicionada ao tema '{theme_file}'!")
        
    except ValueError:
        print("❌ Por favor, insira um número válido.")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='NEPEMCERT - Gerenciador de Imagens de Fundo para Temas',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando de conversão
    convert_parser = subparsers.add_parser('converter', help='Converte imagens para base64 e gera JSON')
    
    # Comando de aplicação
    apply_parser = subparsers.add_parser('aplicar', help='Aplica uma imagem de fundo a um tema')
    
    args = parser.parse_args()
    
    # Verificar qual comando foi solicitado
    if args.command == 'converter':
        convert_command(args)
    elif args.command == 'aplicar':
        apply_command(args)
    else:
        # Por padrão, mostrar ajuda
        print(f"""
NEPEMCERT - Gerenciador de Imagens de Fundo para Temas

Comandos disponíveis:
  converter    Converte imagens para base64 e gera um arquivo JSON
  aplicar      Aplica uma imagem de fundo a um tema

Exemplos de uso:
  python {os.path.basename(__file__)} converter    # Converte todas as imagens desta pasta
  python {os.path.basename(__file__)} aplicar      # Adiciona uma imagem a um tema
        """)
        parser.print_help()

if __name__ == "__main__":
    main()
