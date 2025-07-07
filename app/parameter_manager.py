"""
Módulo para gerenciamento de parâmetros default para certificados.
"""
import os
import json

class ParameterManager:
    """
    Gerencia parâmetros e placeholders para geração de certificados.
    
    Responsável por gerenciar valores padrão, valores institucionais, e valores específicos de temas.
    Também gerencia configurações do sistema como modo de depuração.
    """
    
    def __init__(self, config_file="config/parameters.json"):
        """
        Inicializa o gerenciador de parâmetros.
        
        Args:
            config_file (str): Caminho para o arquivo de configuração
        """
        self.config_file = config_file
        self.parameters = self.load_parameters()
        
        # Garantir que as configurações do sistema existam
        if "system_settings" not in self.parameters:
            self.parameters["system_settings"] = {}
        
        # Garantir que debug_mode esteja definido com um valor padrão (False) se não existir
        if "debug_mode" not in self.parameters["system_settings"]:
            self.parameters["system_settings"]["debug_mode"] = False
            self.save_parameters()
    
    def load_parameters(self):
        """
        Carrega os parâmetros do arquivo de configuração.
        
        Returns:
            dict: Dicionário com os parâmetros carregados
        """
        # Criar diretório config se não existir
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Criar estrutura padrão de parâmetros
                default_params = {
                    "default_placeholders": {},
                    "theme_placeholders": {},
                    "institutional_placeholders": {},
                    "system_settings": {
                        "debug_mode": False
                    }
                }
                # Salvar estrutura padrão
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_params, f, indent=4, ensure_ascii=False)
                return default_params
        except Exception as e:
            print(f"Erro ao carregar parâmetros: {str(e)}")
            return {
                "default_placeholders": {},
                "theme_placeholders": {},
                "institutional_placeholders": {},
                "system_settings": {
                    "debug_mode": False
                }
            }
    
    def save_parameters(self):
        """
        Salva os parâmetros no arquivo de configuração.
        
        Returns:
            bool: True se salvo com sucesso, False caso contrário
        """
        try:
            # Criar diretório config se não existir
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.parameters, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar parâmetros: {str(e)}")
            return False
    
    def get_debug_mode(self):
        """
        Retorna o status atual do modo debug.
        
        Returns:
            bool: True se o modo debug estiver ativado, False caso contrário
        """
        return self.parameters.get("system_settings", {}).get("debug_mode", False)
    
    def set_debug_mode(self, enabled=False):
        """
        Define o status do modo debug e persiste a configuração.
        
        Args:
            enabled (bool): True para ativar o modo debug, False para desativar
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        if "system_settings" not in self.parameters:
            self.parameters["system_settings"] = {}
        
        self.parameters["system_settings"]["debug_mode"] = enabled
        return self.save_parameters()
    
    def get_default_placeholders(self):
        """
        Retorna os placeholders padrão.
        
        Returns:
            dict: Dicionário com os placeholders padrão
        """
        return self.parameters.get("default_placeholders", {})
    
    def get_theme_placeholders(self, theme_name):
        """
        Retorna os placeholders específicos de um tema.
        
        Args:
            theme_name (str): Nome do tema
            
        Returns:
            dict: Dicionário com os placeholders do tema
        """
        return self.parameters.get("theme_placeholders", {}).get(theme_name, {})
    
    def get_institutional_placeholders(self):
        """
        Retorna os placeholders institucionais.
        
        Returns:
            dict: Dicionário com os placeholders institucionais
        """
        return self.parameters.get("institutional_placeholders", {})
    
    def update_default_placeholders(self, new_values):
        """
        Atualiza os placeholders padrão.
        
        Args:
            new_values (dict): Novos valores para os placeholders
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        if "default_placeholders" not in self.parameters:
            self.parameters["default_placeholders"] = {}
        
        self.parameters["default_placeholders"].update(new_values)
        return self.save_parameters()
    
    def update_theme_placeholders(self, theme_name, new_values):
        """
        Atualiza os placeholders de um tema específico.
        
        Args:
            theme_name (str): Nome do tema
            new_values (dict): Novos valores para os placeholders
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        if "theme_placeholders" not in self.parameters:
            self.parameters["theme_placeholders"] = {}
        
        if theme_name not in self.parameters["theme_placeholders"]:
            self.parameters["theme_placeholders"][theme_name] = {}
        
        self.parameters["theme_placeholders"][theme_name].update(new_values)
        return self.save_parameters()
    
    def update_institutional_placeholders(self, new_values):
        """
        Atualiza os placeholders institucionais.
        
        Args:
            new_values (dict): Novos valores para os placeholders
            
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário
        """
        if "institutional_placeholders" not in self.parameters:
            self.parameters["institutional_placeholders"] = {}
        
        self.parameters["institutional_placeholders"].update(new_values)
        return self.save_parameters()
    
    def merge_placeholders(self, csv_data, theme_name=None):
        """
        Mescla placeholders de diferentes fontes de acordo com a prioridade.
        
        Prioridade:
        1. Dados do CSV (maior prioridade)
        2. Placeholders do tema
        3. Placeholders institucionais
        4. Placeholders padrão (menor prioridade)
        
        Args:
            csv_data (dict): Dados do CSV para um certificado específico
            theme_name (str, optional): Nome do tema a ser aplicado. Defaults to None.
            
        Returns:
            dict: Dicionário com todos os placeholders mesclados
        """
        result = {}
        
        # 1. Aplicar placeholders padrão (menor prioridade)
        result.update(self.get_default_placeholders())
        
        # 2. Sobrepor com placeholders institucionais
        result.update(self.get_institutional_placeholders())
        
        # 3. Sobrepor com placeholders do tema (se especificado)
        if theme_name:
            result.update(self.get_theme_placeholders(theme_name))
        
        # 4. Sobrepor com dados do CSV (maior prioridade)
        if csv_data:
            result.update(csv_data)
        
        return result
