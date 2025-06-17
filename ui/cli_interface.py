"""
Interface CLI principal do NEPEM Cert.
Responsável apenas pela apresentação e comunicação com o usuário.
"""

from .ui_utils import console, UIUtils
from .ui_components import UIComponents
from .template_interface import TemplateInterface
from .generator_interface import GeneratorInterface

class CLIInterface:
    """Interface principal da aplicação CLI."""
    
    def __init__(self, app_services):
        """Inicializa a interface com os serviços da aplicação."""
        self.app_services = app_services
        self.ui_utils = UIUtils()
        self.ui_components = UIComponents()
        self.template_interface = TemplateInterface(app_services)
        self.generator_interface = GeneratorInterface(app_services)
    
    def show_main_menu(self):
        """Exibe o menu principal e retorna a opção selecionada."""
        # Exibir cabeçalho
        self.ui_utils.print_header(
            self.app_services["connectivity_manager"], 
            self.app_services["parameter_manager"]
        )
        
        # Obter opções do menu baseado no estado
        menu_options = self._get_main_menu_options()
        
        # Exibir menu e capturar seleção
        choice = self.ui_utils.quiet_select(
            "Selecione uma opção:",
            choices=menu_options,
            style=self.ui_utils.get_menu_style()
        )
        
        return choice
    
    def show_templates_menu(self):
        """Exibe o menu de templates."""
        console.clear()
        console.print("[bold blue]== Gerenciamento de Templates ==[/bold blue]\n")
        
        menu_options = self.ui_components.show_menu_options()["templates"]
        
        choice = self.ui_utils.quiet_select(
            "Selecione uma opção:",
            choices=menu_options,
            style=self.ui_utils.get_menu_style()
        )
        
        return choice
    
    def show_settings_menu(self):
        """Exibe o menu de configurações."""
        console.clear()
        console.print("[bold blue]== Configurações ==[/bold blue]\n")
        
        menu_options = self.ui_components.show_menu_options()["settings"]
        
        choice = self.ui_utils.quiet_select(
            "Selecione uma opção:",
            choices=menu_options,
            style=self.ui_utils.get_menu_style()
        )
        
        return choice
    
    def show_connectivity_menu(self):
        """Exibe o menu de conectividade."""
        console.clear()
        console.print("[bold blue]== Sincronização e Conectividade ==[/bold blue]\n")
        
        menu_options = self.ui_components.show_menu_options()["connectivity"]
        
        choice = self.ui_utils.quiet_select(
            "Selecione uma opção:",
            choices=menu_options,
            style=self.ui_utils.get_menu_style()
        )
        
        return choice
    
    def handle_template_action(self, action):
        """Delega ações de template para a interface específica."""
        return self.template_interface.handle_action(action)
    
    def handle_generator_action(self, action):
        """Delega ações de geração para a interface específica."""
        return self.generator_interface.handle_action(action)
    
    def show_exit_confirmation(self):
        """Exibe confirmação de saída."""
        return self.ui_utils.quiet_confirm("Deseja realmente sair do programa?")
    
    def show_help(self):
        """Exibe ajuda da aplicação."""
        console.clear()
        console.print("[bold blue]== Ajuda do NEPEM Cert ==[/bold blue]\n")
        
        help_text = """
[bold cyan]Sobre o NEPEM Cert[/bold cyan]
Sistema para geração automatizada de certificados em lote.

[bold yellow]Funcionalidades principais:[/bold yellow]
• Geração de certificados em PDF a partir de templates HTML
• Suporte a dados em CSV para geração em lote
• Sistema de temas personalizáveis
• Autenticação de certificados com QR codes
• Sincronização com servidor remoto

[bold yellow]Como usar:[/bold yellow]
1. Importe ou crie templates HTML
2. Prepare arquivo CSV com nomes dos participantes
3. Configure informações do evento
4. Gere os certificados em lote
5. Opcionalmente, empacote em ZIP

[bold yellow]Suporte:[/bold yellow]
Para mais informações, consulte a documentação ou entre em contato
com a equipe de desenvolvimento.
        """
        
        console.print(help_text)
        self.ui_utils.wait_for_enter()
    
    def _get_main_menu_options(self):
        """Obtém opções do menu principal baseado no estado da aplicação."""
        base_options = self.ui_components.show_menu_options()["main"]
        
        # Adicionar opções de debug se necessário
        debug_mode = self.app_services["parameter_manager"].get_debug_mode()
        if debug_mode:
            debug_options = [
                "🐛 DEBUG: Comparar temas",
                "🐛 DEBUG: Verificar sistema"
            ]
            # Inserir antes das opções finais (Ajuda e Sair)
            return base_options[:-2] + debug_options + base_options[-2:]
        
        return base_options
