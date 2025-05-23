"""
Módulo para gerenciamento de temas e estilos para certificados.
"""
import os
import json
import re
import base64
from slugify import slugify

class ThemeManager:
    def __init__(self, themes_dir="themes"):
        self.themes_dir = themes_dir
        os.makedirs(themes_dir, exist_ok=True)
        
        # Carregar temas pré-definidos
        self.predefined_themes = {
            "Clássico": {
                "font_family": "Times New Roman, serif",
                "heading_color": "#1a5276",
                "text_color": "#333333",
                "background_color": "#ffffff",
                "border_color": "#8c7853",
                "border_width": "2px",
                "margin": "40px",
                "heading_size": "36px",
                "text_size": "18px",
                "background_image": None
            },
            "Moderno": {
                "font_family": "Arial, sans-serif",
                "heading_color": "#2c3e50",
                "text_color": "#34495e",
                "background_color": "#ecf0f1",
                "border_color": "#bdc3c7",
                "border_width": "1px",
                "margin": "30px",
                "heading_size": "32px",
                "text_size": "16px",
                "background_image": None
            },
            "Minimalista": {
                "font_family": "Helvetica, Arial, sans-serif",
                "heading_color": "#000000",
                "text_color": "#333333",
                "background_color": "#ffffff",
                "border_color": "#dddddd",
                "border_width": "1px",
                "margin": "40px",
                "heading_size": "28px",
                "text_size": "16px",
                "background_image": None
            }
        }
    
    def save_theme(self, name, theme_settings):
        """Salva um tema com as configurações fornecidas"""
        theme_path = os.path.join(self.themes_dir, f"{slugify(name)}.json")
        with open(theme_path, "w", encoding="utf-8") as f:
            json.dump(theme_settings, f, ensure_ascii=False, indent=2)
        return theme_path
    
    def load_theme(self, name):
        """Carrega um tema pelo nome"""
        # Verificar primeiro nos temas pré-definidos
        if name in self.predefined_themes:
            return self.predefined_themes[name]
        
        # Caso contrário, carregar do arquivo
        theme_path = os.path.join(self.themes_dir, f"{slugify(name)}.json")
        if os.path.exists(theme_path):
            with open(theme_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        return None
    
    def list_themes(self):
        """Lista todos os temas disponíveis (pré-definidos e personalizados)"""
        custom_themes = []
        if os.path.exists(self.themes_dir):
            custom_themes = [os.path.splitext(f)[0] for f in os.listdir(self.themes_dir) if f.endswith('.json')]
        
        return list(self.predefined_themes.keys()) + custom_themes
    
    def delete_theme(self, name):
        """Exclui um tema personalizado"""
        # Não permite excluir temas pré-definidos
        if name in self.predefined_themes:
            return False
            
        theme_path = os.path.join(self.themes_dir, f"{slugify(name)}.json")
        if os.path.exists(theme_path):
            os.remove(theme_path)
            return True
        
        return False
    
    def apply_theme_to_template(self, html_content, theme_settings):
        """Aplica as configurações de tema ao HTML do template"""
        # Extrair as configurações do tema
        font_family = theme_settings.get("font_family", "Arial, sans-serif")
        heading_color = theme_settings.get("heading_color", "#1a5276")
        text_color = theme_settings.get("text_color", "#333333")
        background_color = theme_settings.get("background_color", "#ffffff")
        border_color = theme_settings.get("border_color", "#dddddd")
        border_width = theme_settings.get("border_width", "1px")
        bg_image_base64 = theme_settings.get("background_image")
        margin = theme_settings.get("margin", "40px")
        heading_size = theme_settings.get("heading_size", "32px")
        text_size = theme_settings.get("text_size", "16px")
        
        # Criar o CSS baseado nas configurações
        custom_css = f"""
        <style>
            body {{
                font-family: {font_family};
                color: {text_color};
                background-color: {background_color};
                margin: {margin};
                padding: {margin};
            }}
            .certificate {{
                padding: 20px;
                border: {border_width} solid {border_color};
                background-color: {background_color};
                {f"background-image: url('data:image/png;base64,{bg_image_base64}');" if bg_image_base64 else ""}
                {f"background-size: cover;" if bg_image_base64 else ""}
                {f"background-position: center;" if bg_image_base64 else ""}
                {f"background-repeat: no-repeat;" if bg_image_base64 else ""}
            }}
            h1, h2, h3, .title {{
                color: {heading_color};
                font-size: {heading_size};
            }}
            p, div {{
                font-size: {text_size};
            }}
        </style>
        """
        
        # Verificar se o template já tem uma tag <style>
        if "<style>" in html_content:
            # Substituir o estilo existente
            html_content = re.sub(r'<style>.*?</style>', custom_css, html_content, flags=re.DOTALL)
        else:
            # Adicionar o estilo após a tag <head>
            if "<head>" in html_content:
                html_content = html_content.replace("<head>", "<head>" + custom_css)
            else:
                # Se não houver tag <head>, adicionar no início
                html_content = custom_css + html_content
        
        return html_content
    
    def image_to_base64(self, image_file):
        """Converte uma imagem para base64"""
        if image_file is None:
            return None
        
        return base64.b64encode(image_file.getvalue()).decode("utf-8")
