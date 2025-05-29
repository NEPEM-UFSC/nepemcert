"""
Módulo para gerenciamento de temas e estilos para certificados.

Este módulo contém a classe ThemeManager, responsável por carregar, salvar e aplicar
temas a certificados. Os temas são armazenados em arquivos JSON na pasta 'themes' e
também são definidos no módulo themes.py.
"""
import os
import json
import re
import base64
from slugify import slugify

# Importar temas pré-definidos do módulo themes.py
from app.themes import PREDEFINED_THEMES

class ThemeManager:
    def __init__(self, themes_dir="themes"):
        """
        Inicializa o gerenciador de temas.
        
        Args:
            themes_dir (str): Diretório onde os temas personalizados são armazenados
        """
        self.themes_dir = themes_dir
        os.makedirs(themes_dir, exist_ok=True)
        
        # Carregar temas pré-definidos do módulo themes.py
        self.predefined_themes = PREDEFINED_THEMES
        
        # Mapeamento de nomes de tema para arquivos
        self.theme_files = {
            "Acadêmico Clássico": "academico_classico.json",
            "Executivo Premium": "executivo_premium.json", 
            "Contemporâneo Elegante": "contemporaneo_elegante.json",
            "Diplomático Oficial": "diplomatico_oficial.json",
            "Minimalista Moderno": "minimalista_moderno.json"
        }
        
        # Verificar se todos os temas pré-definidos têm arquivos correspondentes
        self._ensure_theme_files_exist()
        
        # Carregar todos os temas disponíveis (pré-definidos e personalizados)
        self.all_themes = self._load_all_themes()
    
    def _ensure_theme_files_exist(self):
        """
        Garante que todos os temas pré-definidos tenham arquivos JSON correspondentes.
        Se um arquivo não existir, ele é criado com base nas definições do PREDEFINED_THEMES.
        """
        for theme_name, file_name in self.theme_files.items():
            file_path = os.path.join(self.themes_dir, file_name)
            if not os.path.exists(file_path) and theme_name in self.predefined_themes:
                # Salvar as definições do tema em um arquivo JSON
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.predefined_themes[theme_name], f, ensure_ascii=False, indent=2)
    
    def _load_all_themes(self):
        """
        Carrega todos os temas disponíveis, tanto dos arquivos JSON quanto das definições padrão.
        Este método é executado durante a inicialização da classe.
        
        Returns:
            dict: Dicionário com todos os temas disponíveis {nome_tema: configuracoes}
        """
        all_themes = {}
        
        # Primeiro, carregar temas dos arquivos
        if os.path.exists(self.themes_dir):
            for filename in os.listdir(self.themes_dir):
                if filename.endswith('.json'):
                    theme_path = os.path.join(self.themes_dir, filename)
                    try:
                        with open(theme_path, 'r', encoding='utf-8') as f:
                            theme_data = json.load(f)
                            
                        # Transformar nome do arquivo em nome legível
                        theme_name = os.path.splitext(filename)[0].replace('_', ' ').title()
                        
                        # Mapear nomes conhecidos para seus nomes oficiais
                        # Ex: "academico_classico.json" para "Acadêmico Clássico"
                        for official_name, file_name in self.theme_files.items():
                            if file_name == filename:
                                theme_name = official_name
                                break
                                
                        all_themes[theme_name] = theme_data
                    except Exception as e:
                        print(f"Erro ao carregar tema {filename}: {e}")
        
        # Adicionar temas do módulo themes.py que não foram encontrados nos arquivos
        for theme_name, theme_data in self.predefined_themes.items():
            if theme_name not in all_themes:
                all_themes[theme_name] = theme_data
                
        return all_themes
    
    def save_theme(self, name, theme_settings):
        """
        Salva um tema com as configurações fornecidas.
        
        Args:
            name (str): Nome do tema
            theme_settings (dict): Configurações do tema
            
        Returns:
            str: Caminho para o arquivo de tema salvo
        """
        # Se for um tema pré-definido, usar o nome de arquivo mapeado
        if name in self.theme_files:
            file_name = self.theme_files[name]
        else:
            file_name = f"{slugify(name)}.json"
            
        theme_path = os.path.join(self.themes_dir, file_name)
        with open(theme_path, "w", encoding="utf-8") as f:
            json.dump(theme_settings, f, ensure_ascii=False, indent=2)
        return theme_path
    
    def load_theme(self, name):
        """
        Carrega um tema pelo nome.
        
        Args:
            name (str): Nome do tema a ser carregado
            
        Returns:
            dict: Configurações do tema ou None se o tema não existir
        """
        # Determinar o nome do arquivo
        if name in self.theme_files:
            file_name = self.theme_files[name]
        else:
            file_name = f"{slugify(name)}.json"
            
        theme_path = os.path.join(self.themes_dir, file_name)
        
        # Carregar do arquivo
        if os.path.exists(theme_path):
            with open(theme_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        # Se não encontrou um arquivo, verificar nos temas pré-definidos
        if name in self.predefined_themes:
            return self.predefined_themes[name]
        
        return None
    
    def list_themes(self):
        """
        Lista todos os temas disponíveis (pré-definidos e personalizados).
        
        Returns:
            list: Lista de nomes de temas disponíveis
        """
        # Listar todos os temas disponíveis em arquivos
        all_themes = set()
        
        # Adicionar temas do dicionário de mapeamento
        all_themes.update(self.theme_files.keys())
        
        # Adicionar outros temas personalizados da pasta
        if os.path.exists(self.themes_dir):
            for f in os.listdir(self.themes_dir):
                if f.endswith('.json'):
                    # Se não for um dos temas mapeados, adicionar à lista
                    theme_name = os.path.splitext(f)[0]
                    if not any(f == file_name for file_name in self.theme_files.values()):
                        # Transformar nome de arquivo slug para legível
                        readable_name = theme_name.replace('_', ' ').title()
                        all_themes.add(readable_name)
        
        return sorted(list(all_themes))
    
    def delete_theme(self, name):
        """
        Exclui um tema personalizado.
        
        Args:
            name (str): Nome do tema a ser excluído
            
        Returns:
            bool: True se o tema foi excluído, False caso contrário
        """
        # Não permite excluir temas pré-definidos
        if name in self.predefined_themes:
            return False
            
        # Determinar o nome do arquivo
        if name in self.theme_files:
            file_name = self.theme_files[name]
        else:
            file_name = f"{slugify(name)}.json"
            
        theme_path = os.path.join(self.themes_dir, file_name)
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
        border_style = theme_settings.get("border_style", "solid")
        bg_image_base64 = theme_settings.get("background_image")
        margin = theme_settings.get("margin", "40px")
        heading_size = theme_settings.get("heading_size", "32px")
        text_size = theme_settings.get("text_size", "16px")
        
        # Extrair propriedades adicionais específicas para certificados
        title_font_size = theme_settings.get("title_font_size", "48px")
        content_font_size = theme_settings.get("content_font_size", "24px")
        name_font_size = theme_settings.get("name_font_size", "36px")
        name_color = theme_settings.get("name_color", "#1a4971")
        title_color = theme_settings.get("title_color", heading_color)
        signature_color = theme_settings.get("signature_color", "#333333")
        signature_text_size = theme_settings.get("signature_text_size", "14px")
        footer_style = theme_settings.get("footer_style", "classic")
        
        # Garantir que apenas fontes seguras sejam usadas (evita importação de fontes da web)
        # xhtml2pdf tem limitações com fontes importadas via CSS
        safe_fonts = {
            "'Crimson Text', 'Garamond', 'Times New Roman', serif": "Times, Times New Roman, serif",
            "'Cormorant Garamond', 'Palatino Linotype', 'Book Antiqua', serif": "Palatino, Times New Roman, serif",
            "'Montserrat', 'Helvetica Neue', Arial, sans-serif": "Helvetica, Arial, sans-serif",
            "'Raleway', 'Roboto', 'Segoe UI', sans-serif": "Helvetica, Arial, sans-serif",
            "'Poppins', 'Open Sans', Helvetica, sans-serif": "Helvetica, Arial, sans-serif"
        }
        
        # Substituir pela fonte segura correspondente, ou manter a fonte padrão se não estiver mapeada
        font_family = safe_fonts.get(font_family, font_family)
        
        # Criar o CSS baseado nas configurações (sem importar fontes externas)
        custom_css = f"""
        <style>
            @page {{
                size: A4 landscape;
                margin: 0;
            }}
            
            body {{
                margin: 0;
                padding: 0;
                font-family: {font_family};
                color: {text_color};
                background-color: {background_color};
                width: 100%;
                height: 100%;
            }}
            
            .certificate {{
                width: 297mm;
                height: 210mm;
                background-color: {background_color};
                {f"background-image: url('data:image/png;base64,{bg_image_base64}');" if bg_image_base64 else ""}
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                padding: 20mm;
                box-sizing: border-box;
                position: relative;
                color: {text_color};
                text-align: center;
                border: {border_width} {border_style} {border_color};
                box-shadow: 0 0 15px rgba(0,0,0,0.1);
            }}
            
            .header {{
                margin-bottom: 15mm;
            }}
            
            .logo {{
                max-width: 150px;
                margin-bottom: 10mm;
            }}
            
            .title {{
                font-size: {title_font_size};
                font-weight: 700;
                color: {title_color};
                margin-bottom: 20mm;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .content {{
                font-size: {content_font_size};
                line-height: 1.6;
                margin-bottom: 25mm;
            }}
            
            .name {{
                font-size: {name_font_size};
                font-weight: bold;
                color: {name_color};
                margin: 10mm 0;
                border-bottom: 2px solid {name_color};
                display: inline-block;
                padding: 0 20mm 5mm;
                letter-spacing: 0.5px;
            }}
            
            .footer {{
                display: flex;
                justify-content: space-around;
                margin-top: 15mm;
            }}
            
            .signature {{
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            
            .signature-line {{
                width: 60mm;
                border-top: 1px solid {signature_color};
                margin-bottom: 5mm;
            }}
            
            .signature-name {{
                font-weight: bold;
                color: {signature_color};
                font-size: {signature_text_size};
            }}
            
            .date {{
                font-size: 18px;
                margin-top: 10mm;
                font-style: italic;
            }}
            
            .verification {{
                position: absolute;
                bottom: 10mm;
                left: 20mm;
                font-size: 12px;
                text-align: left;
                color: #666;
            }}
            
            .verification-code {{
                font-weight: bold;
                font-family: monospace;
                color: {signature_color};
                margin: 2mm 0;
            }}
            
            /* Estilos específicos para diferentes tipos de rodapé */
            .footer.classic .signature-line {{
                border-top-style: solid;
            }}
            
            .footer.modern .signature-line {{
                border-top-style: solid;
                width: 50mm;
            }}
            
            .footer.minimalist .signature-line {{
                border-top-style: solid;
                width: 40mm;
                border-top-width: 1px;
            }}
            
            .footer.formal .signature-line {{
                border-top-style: double;
                border-top-width: 3px;
                width: 65mm;
            }}
            
            .footer.clean .signature-line {{
                border-top-style: solid;
                border-top-width: 1px;
                width: 50mm;
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
    
    def create_custom_theme(self, name, base_theme=None, **customizations):
        """
        Cria um tema personalizado baseado em um tema existente ou do zero.
        
        Args:
            name (str): Nome do novo tema
            base_theme (str, optional): Nome do tema base a ser customizado
            **customizations: Configurações específicas para customizar
            
        Returns:
            str: Caminho para o arquivo de tema criado
        """
        if base_theme:
            # Carregar tema base
            base_settings = self.load_theme(base_theme)
            if not base_settings:
                raise ValueError(f"Tema base '{base_theme}' não encontrado")
                
            # Aplicar customizações
            theme_settings = base_settings.copy()
            theme_settings.update(customizations)
        else:
            # Criar do zero com valores padrão
            theme_settings = {
                "font_family": "Arial, sans-serif",
                "heading_color": "#1a5276",
                "text_color": "#333333",
                "background_color": "#ffffff",
                "border_color": "#dddddd",
                "border_width": "1px",
                "border_style": "solid",
                "margin": "40px",
                "heading_size": "32px",
                "title_font_size": "48px",
                "text_size": "16px",
                "content_font_size": "24px",
                "name_font_size": "36px",
                "name_color": "#1a4971",
                "title_color": "#1a5276",
                "title_text": "Certificado",
                "intro_text": "Certifica-se que",
                "participation_text": "participou do evento",
                "footer_style": "classic",
                "signature_color": "#333333",
                "signature_text_size": "14px",
                "background_image": None
            }
            # Aplicar customizações
            theme_settings.update(customizations)
            
        # Salvar o novo tema
        return self.save_theme(name, theme_settings)
        
    def set_theme_background_image(self, theme_name, image_path):
        """
        Define uma imagem de fundo para um tema existente.
        
        Args:
            theme_name (str): Nome do tema
            image_path (str): Caminho para o arquivo de imagem
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        # Carregar tema
        theme_settings = self.load_theme(theme_name)
        if not theme_settings:
            return False
            
        # Carregar imagem e converter para base64
        try:
            with open(image_path, "rb") as img_file:
                image_data = img_file.read()
                encoded_image = base64.b64encode(image_data).decode("utf-8")
                
                # Atualizar configurações do tema
                theme_settings["background_image"] = encoded_image
                
                # Salvar o tema atualizado
                self.save_theme(theme_name, theme_settings)
                return True
        except Exception as e:
            print(f"Erro ao carregar imagem de fundo: {e}")
            return False
