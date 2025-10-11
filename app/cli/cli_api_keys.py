"""
Menu CLI para gerenciamento de chaves de API

Fornece interface interativa para:
- Criar novas chaves de API
- Listar chaves carregadas
- Testar conexão com servidor
- Configurar chaves iniciais
"""

import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Adicionar diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.api_client import CertificateAPIClient
from app.api_key_manager import APIKeyManager

console = Console()


def api_keys_menu():
    """Menu principal de gerenciamento de chaves de API"""
    
    # Importar wrappers do questionary
    try:
        from cli import quiet_select, quiet_text, quiet_confirm
    except ImportError:
        # Fallback se não conseguir importar
        import questionary
        quiet_select = questionary.select
        quiet_text = questionary.text
        quiet_confirm = questionary.confirm
    
    # Inicializar gerenciadores
    key_manager = APIKeyManager()
    api_client = CertificateAPIClient()
    
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]Gerenciamento de Chaves de API[/bold cyan]\n"
            "[dim]Gerencie chaves para autenticação com certificados.nepemufsc.com[/dim]",
            border_style="cyan"
        ))
        
        # Tentar carregar chave ativa
        active_key = key_manager.get_active_key()
        if not active_key:
            key_manager.autoload_keys()
            active_key = key_manager.get_active_key()
        
        # Exibir chave ativa
        if active_key:
            console.print(f"\n🔑 Chave ativa: [green]{active_key.key_id}[/green] ([cyan]{active_key.role}[/cyan])")
        else:
            console.print("\n⚠️ [yellow]Nenhuma chave carregada[/yellow]")
        
        # Menu de opções
        choice = quiet_select(
            "\nSelecione uma opção:",
            choices=[
                "🔑 Configurar Chaves Iniciais",
                "➕ Criar Nova Chave",
                "📋 Listar Chaves Carregadas",
                "🔄 Recarregar Chaves do Diretório",
                "🔍 Testar Conexão com Servidor",
                "⚙️ Configurações da API",
                "🔙 Voltar ao Menu Principal"
            ]
        )
        
        if choice == "🔑 Configurar Chaves Iniciais":
            setup_initial_keys(api_client)
        
        elif choice == "➕ Criar Nova Chave":
            create_new_key(api_client, key_manager)
        
        elif choice == "📋 Listar Chaves Carregadas":
            list_loaded_keys(key_manager)
        
        elif choice == "🔄 Recarregar Chaves do Diretório":
            reload_keys(key_manager)
        
        elif choice == "🔍 Testar Conexão com Servidor":
            test_server_connection(api_client)
        
        elif choice == "⚙️ Configurações da API":
            api_settings(api_client)
        
        elif choice == "🔙 Voltar ao Menu Principal":
            break
        
        if choice != "🔙 Voltar ao Menu Principal":
            console.print("\n[dim]Pressione Enter para continuar...[/dim]")
            input()


def setup_initial_keys(api_client: CertificateAPIClient):
    """Configura chaves iniciais (issuer e reader)"""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Configuração Inicial de Chaves[/bold cyan]\n"
        "[dim]Cria chaves issuer e reader usando a chave master admin[/dim]",
        border_style="cyan"
    ))
    
    console.print("\n⚠️ Esta operação criará:")
    console.print("  • Uma chave [green]ISSUER[/green] (para registrar certificados)")
    console.print("  • Uma chave [blue]READER[/blue] (para consultar certificados)")
    console.print("\n[yellow]As chaves serão salvas no diretório 'keys/'[/yellow]")
    
    try:
        from cli import quiet_confirm
    except ImportError:
        import questionary
        quiet_confirm = questionary.confirm
    
    if not quiet_confirm("\nDeseja continuar?", default=False):
        return
    
    try:
        with console.status("[bold green]Criando chaves..."):
            results = api_client.setup_initial_keys()
        
        console.print("\n" + "="*60)
        if results['issuer']:
            console.print("✅ Chave ISSUER criada:", results['issuer'].key_id)
        else:
            console.print("❌ Falha ao criar chave ISSUER")
        
        if results['reader']:
            console.print("✅ Chave READER criada:", results['reader'].key_id)
        else:
            console.print("❌ Falha ao criar chave READER")
        
    except Exception as e:
        console.print(f"\n❌ Erro durante configuração: {e}", style="bold red")


def create_new_key(api_client: CertificateAPIClient, key_manager: APIKeyManager):
    """Cria uma nova chave de API"""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Criar Nova Chave de API[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        from cli import quiet_select, quiet_text, quiet_confirm
    except ImportError:
        import questionary
        quiet_select = questionary.select
        quiet_text = questionary.text
        quiet_confirm = questionary.confirm
    
    # Selecionar role
    role = quiet_select(
        "\nSelecione o tipo de chave:",
        choices=[
            "issuer - Pode criar e modificar certificados",
            "reader - Pode apenas consultar certificados",
            "admin - Acesso total (criar outras chaves)",
        ]
    ).split(" -")[0]
    
    # Descrição
    description = quiet_text(
        "\nDescrição da chave (opcional):",
        default=f"Chave {role} criada via NEPEMCERT"
    )
    
    # Confirmar
    if not quiet_confirm(f"\nCriar chave {role.upper()}?", default=True):
        return
    
    try:
        # Verificar se tem chave para autenticação
        auth_key = key_manager.get_active_key()
        if not auth_key:
            console.print("\n⚠️ Tentando usar chave master admin...", style="yellow")
            auth_key = key_manager.get_master_key('admin')
        
        with console.status(f"[bold green]Criando chave {role}..."):
            new_key = api_client.create_api_key(
                role=role,
                is_active=True,
                description=description,
                auth_key=auth_key,
                save_to_file=True
            )
        
        if new_key:
            console.print(f"\n✅ Chave criada com sucesso!", style="bold green")
            console.print(f"   ID: [cyan]{new_key.key_id}[/cyan]")
            console.print(f"   Role: [cyan]{new_key.role}[/cyan]")
            console.print(f"\n💾 Chave salva em: [dim]keys/{new_key.role}_{new_key.key_id}_*.key[/dim]")
        else:
            console.print("\n❌ Falha ao criar chave", style="bold red")
    
    except Exception as e:
        console.print(f"\n❌ Erro ao criar chave: {e}", style="bold red")


def list_loaded_keys(key_manager: APIKeyManager):
    """Lista todas as chaves carregadas"""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Chaves Carregadas[/bold cyan]",
        border_style="cyan"
    ))
    
    keys = key_manager.list_loaded_keys()
    
    if not keys:
        console.print("\n⚠️ Nenhuma chave carregada", style="yellow")
        console.print("\n[dim]Use 'Recarregar Chaves' para carregar do diretório keys/[/dim]")
        return
    
    # Criar tabela
    table = Table(title="\n📋 Chaves Disponíveis", box=box.ROUNDED)
    table.add_column("Key ID", style="cyan")
    table.add_column("Role", style="magenta")
    table.add_column("Descrição", style="white")
    table.add_column("Status", style="green")
    table.add_column("Ativa", style="yellow")
    
    for key in keys:
        status = "✅ Ativa" if key['isActive'] else "⚠️ Inativa"
        is_current = "⭐ Sim" if key['isCurrent'] else ""
        
        table.add_row(
            key['keyId'],
            key['role'].upper(),
            key.get('description', '-'),
            status,
            is_current
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(keys)} chave(s)[/dim]")


def reload_keys(key_manager: APIKeyManager):
    """Recarrega chaves do diretório"""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Recarregar Chaves[/bold cyan]",
        border_style="cyan"
    ))
    
    with console.status("[bold green]Carregando chaves do diretório keys/..."):
        loaded_key = key_manager.autoload_keys()
    
    if loaded_key:
        console.print(f"\n✅ Chaves carregadas com sucesso!", style="bold green")
        console.print(f"   Chave ativa: [cyan]{loaded_key.key_id}[/cyan] ([magenta]{loaded_key.role}[/magenta])")
        
        # Mostrar todas as chaves carregadas
        all_keys = key_manager.list_loaded_keys()
        console.print(f"\n   Total carregado: [cyan]{len(all_keys)}[/cyan] chave(s)")
    else:
        console.print("\n⚠️ Nenhuma chave encontrada no diretório keys/", style="yellow")


def test_server_connection(api_client: CertificateAPIClient):
    """Testa conexão com o servidor"""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Testar Conexão com Servidor[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"\n🌐 Servidor: [cyan]{api_client.base_url}[/cyan]")
    console.print(f"   Modo: {'[yellow]DESENVOLVIMENTO (localhost)[/yellow]' if api_client.dev_mode else '[green]PRODUÇÃO[/green]'}")
    
    with console.status("[bold green]Testando conexão..."):
        connected = api_client.test_connection()
    
    if connected:
        console.print("\n✅ [bold green]Servidor acessível![/bold green]")
    else:
        console.print("\n❌ [bold red]Servidor não acessível[/bold red]")
        console.print("\n[dim]Verifique:")
        console.print("  • Conexão com a internet")
        console.print("  • URL do servidor")
        if api_client.dev_mode:
            console.print("[dim]  • Se o servidor local está rodando (netlify dev)[/dim]")


def api_settings(api_client: CertificateAPIClient):
    """Configurações da API"""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]Configurações da API[/bold cyan]",
        border_style="cyan"
    ))
    
    # Mostrar configurações atuais
    table = Table(title="\n⚙️ Configurações Atuais", box=box.ROUNDED)
    table.add_column("Configuração", style="cyan")
    table.add_column("Valor", style="white")
    
    table.add_row("URL Base", api_client.base_url)
    table.add_row("Modo", "Desenvolvimento (localhost)" if api_client.dev_mode else "Produção")
    table.add_row("Timeout", f"{api_client.timeout}s")
    table.add_row("Tentativas de Retry", str(api_client.retry_attempts))
    table.add_row("Diretório de Chaves", str(api_client.key_manager.keys_dir))
    
    console.print(table)
    
    try:
        from cli import quiet_select
    except ImportError:
        import questionary
        quiet_select = questionary.select
    
    choice = quiet_select(
        "\nO que deseja fazer?",
        choices=[
            "🔄 Alternar Modo (Dev/Prod)",
            "🔙 Voltar"
        ]
    )
    
    if choice == "🔄 Alternar Modo (Dev/Prod)":
        api_client.dev_mode = not api_client.dev_mode
        if api_client.dev_mode:
            api_client.base_url = "http://localhost:8888/.netlify/functions"
        else:
            api_client.base_url = "https://certificados.nepemufsc.com/.netlify/functions"
        
        console.print(f"\n✅ Modo alterado para: {'[yellow]DESENVOLVIMENTO[/yellow]' if api_client.dev_mode else '[green]PRODUÇÃO[/green]'}")
        console.print(f"   Nova URL: [cyan]{api_client.base_url}[/cyan]")
