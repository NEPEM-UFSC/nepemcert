"""
Módulo para gerenciamento de parâmetros default para certificados.
"""
import os
import json

class ParameterManager:
    def __init__(self, config_dir="config"):
        self.config_dir = config_dir
        self.parameters_file = os.path.join(config_dir, "parameters.json")
        self._parameters = None
        
    @property
    def parameters(self):
        """Carrega e retorna os parâmetros"""
        if self._parameters is None:
            self.load_parameters()
        return self._parameters
    
    def load_parameters(self):
        """Carrega os parâmetros do arquivo JSON"""
        if os.path.exists(self.parameters_file):
            with open(self.parameters_file, "r", encoding="utf-8") as f:
                self._parameters = json.load(f)
        else:
            # Cria um arquivo de parâmetros padrão se não existir
            self._parameters = {
                "default_placeholders": {},
                "theme_placeholders": {},
                "institutional_placeholders": {}
            }
            self.save_parameters()
        
        return self._parameters
    
    def save_parameters(self):
        """Salva os parâmetros no arquivo JSON"""
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.parameters_file, "w", encoding="utf-8") as f:
            json.dump(self._parameters, f, ensure_ascii=False, indent=4)
    
    def get_default_placeholders(self):
        """Retorna os placeholders padrão"""
        return self.parameters.get("default_placeholders", {})
        
    def get_theme_placeholders(self, theme_name):
        """Retorna os placeholders específicos para um tema"""
        theme_placeholders = self.parameters.get("theme_placeholders", {})
        theme_name = theme_name.lower()
        if theme_name in theme_placeholders:
            return theme_placeholders[theme_name]
        return {}
    
    def get_institutional_placeholders(self):
        """Retorna os placeholders institucionais"""
        return self.parameters.get("institutional_placeholders", {})
    
    def update_institutional_placeholders(self, new_values):
        """Atualiza os placeholders institucionais"""
        if "institutional_placeholders" not in self.parameters:
            self.parameters["institutional_placeholders"] = {}
        
        self.parameters["institutional_placeholders"].update(new_values)
        self.save_parameters()
    def merge_placeholders(self, csv_data=None, theme=None):
        """
        Combina diferentes fontes de placeholders na seguinte ordem de prioridade:
        1. Dados do CSV (maior prioridade)
        2. Placeholders do tema
        3. Placeholders institucionais
        4. Placeholders padrão (menor prioridade)
        """
        # Começar com os placeholders padrão (menor prioridade)
        merged = self.get_default_placeholders().copy()
        
        # Adicionar placeholders institucionais
        merged.update(self.get_institutional_placeholders())
        
        # Adicionar placeholders do tema, se especificado
        if theme:
            # Carregar placeholders específicos do tema
            theme_placeholders = self.get_theme_placeholders(theme)
            merged.update(theme_placeholders)
            
            # Verificar se precisamos carregar configurações adicionais do ThemeManager
            from app.theme_manager import ThemeManager
            theme_manager = ThemeManager()
            theme_settings = theme_manager.load_theme(theme)
            
            if theme_settings:
                # Extrair propriedades do tema que também são placeholders
                theme_placeholder_props = [
                    "title_text", "intro_text", "participation_text",
                    "location_text", "date_text", "workload_text",
                    "hours_text", "coordinator_title", "director_title",
                    "title_font_size", "title_color", "content_font_size",
                    "name_font_size", "name_color"
                ]
                
                # Atualizar merged com propriedades do tema que são placeholders
                for prop in theme_placeholder_props:
                    if prop in theme_settings and prop not in merged:
                        merged[prop] = theme_settings[prop]
        
        # Adicionar dados do CSV, se fornecidos (maior prioridade)
        if csv_data:
            merged.update(csv_data)
            
        return merged
