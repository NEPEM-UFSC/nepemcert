"""
Utilitários para interfaces do usuário do NEPEM Cert.
Funções auxiliares para exibição, estilos e interações.
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align
from pyfiglet import Figlet
import questionary
from contextlib import redirect_stderr
from io import StringIO

# Console Rich global
console = Console()

# Versão do aplicativo
APP_VERSION = "1.1.0"

class UIUtils:
    """Classe para utilitários de interface do usuário."""
    
    @staticmethod
    def get_menu_style():
        """Retorna o estilo padrão para menus do questionary."""
        from questionary import Style
        
        return Style([
            ('qmark', 'fg:#ff9d00 bold'),
            ('question', 'bold'),
            ('answer', 'fg:#ff9d00 bold'),
            ('pointer', 'fg:#ff9d00 bold'),
            ('highlighted', 'fg:#ff9d00 bold'),
            ('selected', 'fg:#cc5454'),
            ('separator', 'fg:#cc5454'),
            ('instruction', ''),
            ('text', ''),
            ('disabled', 'fg:#858585 italic')
        ])

    @staticmethod
    def quiet_select(message, choices, **kwargs):
        """Wrapper para questionary.select que suprime mensagens de erro."""
        try:
            if sys.platform.startswith('win'):
                with redirect_stderr(StringIO()):
                    return questionary.select(message, choices, **kwargs).ask()
            else:
                return questionary.select(message, choices, **kwargs).ask()
        except Exception as e:
            console.print(f"[red]Erro ao exibir seleção: {e}[/red]")
            return choices[0] if choices else None

    @staticmethod
    def quiet_text(message, **kwargs):
        """Wrapper para questionary.text que suprime mensagens de erro."""
        try:
            if sys.platform.startswith('win'):
                with redirect_stderr(StringIO()):
                    return questionary.text(message, **kwargs).ask()
            else:
                return questionary.text(message, **kwargs).ask()
        except Exception as e:
            console.print(f"[red]Erro ao solicitar texto: {e}[/red]")
            return kwargs.get('default', "")

    @staticmethod
    def quiet_confirm(message, **kwargs):
        """Wrapper para questionary.confirm que suprime mensagens de erro."""
        try:
            if sys.platform.startswith('win'):
                with redirect_stderr(StringIO()):
                    return questionary.confirm(message, **kwargs).ask()
            else:
                return questionary.confirm(message, **kwargs).ask()
        except Exception as e:
            console.print(f"[red]Erro ao solicitar confirmação: {e}[/red]")
            return kwargs.get('default', False)

    @staticmethod
    def quiet_checkbox(message, choices, **kwargs):
        """Wrapper para questionary.checkbox que suprime mensagens de erro."""
        try:
            if sys.platform.startswith('win'):
                with redirect_stderr(StringIO()):
                    return questionary.checkbox(message, choices, **kwargs).ask()
            else:
                return questionary.checkbox(message, choices, **kwargs).ask()
        except Exception as e:
            console.print(f"[red]Erro ao exibir checkbox: {e}[/red]")
            return []

    @staticmethod
    def quiet_path(message, **kwargs):
        """Wrapper para questionary.path que suprime mensagens de erro."""
        try:
            if sys.platform.startswith('win'):
                with redirect_stderr(StringIO()):
                    return questionary.path(message, **kwargs).ask()
            else:
                return questionary.path(message, **kwargs).ask()
        except Exception as e:
            console.print(f"[red]Erro ao solicitar caminho: {e}[/red]")
            return kwargs.get('default', "")    @staticmethod
    def open_file_cross_platform(file_path):
        """Abre um arquivo usando o programa padrão do sistema operacional."""
        import subprocess
        try:
            os.startfile(file_path)  # Windows
        except AttributeError:
            try:
                subprocess.call(["open", file_path])  # macOS
            except:
                try:
                    subprocess.call(["xdg-open", file_path])  # Linux
                except:
                    pass  # Silenciosamente ignora erros se todos os métodos falharem

    @staticmethod
    def create_summary_table(data_dict, title=None):
        """Cria uma tabela Rich para exibir dados de resumo."""
        table = Table(box=box.SIMPLE, title=title)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")
        
        for key, value in data_dict.items():
            table.add_row(key, str(value))
        
        return table

    @staticmethod
    def wait_for_enter(message="Pressione Enter para continuar..."):
        """Exibe uma mensagem e aguarda o usuário pressionar Enter."""
        console.print(f"\n[dim]{message}[/dim]")
        input()

    @staticmethod
    def print_header(connectivity_manager, parameter_manager):
        """Exibe o cabeçalho da aplicação com logo e informações de status."""
        console.clear()
        f = Figlet(font="slant")
        console.print(f.renderText("NEPEM Cert"), style="bold blue")
        
        # Painel de versão
        version_panel = Panel(
            f"[bold]Versão:[/bold] {APP_VERSION}",
            title="Informações do Sistema",
            border_style="green",
            height=3,
            padding=(0, 2)
        )
        
        # Status da conexão
        conn_info = connectivity_manager.get_connection_status()
        connection_status = conn_info["status"]
        status_color = {
            "Conectado": "green",
            "Desconectado": "red",
            "Aguardando": "yellow"
        }.get(connection_status, "yellow")
        
        connection_panel = Panel(
            f"[bold]Status:[/bold] [{status_color}]{connection_status}[/{status_color}]",
            title="Conexão com Servidor",
            border_style=status_color,
            height=3,
            padding=(0, 2)
        )
        
        # Exibe os painéis lado a lado
        console.print(Align.center(version_panel, vertical="top"), connection_panel)
        
        console.print("\n[bold cyan]Gerador de Certificados em Lote[/bold cyan]")
        console.print("[dim]Use os comandos abaixo para gerenciar seus certificados.[/dim]")
        
        # Exibir indicador de modo debug
        if parameter_manager.get_debug_mode():
            console.print("\n[bold red]🐛 [DEBUG MODE ATIVADO] 🐛[/bold red]")
