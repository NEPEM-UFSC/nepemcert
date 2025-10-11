"""
NEPEM Certificados - Interface de Linha de Comando
Ferramenta para geração de certificados em lote.
"""

import os
import sys
import random

from app import themes

# Suprimir avisos verbosos do GLib no Windows
os.environ['G_MESSAGES_DEBUG'] = ''
os.environ['GLIB_SILENCE_DEPRECATION'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'

# Redirecionar stderr temporariamente para suprimir avisos do GTK/GLib
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import click
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box
from rich.align import Align
from rich.layout import Layout
from rich.text import Text
from pathlib import Path
import questionary
from pyfiglet import Figlet
import pandas as pd
import time
import random
import string
from datetime import datetime

from app.cli.cli_debug import debug_system_check, debug_compare_themes
from app.cli.cli_certificates_menu import generate_certificates_menu, generate_certificate_single
from app.cli.cli_preview_data import preview_imported_data
from app.cli.cli_connectivity import connectivity_menu


# Configurar questionary para reduzir verbosidade no Windows
if sys.platform.startswith('win'):
    # Suprimir avisos do GLib/GTK no Windows
    from contextlib import redirect_stderr
    from io import StringIO

# Wrapper functions para questionary que suprimem stderr
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
        return kwargs.get('default', "")

# Importação dos módulos da aplicação
from app.csv_manager import CSVManager
from app.template_manager import TemplateManager
from app.pdf_generator import PDFGenerator
from app.zip_exporter import ZipExporter
from app.connectivity_manager import ConnectivityManager
from app.parameter_manager import ParameterManager
from app.theme_manager import ThemeManager
from app.cert_auth_manager import CertAuthenticationManager
from app.certificate_service import CertificateService # Added CertificateService import
from app.utils.app_parameters import APP_VERSION

# Configuração do console Rich
console = Console()


# Inicialização dos gerenciadores
csv_manager = CSVManager()
template_manager = TemplateManager()
pdf_generator = PDFGenerator()
zip_exporter = ZipExporter()
connectivity_manager = ConnectivityManager()
parameter_manager = ParameterManager()
theme_manager = ThemeManager()
auth_manager = CertAuthenticationManager()
certificate_service = CertificateService() # Instantiated CertificateService


def check_connection_status():
    """Verifica o status de conexão com servidor remoto."""
    # Usa o connectivity_manager para obter o status real
    conn_info = connectivity_manager.get_connection_status()
    return conn_info["status"]


def print_header():
    """Exibe o cabeçalho da aplicação com logo e informações de status."""
    console.clear()
    f = Figlet(font="slant")
    console.print(f.renderText("NEPEM Cert"), style="bold blue")
    
    # Divisão para as caixas de informação lado a lado (lado a lado sem layout aninhado)
    version_panel = Panel(
        f"[bold]Versão:[/bold] {APP_VERSION}",
        title="Informações do Sistema",
        border_style="green",
        height=3,
        padding=(0, 2)
    )
    
    connection_status = check_connection_status()
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
    
    # Reduz espaço entre painéis e menu
    console.print("\n[bold cyan]Gerador de Certificados em Lote[/bold cyan]")
    console.print("[dim]Use os comandos abaixo para gerenciar seus certificados.[/dim]")
    
    # Exibir indicador de modo debug no rodapé quando estiver ativado
    if parameter_manager.get_debug_mode():
        console.print("\n[bold red]🐛 [DEBUG MODE ATIVADO] 🐛[/bold red]")


def main_menu():
    """Exibe o menu principal da aplicação."""
    print_header()
    
    # Lista básica de opções do menu
    menu_options = [
        "🔖 Gerar Certificados",
        "🎨 Gerenciar Templates",
        "⚙️ Configurações",
        "🔄 Sincronização e Conectividade",
        "❓ Ajuda",
        "🚪 Sair"
    ]
    
    # Adicionar opções de debug se o modo debug estiver ativado
    debug_mode = parameter_manager.get_debug_mode()
    if debug_mode:
        # Inserir as opções de debug antes da Ajuda
        menu_options.insert(-2, "🐛 DEBUG: Comparar temas")
        menu_options.insert(-2, "🐛 DEBUG: Verificar sistema")
    
    choice = quiet_select(
        "Selecione uma opção:",
        choices=menu_options,
        use_indicator=True,
        style=get_menu_style()
    )
    
    if choice == "🔖 Gerar Certificados":
        generate_certificates_menu()
    elif choice == "🎨 Gerenciar Templates":
        manage_templates_menu()
    elif choice == "⚙️ Configurações":
        settings_menu()
    elif choice == "🔄 Sincronização e Conectividade":
        connectivity_menu()
    elif choice == "🐛 DEBUG: Comparar temas":
        debug_compare_themes()
    elif choice == "🐛 DEBUG: Verificar sistema":
        debug_system_check()
    elif choice == "❓ Ajuda":
        show_help()
    elif choice == "🚪 Sair":
        console.print("[bold green]Obrigado por usar o NEPEM Cert. Até logo![/bold green]")
        return False
    
    return True


# Funções de implementação para o menu de templates

def list_templates():
    """Lista os templates disponíveis."""
    console.clear()
    console.print("[bold blue]== Templates Disponíveis ==[/bold blue]\n")
    
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[yellow]Nenhum template encontrado.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Nome do Template", style="cyan")
        table.add_column("Tamanho", justify="right")
        table.add_column("Última Modificação")
        
        for template in templates:
            template_path = os.path.join(template_manager.templates_dir, template)
            size = os.path.getsize(template_path) / 1024  # KB
            mod_time = datetime.fromtimestamp(os.path.getmtime(template_path))
            
            table.add_row(
                template,
                f"{size:.1f} KB",
                mod_time.strftime("%d/%m/%Y %H:%M")
            )
        
        console.print(table)
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def import_template():
    """Importa um novo template."""
    console.clear()
    console.print("[bold blue]== Importar Novo Template ==[/bold blue]\n")
    
    # Solicitar caminho do template
    template_path = quiet_path(
        "Selecione o arquivo HTML do template:",
        validate=lambda path: os.path.exists(path) and path.lower().endswith('.html')
    )
    
    if not template_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Solicitar nome para salvar o template
    template_name = quiet_text(
        "Nome para salvar o template:",
        default=os.path.basename(template_path)
    )
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    if not template_name.lower().endswith('.html'):
        template_name += '.html'
    
    # Verificar se já existe um template com esse nome
    templates = template_manager.list_templates()
    if template_name in templates:
        overwrite = quiet_confirm(
            f"Já existe um template com o nome '{template_name}'. Deseja sobrescrever?"
        )
        
        if not overwrite:
            console.print("[yellow]Operação cancelada.[/yellow]")
            return
    
    # Ler o conteúdo do arquivo original
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Salvar o template
        template_manager.save_template(template_name, template_content)
        console.print(f"[bold green]✓ Template '{template_name}' importado com sucesso![/bold green]")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao importar template:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def edit_template():
    """Edita um template existente."""
    console.clear()
    console.print("[bold blue]== Editar Template ==[/bold blue]\n")
    
    # Listar templates disponíveis
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[yellow]Nenhum template disponível para edição.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
    
    # Selecionar template para editar    
    template_name = quiet_select(
        "Selecione o template para editar:",
        choices=templates,
        style=get_menu_style()
    )
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar conteúdo do template
    template_content = template_manager.load_template(template_name)
    if not template_content:
        console.print(f"[bold red]Erro ao carregar template:[/bold red] Arquivo não encontrado.")
        return
    
    console.print(f"[bold]Conteúdo atual do template:[/bold] {template_name}\n")
    console.print(Syntax(template_content[:500] + "..." if len(template_content) > 500 else template_content, "html"))
    
    console.print("\n[yellow]Aviso: A edição direta de templates HTML via CLI é limitada.[/yellow]")
    console.print("[yellow]Para edições complexas, recomendamos usar um editor HTML externo.[/yellow]\n")
    
    # Oferecer opção para abrir em um editor externo
    open_option = quiet_confirm("Deseja abrir o template em um editor externo?")
    
    if open_option:
        template_path = os.path.join(template_manager.templates_dir, template_name)
        
        try:
            import subprocess
            try:
                os.startfile(template_path)  # Windows
            except AttributeError:
                try:
                    subprocess.call(["open", template_path])  # macOS
                except:
                    subprocess.call(["xdg-open", template_path])  # Linux
            
            console.print("[green]Template aberto no editor padrão.[/green]")
            console.print("[yellow]Lembre-se de salvar o arquivo após a edição.[/yellow]")
        
        except Exception as e:
            console.print(f"[bold red]Erro ao abrir o arquivo:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def delete_template():
    """Exclui um template."""
    console.clear()
    console.print("[bold blue]== Excluir Template ==[/bold blue]\n")
    
    # Listar templates disponíveis
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[yellow]Nenhum template disponível para exclusão.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
    
    # Selecionar template para excluir    
    template_name = quiet_select(
        "Selecione o template para excluir:",
        choices=templates,
        style=get_menu_style()
    )
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Confirmar exclusão
    confirm = quiet_confirm(
        f"Tem certeza que deseja excluir o template '{template_name}'? Esta ação não pode ser desfeita."
    )
    
    if not confirm:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Excluir o template
    result = template_manager.delete_template(template_name)
    
    if result:
        console.print(f"[bold green]✓ Template '{template_name}' excluído com sucesso![/bold green]")
    else:
        console.print(f"[bold red]Erro ao excluir template:[/bold red] Arquivo não encontrado.")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def preview_template():
    """Visualiza um template."""
    console.clear()
    console.print("[bold blue]== Visualizar Template ==[/bold blue]\n")
    
    # Listar templates disponíveis
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[yellow]Nenhum template disponível para visualização.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
    
    # Selecionar template para visualizar    
    template_name = quiet_select(
        "Selecione o template para visualizar:",
        choices=templates,
        style=get_menu_style()
    )
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar conteúdo do template
    template_content = template_manager.load_template(template_name)
    if not template_content:
        console.print(f"[bold red]Erro ao carregar template:[/bold red] Arquivo não encontrado.")
        return
    
    # Detectar placeholders no template
    placeholders = template_manager.extract_placeholders(template_content)
    
    console.print(f"[bold]Template:[/bold] {template_name}\n")
    
    # Mostrar informações sobre o template
    console.print("[bold]Visualização do HTML:[/bold]")
    console.print(Syntax(template_content[:1000] + "..." if len(template_content) > 1000 else template_content, "html"))
    
    if placeholders:
        console.print("\n[bold]Placeholders detectados:[/bold]")
        for i, placeholder in enumerate(placeholders, 1):
            console.print(f"{i}. [cyan]{{{{{placeholder}}}}}[/cyan]")
    else:
        console.print("\n[yellow]Nenhum placeholder detectado no template.[/yellow]")
    
    # Oferecer opção para gerar uma prévia em PDF com dados fictícios
    preview_option = quiet_confirm("Deseja gerar uma prévia em PDF com dados de exemplo?")
    
    if preview_option:
        # Criar dados de exemplo para os placeholders
        example_data = {}
        for placeholder in placeholders:
            example_data[placeholder] = f"Exemplo de {placeholder}"
        
        # Gerar PDF de prévia
        preview_path = os.path.join(certificate_service.output_dir, "preview_template.pdf") # Use service's output_dir
        
        try:
            with console.status("[bold green]Gerando prévia em PDF..."):
                # Preparar template temporário
                temp_name = f"temp_preview_{random.randint(1000, 9999)}.html"
                temp_path = os.path.join("templates", temp_name)
                
                try:
                    # Salvar template temporário
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(template_content)
                    
                    # Renderizar com dados de exemplo
                    html_content = template_manager.render_template(temp_name, example_data)
                      # Gerar PDF
                    pdf_generator.generate_pdf(html_content, preview_path, orientation='landscape')
                finally:
                    # Limpar arquivo temporário
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            console.print(f"[bold green]✓ Prévia gerada com sucesso![/bold green]")
            console.print(f"[bold]Caminho:[/bold] {preview_path}")
            
            # Oferecer opção para abrir o PDF
            open_option = quiet_confirm("Deseja abrir a prévia em PDF?")
            
            if open_option:
                import subprocess
                try:
                    os.startfile(preview_path)  # Windows
                except AttributeError:
                    try:
                        subprocess.call(["open", preview_path])  # macOS
                    except:
                        subprocess.call(["xdg-open", preview_path])  # Linux
        
        except Exception as e:
            console.print(f"[bold red]Erro ao gerar prévia:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


# Funções de implementação para as demais opções de menu (básicas)
def configure_directories():
    """Configura os diretórios de trabalho."""
    console.print("[yellow]Esta funcionalidade está planejada para uma futura atualização. Obrigado pela sua compreensão.[/yellow]")
    input("\nPressione Enter para voltar...")


def configure_appearance():
    """Configura aparência e tema."""
    console.print("[yellow]Esta funcionalidade está planejada para uma futura atualização. Obrigado pela sua compreensão.[/yellow]")
    input("\nPressione Enter para voltar...")


def configure_generation_parameters():
    """Configura parâmetros de geração de certificados."""
    console.clear()
    console.print("[bold blue]== Parâmetros de Geração de Certificados ==[/bold blue]\n")
    
    choice = quiet_select(
        "O que você deseja configurar?",
        choices=[
            "📝 Valores para campos institucionais",
            "🔤 Valores padrão para campos",
            "🖼️ Valores específicos para temas",
            "↩️ Voltar"
        ],
        style=get_menu_style()
    )
    
    if choice == "📝 Valores para campos institucionais":
        configure_institutional_placeholders()
    elif choice == "🔤 Valores padrão para campos":
        configure_default_placeholders()
    elif choice == "🖼️ Valores específicos para temas":
        configure_theme_placeholders()
    elif choice == "↩️ Voltar":
        return


def configure_institutional_placeholders():
    """Configura valores institucionais."""
    console.clear()
    console.print("[bold blue]== Configuração de Campos Institucionais ==[/bold blue]\n")
    
    # Carregar valores institucionais existentes
    institutional = parameter_manager.get_institutional_placeholders()
    
    # Exibir valores atuais
    if institutional:
        console.print("[bold]Valores atuais:[/bold]")
        table = Table(show_header=True, header_style="bold blue", box=box.SIMPLE)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")
        
        for field, value in institutional.items():
            table.add_row(field, value)
        
        console.print(table)
    else:
        console.print("[yellow]Nenhum valor institucional configurado.[/yellow]")
    
    # Menu de opções
    choice = quiet_select(
        "O que você deseja fazer?",
        choices=[
            "➕ Adicionar/editar campo",
            "🗑️ Remover campo",
            "↩️ Voltar"
        ],
        style=get_menu_style()
    )
    
    if choice == "➕ Adicionar/editar campo":
        field = quiet_text("Nome do campo:")
        if field:
            value = quiet_text(f"Valor para '{field}':")
            if field and value:
                parameter_manager.update_institutional_placeholders({field: value})
                console.print(f"[green]✓[/green] Campo '{field}' atualizado.")
                
                # Recarregar esta tela para mostrar valores atualizados
                configure_institutional_placeholders()
    
    elif choice == "🗑️ Remover campo":
        if not institutional:
            console.print("[yellow]Não há campos para remover.[/yellow]")
            input("\nPressione Enter para voltar...")
            configure_institutional_placeholders()
            return
        field_to_remove = quiet_select(
            "Selecione o campo para remover:",
            choices=list(institutional.keys()) + ["Cancelar"],
            style=get_menu_style()
        )
        
        if field_to_remove and field_to_remove != "Cancelar":
            confirm = quiet_confirm(f"Tem certeza que deseja remover '{field_to_remove}'?")
            if confirm:
                params = parameter_manager.parameters
                if "institutional_placeholders" in params and field_to_remove in params["institutional_placeholders"]:
                    del params["institutional_placeholders"][field_to_remove]
                    parameter_manager.save_parameters()
                    console.print(f"[green]✓[/green] Campo '{field_to_remove}' removido.")
                
                # Recarregar esta tela para mostrar valores atualizados
                configure_institutional_placeholders()
    
    elif choice == "↩️ Voltar":
        configure_generation_parameters()


def configure_default_placeholders():
    """Configura valores padrão."""
    # Implementação básica
    console.print("[yellow]Esta funcionalidade está planejada para uma futura atualização. Obrigado pela sua compreensão.[/yellow]")
    input("\nPressione Enter para voltar...")


def configure_theme_placeholders():
    """Configura valores para temas."""
    # Implementação básica
    console.print("[yellow]Esta funcionalidade está planejada para uma futura atualização. Obrigado pela sua compreensão.[/yellow]")
    input("\nPressione Enter para voltar...")


def manage_presets():
    """Gerencia presets de configuração."""
    console.print("[yellow]Esta funcionalidade está planejada para uma futura atualização. Obrigado pela sua compreensão.[/yellow]")
    input("\nPressione Enter para voltar...")

# Função principal do aplicativo
def main():
    """Função principal que inicializa o aplicativo."""
    # Exibe a tela de carregamento antes de iniciar
    try:
        from app.loading_screen import loading_dummy
        loading_dummy(4.0)  # Exibir por 4 segundos (só será exibido uma vez)
    except ImportError:
        # Se não conseguir importar a tela de carregamento, continua normalmente
        console.print("[yellow]Aviso: Módulo de carregamento não encontrado.[/yellow]")
    
    # Continuar com o menu principal após o carregamento
    while main_menu():
        pass

# Ponto de entrada do script
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Programa encerrado pelo usuário.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Erro inesperado:[/bold red] {str(e)}")


def verify_authentication_code():
    """Verifica a autenticidade de um código de certificado."""
    console.clear()
    console.print("[bold blue]== Verificação de Autenticidade de Certificado ==[/bold blue]\n")
    
    # Solicitar código de autenticação ou verificação
    code_type = quiet_select(
        "Tipo de código que você possui:",
        choices=[
            "Código de autenticação completo (32 caracteres)",
            "Código de verificação curto (8-9 caracteres)",
            "Voltar"
        ],
        style=get_menu_style()
    )
    
    if code_type == "Voltar":
        return
    
    # Solicitar o código conforme o tipo selecionado
    if code_type == "Código de autenticação completo (32 caracteres)":
        codigo = quiet_text("Digite o código de autenticação:").strip()
    else:
        codigo = quiet_text("Digite o código de verificação:").strip()
    
    if not codigo:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Verificar o código
    with console.status("[bold green]Verificando código..."):
        result = auth_manager.verificar_codigo(codigo)
    
    if result:
        console.print("[bold green]✓ Certificado autêntico![/bold green]\n")
        
        # Exibir detalhes do certificado
        table = Table(box=box.SIMPLE)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")
        
        for campo, valor in result.items():
            if campo not in ['codigo_verificacao', 'data_geracao']:  # Campos que não precisam ser exibidos
                table.add_row(campo, str(valor))
        
        console.print(table)
        
        # Opções adicionais
        options = quiet_select(
            "Opções adicionais:",
            choices=[
                "Verificar outro código",
                "Voltar ao menu"
            ],
            style=get_menu_style()
        )
        
        if options == "Verificar outro código":
            verify_authentication_code()  # Recursivamente chama a mesma função
        
    else:
        console.print("[bold red]❌ Código inválido ou não encontrado![/bold red]")
        console.print("\nPossíveis causas:")
        console.print("• O código foi digitado incorretamente")
        console.print("• O certificado não existe no sistema")
        console.print("• O certificado está em uma base de dados diferente")
        
        retry = quiet_confirm("Deseja tentar novamente?")
        if retry:
            verify_authentication_code()  # Recursivamente chama a mesma função
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()

def settings_menu():
    """Menu de configurações."""
    console.clear()
    console.print("[bold blue]== Configurações ==[/bold blue]\n")
    
    choice = quiet_select(
        "O que você deseja configurar?",
        choices=[
            "📁 Diretórios de trabalho",
            "🎨 Aparência e tema",
            "📊 Parâmetros de geração",
            "🔧 Configurações do sistema",
            "💾 Salvar/carregar presets",
            "↩️ Voltar ao menu principal"
        ],
        style=get_menu_style()
    )
    
    if choice == "📁 Diretórios de trabalho":
        configure_directories()
    elif choice == "🎨 Aparência e tema":
        configure_appearance()
    elif choice == "📊 Parâmetros de geração":
        configure_generation_parameters()
    elif choice == "🔧 Configurações do sistema":
        configure_system_settings()
    elif choice == "💾 Salvar/carregar presets":
        manage_presets()
    elif choice == "↩️ Voltar ao menu principal":
        return


def configure_system_settings():
    """Configurações gerais do sistema."""
    console.clear()
    console.print("[bold blue]== Configurações do Sistema ==[/bold blue]\n")
    
    # Verificar status atual do modo debug
    debug_mode = parameter_manager.get_debug_mode()
    debug_status = "[green]ATIVADO[/green]" if debug_mode else "[red]DESATIVADO[/red]"
    
    console.print(f"[bold]Status atual do modo DEBUG:[/bold] {debug_status}\n")
    console.print("[dim]O modo DEBUG exibe opções e informações adicionais para desenvolvedores e diagnóstico.[/dim]")
    console.print("[dim]Ativar este modo pode expor informações técnicas e funções experimentais.[/dim]\n")
    
    # Opções disponíveis para configurações do sistema
    choice = quiet_select(
        "O que você deseja configurar?",
        choices=[
            f"{'Desativar' if debug_mode else 'Ativar'} modo DEBUG",
            "↩️ Voltar"
        ],
        style=get_menu_style()
    )
    
    if choice == "Ativar modo DEBUG" or choice == "Desativar modo DEBUG":
        new_status = not debug_mode
        confirm_msg = "Tem certeza que deseja ATIVAR o modo DEBUG?" if new_status else "Tem certeza que deseja DESATIVAR o modo DEBUG?"
        
        confirm = quiet_confirm(confirm_msg)
        if confirm:
            result = parameter_manager.set_debug_mode(new_status)
            if result:
                status_msg = "[green]✓ Modo DEBUG ATIVADO com sucesso![/green]" if new_status else "[yellow]✓ Modo DEBUG DESATIVADO![/yellow]"
                console.print(status_msg)
                console.print("[dim]Esta configuração será mantida entre sessões do programa.[/dim]")
                
                if new_status:
                    console.print("\n[yellow]Atenção: Funções de DEBUG agora estão visíveis no menu principal.[/yellow]")
                    console.print("[yellow]Estas incluem:[/yellow]")
                    console.print("[dim]  • DEBUG: Comparar temas[/dim]")
                    console.print("[dim]  • DEBUG: Verificar sistema[/dim]")
            else:
                console.print("[bold red]Erro ao salvar configuração![/bold red]")
        
        # Mostrar novamente o menu de configurações do sistema
        console.print("\n[dim]Pressione Enter para continuar...[/dim]")
        input()
        configure_system_settings()
    
    elif choice == "↩️ Voltar":
        settings_menu()


def manage_templates_menu():
    """Menu para gerenciamento de templates."""
    console.clear()
    console.print("[bold blue]== Gerenciamento de Templates ==[/bold blue]\n")
    
    choice = quiet_select(
        "O que você deseja fazer?",
        choices=[
            "📄 Listar templates",
            "📥 Importar template",
            "✏️ Editar template",
            "🗑️ Excluir template",
            "👁️ Visualizar template",
            "🧪 Testar geração de certificado",
            "📊 Visualizar dados CSV",
            "↩️ Voltar ao menu principal"
        ],
        style=get_menu_style()
    )
    
    if choice == "📄 Listar templates":
        list_templates()
    elif choice == "📥 Importar template":
        import_template()
    elif choice == "✏️ Editar template":
        edit_template()
    elif choice == "🗑️ Excluir template":
        delete_template()
    elif choice == "👁️ Visualizar template":
        preview_template()
    elif choice == "🧪 Testar geração de certificado":
        generate_certificate_single()
    elif choice == "📊 Visualizar dados CSV":
        preview_imported_data()
    elif choice == "↩️ Voltar ao menu principal":
        return
    
    # Retornar ao menu de templates após cada operação
    manage_templates_menu()


def show_help():
    """Exibe a ajuda do sistema."""
    console.clear()
    console.print("[bold blue]== Ajuda do NEPEM Cert ==[/bold blue]\n")
    
    help_content = """
[bold]NEPEM Cert - Gerador de Certificados em Lote[/bold]

[bold cyan]Funcionalidades Principais:[/bold cyan]
• [green]Geração de Certificados:[/green] Crie certificados em lote a partir de templates HTML e dados CSV
• [green]Gerenciamento de Templates:[/green] Importe, edite e gerencie templates de certificados
• [green]Temas Personalizados:[/green] Aplique diferentes estilos visuais aos seus certificados
• [green]Configurações Flexíveis:[/green] Configure valores padrão, institucionais e específicos por tema

[bold cyan]Como Usar:[/bold cyan]
1. [yellow]Prepare seu arquivo CSV[/yellow] com uma coluna contendo os nomes dos participantes
2. [yellow]Importe um template HTML[/yellow] ou use um dos templates existentes
3. [yellow]Configure os parâmetros[/yellow] institucionais e valores padrão
4. [yellow]Gere os certificados[/yellow] informando os dados do evento

[bold cyan]Formatos Suportados:[/bold cyan]
• [green]Templates:[/green] Arquivos HTML com placeholders no formato {{ placeholder }}
• [green]Dados:[/green] Arquivos CSV com encoding UTF-8
• [green]Saída:[/green] Certificados em PDF e opcionalmente empacotados em ZIP

[bold cyan]Placeholders Disponíveis:[/bold cyan]
• {{ nome }} - Nome do participante
• {{ evento }} - Nome do evento
• {{ data }} - Data do evento
• {{ local }} - Local do evento
• {{ carga_horaria }} - Carga horária do evento
• {{ codigo_autenticacao }} - Código único de autenticação
• {{ codigo_verificacao }} - Código de verificação
• {{ data_emissao }} - Data de emissão do certificado

[bold cyan]Dicas Importantes:[/bold cyan]
• Use encoding UTF-8 nos arquivos CSV para evitar problemas com acentos
• Templates HTML devem ser compatíveis com a biblioteca de geração de PDF
• Evite elementos CSS complexos como flexbox ou posicionamento absoluto
• Configure valores institucionais para reutilizar informações comuns

[bold [bold cyan]Suporte:[/bold cyan]
• Versão atual: v1.1.0
• Para problemas técnicos, ative o modo DEBUG nas configurações
• Templates de exemplo estão disponíveis na pasta 'templates'
"""
    
    console.print(help_content)
    
    input("\n[dim]Pressione Enter para voltar ao menu principal...[/dim]")
    """Exibe a ajuda do sistema."""
    console.clear()
    console.print("[bold blue]== Ajuda do NEPEM Cert ==[/bold blue]\n")
    
    help_content = """
[bold]NEPEM Cert - Gerador de Certificados em Lote[/bold]

[bold cyan]Funcionalidades Principais:[/bold cyan]
• [green]Geração de Certificados:[/green] Crie certificados em lote a partir de templates HTML e dados CSV
• [green]Gerenciamento de Templates:[/green] Importe, edite e gerencie templates de certificados
• [green]Temas Personalizados:[/green] Aplique diferentes estilos visuais aos seus certificados
• [green]Configurações Flexíveis:[/green] Configure valores padrão, institucionais e específicos por tema

[bold cyan]Como Usar:[/bold cyan]
1. [yellow]Prepare seu arquivo CSV[/yellow] com uma coluna contendo os nomes dos participantes
2. [yellow]Importe um template HTML[/yellow] ou use um dos templates existentes
3. [yellow]Configure os parâmetros[/yellow] institucionais e valores padrão
4. [yellow]Gere os certificados[/yellow] informando os dados do evento

[bold cyan]Formatos Suportados:[/bold cyan]
• [green]Templates:[/green] Arquivos HTML com placeholders no formato {{ placeholder }}
• [green]Dados:[/green] Arquivos CSV com encoding UTF-8
• [green]Saída:[/green] Certificados em PDF e opcionalmente empacotados em ZIP

[bold cyan]Placeholders Disponíveis:[/bold cyan]
• {{ nome }} - Nome do participante
• {{ evento }} - Nome do evento
• {{ data }} - Data do evento
• {{ local }} - Local do evento
• {{ carga_horaria }} - Carga horária do evento
• {{ codigo_autenticacao }} - Código único de autenticação
• {{ codigo_verificacao }} - Código de verificação
• {{ data_emissao }} - Data de emissão do certificado

[bold cyan]Dicas Importantes:[/bold cyan]
• Use encoding UTF-8 nos arquivos CSV para evitar problemas com acentos
• Templates HTML devem ser compatíveis com a biblioteca de geração de PDF
• Evite elementos CSS complexos como flexbox ou posicionamento absoluto
• Configure valores institucionais para reutilizar informações comuns

[bold [bold cyan]Suporte:[/bold cyan]
• Versão atual: v1.1.0
• Para problemas técnicos, ative o modo DEBUG nas configurações
• Templates de exemplo estão disponíveis na pasta 'templates'
"""
    
    console.print(help_content)
    
    input("\n[dim]Pressione Enter para voltar ao menu principal...[/dim]")
