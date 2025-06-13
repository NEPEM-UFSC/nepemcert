"""
Módulo para gerenciamento de temas e estilos para certificados.

Este módulo contém a classe ThemeManager, responsável por carregar, salvar e aplicar
temas a certificados. Os temas são armazenados em arquivos JSON na pasta 'themes' e
também são definidos no módulo themes.py.
"""
import os
import json
import re # Still needed by other methods like slugify if it were here, or by users of the class
import base64
from slugify import slugify

# Importar temas pré-definidos do módulo themes.py
from app.themes import PREDEFINED_THEMES
from app.utils import load_json_with_comments

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
            "Minimalista Moderno": "minimalista_moderno.json",
            "Executivo Distincao": "executivo_distincao.json",
            "Linhaca Contemporaneo": "linhaca_contemporaneo.json",
            "Linhaca Contemporaneo Contribuição": "linhaca_contemporaneo_contribuição.json",
            "Minimalista Neutro": "minimalista_neutro.json",
            "Moderno Tecnológico": "moderno_tecnológico.json",
            "Tradicional Solene": "tradicional_solene.json"
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
                    except json.JSONDecodeError:
                        # Tentar novamente com a função que suporta comentários
                        try:
                            theme_path = os.path.join(self.themes_dir, filename)
                            theme_data = load_json_with_comments(theme_path)
                            
                            # Mapear nomes conhecidos para seus nomes oficiais
                            theme_name = os.path.splitext(filename)[0].replace('_', ' ').title()
                            for official_name, file_name in self.theme_files.items():
                                if file_name == filename:
                                    theme_name = official_name
                                    break
                                    
                            all_themes[theme_name] = theme_data
                        except Exception as e:
                            print(f"Erro ao carregar tema {filename}: {e}")
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
        """        # Determinar o nome do arquivo
        if name in self.theme_files:
            file_name = self.theme_files[name]
        else:
            file_name = f"{slugify(name)}.json"
            
        theme_path = os.path.join(self.themes_dir, file_name)
        
        # Carregar do arquivo
        if os.path.exists(theme_path):
            try:
                with open(theme_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Tentar novamente com a função que suporta comentários
                try:
                    return load_json_with_comments(theme_path)
                except Exception:
                    return None
                
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

    def _map_font_to_safe(self, font_family):
        """
        Mapeia famílias de fontes para versões web-safe compatíveis com PDF.
        
        Args:
            font_family (str): Família de fonte original
            
        Returns:
            str: Família de fonte mapeada para versão web-safe
        """
        # Dicionário de mapeamento de fontes para versões web-safe
        safe_fonts = {
            # Fontes serifadas
            'Times New Roman': 'Times, serif',
            'Times': 'Times, serif',
            'Georgia': 'Georgia, serif',
            'Garamond': 'Georgia, serif',
            'Book Antiqua': 'Georgia, serif',
            
            # Fontes sans-serif
            'Arial': 'Arial, sans-serif',
            'Helvetica': 'Helvetica, Arial, sans-serif',
            'Helvetica Neue': 'Helvetica, Arial, sans-serif',
            'Verdana': 'Verdana, sans-serif',
            'Tahoma': 'Verdana, sans-serif',
            'Trebuchet MS': 'Verdana, sans-serif',
            'Calibri': 'Arial, sans-serif',
            'Segoe UI': 'Arial, sans-serif',
            'Roboto': 'Arial, sans-serif',
            'Open Sans': 'Arial, sans-serif',
            'Lato': 'Arial, sans-serif',
            'Montserrat': 'Helvetica, Arial, sans-serif',
            'Source Sans Pro': 'Arial, sans-serif',
            'Ubuntu': 'Arial, sans-serif',
            'Nunito': 'Arial, sans-serif',
            'PT Sans': 'Arial, sans-serif',
            'Poppins': 'Arial, sans-serif',
            'Inter': 'Arial, sans-serif',
            
            # Fontes monoespaçadas
            'Courier New': 'Courier, monospace',
            'Courier': 'Courier, monospace',
            'Monaco': 'Courier, monospace',
            'Consolas': 'Courier, monospace',
            'Source Code Pro': 'Courier, monospace',
            
            # Fontes decorativas/especiais
            'Impact': 'Arial Black, sans-serif',
            'Arial Black': 'Arial Black, sans-serif',
            'Comic Sans MS': 'Arial, sans-serif',
            'Brush Script MT': 'cursive',
            'Lucida Handwriting': 'cursive'
        }
        
        # Limpar a string da fonte (remover espaços extras, etc.)
        font_family = font_family.strip()
        
        # Se já contém fallbacks (vírgulas), usar como está
        if ',' in font_family:
            return font_family
        
        # Procurar mapeamento direto
        if font_family in safe_fonts:
            return safe_fonts[font_family]
        
        # Procurar mapeamento parcial (case-insensitive)
        font_lower = font_family.lower()
        for font_key, font_value in safe_fonts.items():
            if font_key.lower() in font_lower or font_lower in font_key.lower():
                return font_value
        
        # Se não encontrar mapeamento, determinar categoria baseada em palavras-chave
        font_lower = font_family.lower()
        
        # Verificar se é serif
        serif_keywords = ['serif', 'times', 'roman', 'garamond', 'georgia', 'book']
        if any(keyword in font_lower for keyword in serif_keywords):
            return f"{font_family}, serif"
        
        # Verificar se é monospace
        mono_keywords = ['mono', 'courier', 'code', 'console', 'terminal']
        if any(keyword in font_lower for keyword in mono_keywords):
            return f"{font_family}, monospace"
        
        # Verificar se é cursive/script
        script_keywords = ['script', 'handwriting', 'cursive', 'brush']
        if any(keyword in font_lower for keyword in script_keywords):
            return f"{font_family}, cursive"
        
        # Padrão: sans-serif
        return f"{font_family}, sans-serif"

    def apply_theme_to_template(self, html_content, theme_settings):
        """
        Aplica configurações de tema ao template HTML injetando estilos CSS.
        
        Args:
            html_content (str): Conteúdo HTML do template
            theme_settings (dict): Configurações do tema
            
        Returns:
            str: HTML com tema aplicado
        """
        if not theme_settings:
            return html_content
        
        # Construir CSS rules baseado nas configurações do tema
        css_rules = []
        
        # Font family (mapear para fontes seguras)
        if 'font_family' in theme_settings:
            mapped_font = self._map_font_to_safe(theme_settings['font_family'])
            css_rules.append(f"body {{ font-family: {mapped_font} !important; }}")
        
        # Text color (aplicar a múltiplos seletores)
        if 'text_color' in theme_settings:
            color = theme_settings['text_color']
            css_rules.append(f"body, .content, .text, .verification, .footer, p, div {{ color: {color} !important; }}")
        
        # Background color (aplicar apenas se não houver background image)
        if 'background_color' in theme_settings and not theme_settings.get('background_image'):
            bg_color = theme_settings['background_color']
            css_rules.append(f"body, .certificate, .certificate-container {{ background-color: {bg_color} !important; }}")
        
        # Border (aplicar a múltiplos seletores)
        if all(key in theme_settings for key in ['border_width', 'border_style', 'border_color']):
            border = f"{theme_settings['border_width']} {theme_settings['border_style']} {theme_settings['border_color']}"
            css_rules.append(f"body, .certificate, .certificate-container {{ border: {border} !important; }}")
        
        # Title color
        if 'title_color' in theme_settings:
            css_rules.append(f".title, h1 {{ color: {theme_settings['title_color']} !important; }}")
        
        # Name color
        if 'name_color' in theme_settings:
            color = theme_settings['name_color']
            css_rules.append(f".name, .participant-name {{ color: {color} !important; border-bottom-color: {color} !important; }}")
        
        # Event name color
        if 'event_name_color' in theme_settings:
            css_rules.append(f".event-name, .evento {{ color: {theme_settings['event_name_color']} !important; }}")
        
        # Signature color
        if 'signature_color' in theme_settings:
            color = theme_settings['signature_color']
            css_rules.append(f".signature-line {{ border-top-color: {color} !important; }}")
            css_rules.append(f".signature-name, .assinatura p, .signature div {{ color: {color} !important; }}")
        
        # Link color
        if 'link_color' in theme_settings:
            css_rules.append(f"a, .nepemcert-link {{ color: {theme_settings['link_color']} !important; }}")
        
        # Background image - CORRIGIDO: aplicar com data URI completo
        if 'background_image' in theme_settings and theme_settings['background_image']:
            base64_img = theme_settings['background_image']
            
            # Verificar se já inclui o prefixo data URI
            if not base64_img.startswith('data:'):
                # Assumir PNG por padrão se não especificado
                image_data_uri = f"data:image/png;base64,{base64_img}"
            else:
                image_data_uri = base64_img
            
            # Aplicar background image ao body com configurações otimizadas para PDF
            css_rules.append(f"""
                body {{
                    background-image: url('{image_data_uri}') !important;
                    background-size: cover !important;
                    background-position: center center !important;
                    background-repeat: no-repeat !important;
                    background-attachment: fixed !important;
                }}
            """.strip())
            
            # Garantir que elementos filhos sejam transparentes para mostrar o background
            css_rules.append(f"""
                .certificate-container, .title, .content, .signature, .footer, #qr-code-placeholder {{
                    background: transparent !important;
                }}
            """.strip())
            
            # Ajustar text-shadow para melhor legibilidade sobre backgrounds
            css_rules.append(f"""
                .title, .content, .participant-name, .event-name, .signature, .footer {{
                    text-shadow: 1px 1px 3px rgba(255, 255, 255, 0.9), -1px -1px 3px rgba(255, 255, 255, 0.9) !important;
                }}
            """.strip())
        
        # Se não há regras CSS, retornar HTML original
        if not css_rules:
            return html_content
        
        # Criar o bloco de estilo CSS
        css_block = f'''<style type="text/css" id="nepemcert-theme-styles">
        /* Theme Styles Applied by NEPEMCERT */
        {chr(10).join(css_rules)}
</style>'''
        
        # Tentar inserir antes de </head>
        if '</head>' in html_content:
            return html_content.replace('</head>', f'{css_block}\n</head>')
        
        # Se não há </head>, tentar inserir após <body>
        elif '<body>' in html_content:
            return html_content.replace('<body>', f'<body>\n{css_block}')
        
        # Se não há nem </head> nem <body>, inserir no início
        else:
            return f'{css_block}\n{html_content}'
    
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
        else:            # Criar do zero com valores padrão (apenas cores e fontes)
            theme_settings = {
                "font_family": "Arial, sans-serif",
                "heading_color": "#1a5276", # Note: heading_color is not directly used in new apply_theme
                "text_color": "#333333",
                "background_color": "#ffffff",
                "border_color": "#dddddd",
                "border_width": "4px",
                "border_style": "solid",
                "name_color": "#1a4971",
                "title_color": "#1a5276",
                "event_name_color": "#1a5276",
                "link_color": "#1a5276",
                "title_text": "Certificado", # These text fields are not used by apply_theme_to_template CSS generation
                "intro_text": "Certifica-se que",
                "participation_text": "participou do evento",
                "footer_style": "classic", # Not used by apply_theme_to_template CSS generation
                "signature_color": "#333333",
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

