import os
import sys
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box
import questionary
from contextlib import redirect_stderr
from io import StringIO

# Importações dos módulos da aplicação
from app.connectivity_manager import ConnectivityManager
from app.template_manager import TemplateManager
from app.certificate_service import CertificateService

# Inicializar console e componentes
console = Console()
connectivity_manager = ConnectivityManager()
template_manager = TemplateManager()
certificate_service = CertificateService()

# Wrapper functions para questionary
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

def connectivity_menu():
    """Menu de conectividade e sincronização."""
    console.clear()
    console.print("[bold blue]== Sincronização e Conectividade ==[/bold blue]\n")
    
    # Verificar status da conexão
    status_info = connectivity_manager.get_connection_status()
    status_color = {
        "Conectado": "green",
        "Desconectado": "red",
        "Aguardando": "yellow"
    }.get(status_info["status"], "yellow")
    
    console.print(f"[bold]Status atual:[/bold] [{status_color}]{status_info['status']}[/{status_color}]")
    console.print(f"[bold]Última verificação:[/bold] {status_info.get('last_check', 'Nunca')}")
    
    # Verificar certificados não sincronizados
    try:
        from app.offline_sync_manager import OfflineSyncManager
        sync_manager = OfflineSyncManager()
        
        pending_count = sync_manager.get_pending_count()
        if pending_count > 0:
            console.print(f"\n[yellow]⚠️  {pending_count} certificado(s) aguardando sincronização[/yellow]")
    except Exception:
        pass
    
    choice = quiet_select(
        "\nO que você deseja fazer?",
        choices=[
            "🔄 Verificar conexão",
            "⚙️ Configurar servidor",
            "📤 Sincronizar Certificados Pendentes",
            "📥 Baixar Templates do Servidor",
            "📊 Ver Estatísticas de Sincronização",
            "📋 Histórico de sincronização", 
            "↩️ Voltar ao menu principal"
        ],
        style=get_menu_style()
    )
    
    if choice == "🔄 Verificar conexão":
        console.clear()
        console.print("[bold blue]== Status da Conexão ==[/bold blue]\n")
        
        if not connectivity_manager.config.get("server_url"):
            console.print("[yellow]URL do servidor não configurada. Configure o servidor primeiro.[/yellow]")
            console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
            input()
            connectivity_menu()
            return

        with console.status("[bold green]Verificando conexão com o servidor...", spinner="dots"):
            result = connectivity_manager.check_connection() 
        
        status_color = "green" if result.get("status") == "Conectado" else "red"
        console.print(f"Status: [{status_color}]{result.get('status', 'Desconhecido')}[/{status_color}]")
        console.print(f"Mensagem: {result.get('message', 'N/A')}")
        console.print(f"Horário da Verificação: {result.get('timestamp', 'N/A')}")
        console.print(f"URL do Servidor: {connectivity_manager.config.get('server_url', 'Não configurada')}")

        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        connectivity_menu()
    
    elif choice == "⚙️ Configurar servidor":
        configure_remote_server()
        connectivity_menu()
    
    elif choice == "📤 Sincronizar Certificados Pendentes":
        sync_pending_certificates()
        connectivity_menu()
    
    elif choice == "📊 Ver Estatísticas de Sincronização":
        show_sync_statistics()
        connectivity_menu()

    elif choice == "📥 Baixar Templates do Servidor": 
        download_templates_ui() 
        # connectivity_menu() is called at the end of download_templates_ui
    
    elif choice == "📋 Histórico de sincronização":
        show_sync_history_stub()
        # connectivity_menu() is called at the end of show_sync_history_stub
    
    elif choice == "↩️ Voltar ao menu principal":
        return


def show_sync_history_stub():
    """Placeholder for showing synchronization history."""
    console.clear()
    console.print("[bold blue]== Histórico de Sincronização ==[/bold blue]\n")
    console.print("[yellow]Esta funcionalidade está planejada para uma futura atualização. Obrigado pela sua compreensão.[/yellow]")
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()
    connectivity_menu() # Return to connectivity menu


def sync_pending_certificates():
    """Sincroniza certificados pendentes no banco de dados local."""
    console.clear()
    console.print("[bold blue]== Sincronizar Certificados Pendentes ==[/bold blue]\n")
    
    try:
        from app.offline_sync_manager import OfflineSyncManager
        from app.auto_sync_service import AutoSyncService
        
        sync_manager = OfflineSyncManager()
        
        # Verificar se há certificados pendentes
        pending_count = sync_manager.get_pending_count()
        
        if pending_count == 0:
            console.print("[green]✓ Todos os certificados estão sincronizados![/green]")
            console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
            input()
            return
        
        console.print(f"[yellow]Encontrados {pending_count} certificado(s) pendente(s) de sincronização.[/yellow]\n")
        
        confirm = quiet_confirm("Deseja iniciar a sincronização agora?", default=True)
        if not confirm:
            console.print("[yellow]Sincronização cancelada.[/yellow]")
            console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
            input()
            return
        
        # Iniciar serviço de sincronização
        console.print("\n[bold green]Iniciando sincronização...[/bold green]")
        auto_sync = AutoSyncService()
        
        with console.status("[bold green]Sincronizando certificados...") as status:
            result = auto_sync.force_sync()
        
        console.print("\n[bold]Resultado da Sincronização:[/bold]")
        console.print(f"[green]✓ Sincronizados com sucesso: {result.get('success', 0)}[/green]")
        
        if result.get('failed', 0) > 0:
            console.print(f"[red]✗ Falhas: {result.get('failed', 0)}[/red]")
        
        if result.get('error'):
            console.print(f"[red]Erro: {result['error']}[/red]")
        
    except Exception as e:
        console.print(f"[red]Erro durante sincronização: {str(e)}[/red]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def show_sync_statistics():
    """Exibe estatísticas detalhadas de sincronização."""
    console.clear()
    console.print("[bold blue]== Estatísticas de Sincronização ==[/bold blue]\n")
    
    try:
        from app.offline_sync_manager import OfflineSyncManager
        
        sync_manager = OfflineSyncManager()
        stats = sync_manager.get_sync_statistics()
        
        if not stats:
            console.print("[yellow]Não há estatísticas disponíveis.[/yellow]")
            console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
            input()
            return
        
        # Criar tabela de estatísticas
        table = Table(title="Resumo de Sincronização", box=box.ROUNDED)
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", justify="right", style="white")
        
        status_counts = stats.get('status_counts', {})
        
        table.add_row("Total de Certificados", str(stats.get('total_records', 0)))
        table.add_row("✓ Sincronizados", f"[green]{stats.get('synced_count', 0)}[/green]")
        table.add_row("⏳ Pendentes", f"[yellow]{stats.get('pending_count', 0)}[/yellow]")
        table.add_row("🔄 Aguardando Retry", f"[blue]{stats.get('retry_count', 0)}[/blue]")
        table.add_row("✗ Falhados", f"[red]{stats.get('failed_count', 0)}[/red]")
        table.add_row("", "")  # Linha vazia
        table.add_row("Últimas 24h", str(stats.get('last_24h_count', 0)))
        table.add_row("Média de Tentativas", f"{stats.get('avg_sync_attempts', 0):.1f}")
        table.add_row("Máximo de Tentativas", str(stats.get('max_sync_attempts', 0)))
        
        console.print(table)
        
        # Mostrar alerta se houver pendentes
        alert = sync_manager.get_sync_alert()
        if alert:
            console.print("\n[bold yellow]⚠️  Certificados Mais Antigos Não Sincronizados:[/bold yellow]")
            for cert in alert.get('certificados_antigos', []):
                console.print(f"  • [cyan]{cert['nome']}[/cyan] - {cert['evento']}")
                console.print(f"    Criado em: {cert['criado_em']}")
        
        console.print(f"\n[dim]Banco de dados: {stats.get('db_path', 'N/A')}[/dim]")
        console.print(f"[dim]Última atualização: {stats.get('last_updated', 'N/A')}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Erro ao obter estatísticas: {str(e)}[/red]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def check_connection():
    """Verifica o status da conexão."""
    console.clear()
    console.print("[bold blue]== Status da Conexão ==[/bold blue]\n")
    
    with console.status("[bold green]Verificando conexão com o servidor..."):
        result = connectivity_manager.check_connection()
    
    status_color = {
        "Conectado": "green",
        "Desconectado": "red",
        "Aguardando": "yellow"
    }.get(result["status"], "yellow")
    
    # Criar textos formatados do Rich para evitar que as tags apareçam
    console.print(Text.from_markup(f"[bold]Status:[/bold] "), end="")
    console.print(Text(result["status"], style=status_color))
    
    console.print(Text.from_markup(f"[bold]Mensagem:[/bold] {result['message']}"))
    console.print(Text.from_markup(f"[bold]Horário:[/bold] {result['timestamp']}"))
    
    if "server_url" in connectivity_manager.config and connectivity_manager.config["server_url"]:
        console.print(Text.from_markup(f"[bold]URL do servidor:[/bold] {connectivity_manager.config['server_url']}"))
    else:
        console.print(Text("Servidor não configurado.", style="yellow"))
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def configure_remote_server():
    """Configura as opções de conexão com o servidor remoto."""
    console.clear()
    console.print("[bold blue]== Configurar Conexão com Servidor Remoto ==[/bold blue]\n")

    current_config = connectivity_manager.config
    console.print(f"URL do Servidor Atual: [cyan]{current_config.get('server_url', 'Não configurado')}[/cyan]")
    console.print(f"Chave de API Atual: [cyan]{'Configurada' if current_config.get('api_key') else 'Não configurada'}[/cyan]")
    console.print(f"Usuário Atual: [cyan]{current_config.get('username', 'Não configurado')}[/cyan]")
    console.print("---\n")

    new_url = quiet_text(
        "Nova URL do Servidor (deixe em branco para manter atual):",
        default=current_config.get('server_url', '')
    ).strip()

    new_api_key = quiet_text(
        "Nova Chave de API (deixe em branco para manter atual, '#' para limpar):",
        default=""  # Don't show current API key
    ).strip()

    new_username = quiet_text(
        "Novo Usuário (deixe em branco para manter atual, '#' para limpar):",
        default=current_config.get('username', '')
    ).strip()
    
    new_password = quiet_text(
        "Nova Senha (deixe em branco para não alterar se usuário não mudar; '#' para limpar senha):",
        default="" # Do not display current password
    ).strip()

    changes_made = False
    if new_url != current_config.get('server_url', ''): # Check against empty string if not set
        connectivity_manager.set_server_url(new_url)
        console.print(f"[green]✓ URL do servidor atualizada para: {new_url if new_url else 'Nenhuma (removida)'}[/green]")
        changes_made = True

    if new_api_key: # Only process if user typed something for API key
        if new_api_key == '#':
            if current_config.get('api_key'): # Only print if there was a key
                connectivity_manager.set_api_key("")
                console.print("[yellow]✓ Chave de API removida.[/yellow]")
                changes_made = True
            else:
                console.print("[dim]Nenhuma chave de API para remover.[/dim]")
        else:
            connectivity_manager.set_api_key(new_api_key)
            console.print("[green]✓ Chave de API atualizada.[/green]")
            changes_made = True
    
    # Username and Password Logic
    current_username_val = current_config.get('username', '')
    current_password_val = current_config.get('password', '') # Needed for comparison
    
    processed_username = current_username_val
    username_explicitly_changed = False

    if new_username: # User typed something for username
        if new_username == '#':
            if current_username_val: # Only if there was a username
                processed_username = ""
                console.print("[yellow]✓ Usuário removido.[/yellow]")
                username_explicitly_changed = True
            else:
                console.print("[dim]Nenhum usuário para remover.[/dim]")
        elif new_username != current_username_val:
            processed_username = new_username
            console.print(f"[green]✓ Usuário atualizado para: {processed_username}[/green]")
            username_explicitly_changed = True
        # If new_username is same as current_username_val, no change yet for username itself

    processed_password = current_password_val

    if new_password: # User typed something for password
        if new_password == '#':
            if current_password_val: # Only if there was a password
                processed_password = ""
                console.print("[yellow]✓ Senha removida.[/yellow]")
            else:
                console.print("[dim]Nenhuma senha para remover.[/dim]")
        else:
            processed_password = new_password
            console.print("[green]✓ Senha atualizada.[/green]")
    elif username_explicitly_changed and processed_username != "": 
        # Username changed (and not to blank), but no new password typed. Clear old password.
        if current_password_val: # Only if there was an old password
            processed_password = ""
            console.print("[yellow]✓ Senha anterior removida devido à mudança de usuário. Defina uma nova senha se necessário.[/yellow]")
    
    # If username is cleared, password must also be cleared
    if processed_username == "" and current_username_val != "": # If username was just cleared
        if current_password_val: # And there was a password
             processed_password = "" # Ensure password is also cleared
             console.print("[yellow]✓ Senha removida pois usuário foi removido.[/yellow]")


    # Update credentials if they actually changed from what's stored
    if processed_username != current_username_val or processed_password != current_password_val:
        connectivity_manager.set_credentials(processed_username, processed_password)
        changes_made = True # This ensures save_config is called

    if not changes_made:
        console.print("\n[dim]Nenhuma alteração feita.[/dim]")
    else:
        connectivity_manager.save_config() 
        console.print("\n[bold green]✓ Configurações de conexão salvas com sucesso![/bold green]")

    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def upload_certificates_ui():
    """Interface do usuário para enviar certificados para o servidor remoto."""
    console.clear()
    console.print("[bold blue]== Enviar Certificados para Servidor Remoto ==[/bold blue]\n")

    # Check if server is configured
    if not connectivity_manager.config.get("server_url"):
        console.print("[yellow]URL do servidor não configurada. Configure o servidor primeiro.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return

    console.print(f"Enviando para: [cyan]{connectivity_manager.config['server_url']}[/cyan]")

    default_output_dir = certificate_service.output_dir # Use global certificate_service instance

    pdf_dir = quiet_path(
        "Selecione o diretório contendo os certificados PDF para enviar:",
        default=default_output_dir,
        only_directories=True,
        validate=lambda path: os.path.isdir(path)
    )

    if not pdf_dir:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return

    # List PDF files in the selected directory
    try:
        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
        if not pdf_files:
            console.print(f"[yellow]Nenhum arquivo PDF encontrado em '{pdf_dir}'.[/yellow]")
            console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
            input()
            return
        
        console.print(f"\nArquivos PDF encontrados em '{os.path.basename(pdf_dir)}':")
        for i, fname in enumerate(pdf_files):
             console.print(f"  {i+1}. {fname}")

    except Exception as e:
        console.print(f"[red]Erro ao listar arquivos PDF: {str(e)}[/red]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Ask for confirmation
    confirm_upload = quiet_confirm(f"\nDeseja enviar {len(pdf_files)} certificado(s) para o servidor?")
    if not confirm_upload:
        console.print("[yellow]Envio cancelado.[/yellow]")
        return

    full_file_paths = [os.path.join(pdf_dir, fname) for fname in pdf_files]

    with console.status("[bold green]Enviando certificados...", spinner="dots") as status:
        result = connectivity_manager.upload_certificates(full_file_paths)

        if result.get("success", False):
            status.update("[bold green]Certificados enviados com sucesso![/bold green]")
            console.print(f"\n[green]✓ {result.get('message', 'Envio concluído.')}[/green]")
            if result.get("files_processed") is not None: # Check if key exists
                console.print(f"  Arquivos processados: {result.get('files_processed')}")
            if result.get("details"): # Assuming 'details' is a list of dicts
                console.print("  Detalhes do envio:")
                for item in result.get("details", []):
                    item_status = item.get('status', 'N/A')
                    item_error = item.get('error', '')
                    error_msg = f", Erro: {item_error}" if item_error else ""
                    console.print(f"    - Arquivo: {item.get('filename', 'N/A')}, Status: {item_status}{error_msg}")
        else:
            status.update("[bold red]Falha no envio dos certificados.[/bold red]")
            console.print(f"\n[red]✗ {result.get('message', 'Erro desconhecido durante o envio.')}[/red]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def download_templates_ui():
    """Interface do usuário para baixar templates do servidor remoto."""
    console.clear()
    console.print("[bold blue]== Baixar Templates do Servidor Remoto ==[/bold blue]\n")

    if not connectivity_manager.config.get("server_url"):
        console.print("[yellow]URL do servidor não configurada. Configure o servidor primeiro.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return

    console.print(f"Buscando templates de: [cyan]{connectivity_manager.config['server_url']}[/cyan]")

    with console.status("[bold green]Buscando lista de templates disponíveis...", spinner="dots") as status:
        list_result = connectivity_manager.download_templates() # This lists templates

        if not list_result.get("success") or not list_result.get("templates"):
            status.update("[bold red]Falha ao buscar templates.[/bold red]")
            message = list_result.get('message', 'Não foi possível obter a lista de templates do servidor.')
            console.print(f"[red]✗ {message}[/red]")
            if isinstance(list_result.get("templates"), list) and not list_result.get("templates") and list_result.get("success"):
                 console.print("[yellow]Nenhum template encontrado no servidor.[/yellow]")
            console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
            input()
            return
        
        status.update("[bold green]Lista de templates recebida.[/bold green]")
        remote_templates = list_result.get("templates", [])

    console.print("\n[bold]Templates disponíveis no servidor:[/bold]")
    
    if not remote_templates: # Should be caught above, but double check
        console.print("[yellow]Nenhum template encontrado no servidor.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return

    template_choices = []
    for idx, t_info in enumerate(remote_templates):
        choice_label = f"{t_info.get('name', f'Template {idx+1}')}"
        if t_info.get('description'):
            choice_label += f" - {t_info.get('description')}"
        if t_info.get('version'): # Assuming API might provide version
            choice_label += f" (v{t_info.get('version')})"
        template_choices.append({"name": choice_label, "value": t_info.get('name'), "checked": False})

    if not template_choices:
        console.print("[red]Erro ao processar lista de templates recebidos.[/red]")
        input("\nPressione Enter para voltar...")
        return

    selected_template_names = quiet_checkbox(
        "Selecione os templates que deseja baixar (espaço para marcar, Enter para confirmar):",
        choices=template_choices
    )

    if not selected_template_names:
        console.print("[yellow]Nenhum template selecionado para download.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return

    console.print(f"\nBaixando {len(selected_template_names)} template(s)...")
    target_template_dir = template_manager.templates_dir 
    os.makedirs(target_template_dir, exist_ok=True)
    
    downloaded_count = 0
    failed_count = 0
    download_errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        transient=False # Keep progress bar visible after completion
    ) as progress_bar:
        download_task = progress_bar.add_task("Baixando...", total=len(selected_template_names))

        for template_name_to_download in selected_template_names:
            if not template_name_to_download: continue

            progress_bar.update(download_task, description=f"Baixando {template_name_to_download}...")
            
            local_template_path = os.path.join(target_template_dir, template_name_to_download)
            if os.path.exists(local_template_path):
                overwrite = quiet_confirm(
                    f"O template '{template_name_to_download}' já existe localmente. Deseja sobrescrevê-lo?",
                    default=False
                )
                if not overwrite:
                    console.print(f"[yellow]Download de '{template_name_to_download}' pulado.[/yellow]")
                    progress_bar.update(download_task, advance=1)
                    continue
            
            download_specific_result = connectivity_manager.download_specific_template(
                template_name_to_download, 
                target_template_dir
            )

            if download_specific_result.get("success"):
                console.print(f"[green]✓ Template '{template_name_to_download}' baixado para '{target_template_dir}'.[/green]")
                downloaded_count += 1
            else:
                error_msg = download_specific_result.get('message', 'Erro desconhecido')
                console.print(f"[red]✗ Falha ao baixar '{template_name_to_download}': {error_msg}[/red]")
                failed_count += 1
                download_errors.append(f"{template_name_to_download}: {error_msg}")
            progress_bar.update(download_task, advance=1)

    console.print("\n[bold]Resumo do Download:[/bold]")
    console.print(f"[green]Templates baixados com sucesso: {downloaded_count}[/green]")
    if failed_count > 0:
        console.print(f"[red]Falhas no download: {failed_count}[/red]")
        if download_errors:
             console.print("[bold red]Detalhes dos erros:[/bold red]")
             for error in download_errors:
                 console.print(f"  - {error}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def configure_credentials():
    """Configura credenciais de acesso ao servidor."""
    console.print("[yellow]Função ainda não implementada completamente.[/yellow]")
    input("\nPressione Enter para voltar...")
