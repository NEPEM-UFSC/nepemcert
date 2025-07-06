"""
Utilitários compartilhados para interfaces CLI
Funções reutilizáveis para evitar duplicação de código
"""

import os
import sys
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box
import questionary
from contextlib import redirect_stderr
from io import StringIO

# Inicializar console
console = Console()

# Wrapper functions para questionary
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

def load_and_validate_csv(csv_path, has_header=True):
    """
    Carrega e valida arquivo CSV com tratamento de erros.
    
    Args:
        csv_path (str): Caminho para o arquivo CSV
        has_header (bool): Se o arquivo tem cabeçalho
    
    Returns:
        tuple: (dataframe, success, error_message)
    """
    try:
        console.print(f"[dim]Tentando carregar CSV de: {csv_path}[/dim]")
        console.print(f"[dim]Arquivo com cabeçalho? {has_header}[/dim]")
        
        # Tentativa com diferentes separadores caso o padrão falhe
        separators = [',', ';', '\t', '|']
        encoding_options = ['utf-8', 'latin1', 'cp1252']
        
        success = False
        df = None
        
        for encoding in encoding_options:
            for sep in separators:
                try:
                    console.print(f"[dim]Tentando ler CSV com separador '{sep}' e encoding '{encoding}'...[/dim]")
                    
                    if has_header:
                        console.print("[dim]Lendo CSV com cabeçalho...[/dim]")
                        df = pd.read_csv(csv_path, sep=sep, encoding=encoding)
                        console.print(f"[dim]Colunas encontradas: {', '.join(df.columns)}[/dim]")
                        
                        # Se o arquivo tem cabeçalho, verificamos se existe a coluna "nome"
                        if "nome" not in df.columns:
                            console.print("[dim]Coluna 'nome' não encontrada no cabeçalho[/dim]")
                            # Se não tiver a coluna nome, mas tiver apenas 1 coluna, renomear para "nome"
                            if len(df.columns) == 1:
                                console.print(f"[dim]Renomeando coluna única '{df.columns[0]}' para 'nome'[/dim]")
                                df.columns = ["nome"]
                                success = True
                                break
                        else:
                            success = True
                            break
                    else:
                        console.print("[dim]Lendo CSV sem cabeçalho, considerando primeira coluna como 'nome'...[/dim]")
                        # Se não tem cabeçalho, lê considerando que a primeira coluna é "nome"
                        df = pd.read_csv(csv_path, header=None, names=["nome"], sep=sep, encoding=encoding)
                        console.print(f"[dim]Dados carregados. Formato da tabela: {df.shape} (linhas x colunas)[/dim]")
                        success = True
                        break
                except Exception as e:
                    console.print(f"[dim]Tentativa com separador '{sep}' e encoding '{encoding}' falhou: {str(e)}[/dim]")
            
            if success:
                break
        
        if not success:
            return None, False, "Não foi possível ler o arquivo CSV em nenhum formato reconhecido."
        
        if has_header and "nome" not in df.columns and len(df.columns) > 1:
            return None, False, f"O arquivo CSV com cabeçalho deve conter uma coluna chamada 'nome'. Colunas encontradas: {', '.join(df.columns)}"
        
        # Mostrar os primeiros registros para debug
        console.print("[dim]Primeiros registros carregados:[/dim]")
        if df is not None:
            for i, row in df.head(2).iterrows():
                console.print(f"[dim]Registro {i+1}: {row.to_dict()}[/dim]")
        
        # Verificar se o arquivo tem mais informações além do nome
        if df is not None and len(df.columns) > 1:
            console.print("[yellow]Aviso: O arquivo CSV contém múltiplas colunas.[/yellow]")
            console.print(f"Colunas encontradas: {', '.join(df.columns)}")
            console.print("[yellow]O sistema utilizará apenas a coluna 'nome'.[/yellow]")
            
            # Garantir que temos a coluna "nome"
            if "nome" not in df.columns:
                return None, False, "Não foi encontrada uma coluna 'nome' no arquivo."
        
        # Verificar valores nulos
        if df["nome"].isna().any():
            null_count = df["nome"].isna().sum()
            console.print(f"[yellow]Aviso: Existem {null_count} valores vazios na coluna 'nome'.[/yellow]")
            console.print("[dim]Estes registros serão ignorados.[/dim]")
        
        # Remover valores nulos
        if df is not None:
            df = df.dropna(subset=["nome"])
        
        if df is None or len(df) == 0:
            return None, False, "Não foram encontrados participantes válidos no arquivo."
        
        console.print(f"[green]✓[/green] Dados carregados com sucesso. {len(df)} participantes encontrados.")
        
        # Exibir uma prévia dos nomes carregados
        preview_limit = min(5, len(df))
        console.print(f"\n[bold]Prévia dos primeiros {preview_limit} participantes:[/bold]")
        for i, nome in enumerate(df["nome"].head(preview_limit)):
            console.print(f"  {i+1}. {nome}")
        
        return df, True, None
    
    except pd.errors.EmptyDataError:
        return None, False, "O arquivo CSV está vazio."
    except pd.errors.ParserError as e:
        return None, False, f"Erro de formatação no CSV: {str(e)}"
    except UnicodeDecodeError:
        return None, False, "Erro de codificação: O arquivo não está em formato UTF-8."
    except FileNotFoundError:
        return None, False, f"O arquivo {csv_path} não foi encontrado."
    except PermissionError:
        return None, False, "Erro de permissão: Não foi possível acessar o arquivo."
    except Exception as e:
        return None, False, f"Erro inesperado ao carregar CSV: {str(e)}"

def collect_event_data():
    """
    Coleta informações do evento do usuário.
    
    Returns:
        dict: Dados do evento
    """
    console.print("\n[bold]Informações do Evento[/bold]")
    evento = quiet_text("Nome do evento:")
    data = quiet_text("Data do evento (ex: 15/05/2023):", default=datetime.now().strftime("%d/%m/%Y"))
    local = quiet_text("Local do evento:")
    carga_horaria = quiet_text("Carga horária (horas):")
    
    return {
        "evento": evento,
        "data": data,
        "local": local,
        "carga_horaria": carga_horaria
    }

def review_event_data(event_data, num_participants=None):
    """
    Permite ao usuário revisar e editar os dados do evento.
    
    Args:
        event_data (dict): Dados do evento
        num_participants (int): Número de participantes (opcional)
    
    Returns:
        dict: Dados do evento atualizados ou None se cancelado
    """
    while True:
        console.clear()
        console.print("[bold blue]== Revisão das Informações do Evento ==[/bold blue]\n")
        
        table = Table(box=box.SIMPLE)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")
        
        table.add_row("Nome do evento", event_data["evento"])
        table.add_row("Data", event_data["data"])
        table.add_row("Local", event_data["local"])
        table.add_row("Carga horária", f"{event_data['carga_horaria']} horas")
        
        if num_participants:
            table.add_row("Número de participantes", str(num_participants))
        
        console.print(table)
        
        # Perguntar se deseja modificar algo
        choices = [
            "Não, continuar",
            "Modificar nome do evento",
            "Modificar data",
            "Modificar local",
            "Modificar carga horária",
            "Cancelar operação"
        ]
        
        choice = quiet_select(
            "Deseja modificar alguma informação?",
            choices=choices,
            style=get_menu_style()
        )
        
        if choice == "Não, continuar":
            return event_data
        elif choice == "Modificar nome do evento":
            event_data["evento"] = quiet_text("Nome do evento:", default=event_data["evento"])
        elif choice == "Modificar data":
            event_data["data"] = quiet_text("Data do evento:", default=event_data["data"])
        elif choice == "Modificar local":
            event_data["local"] = quiet_text("Local do evento:", default=event_data["local"])
        elif choice == "Modificar carga horária":
            event_data["carga_horaria"] = quiet_text("Carga horária (horas):", default=event_data["carga_horaria"])
        elif choice == "Cancelar operação":
            return None

def select_template(template_manager):
    """
    Permite ao usuário selecionar um template.
    
    Args:
        template_manager: Instância do TemplateManager
    
    Returns:
        str: Nome do template selecionado ou None se cancelado
    """
    templates = template_manager.list_templates()
    if not templates:
        console.print("[yellow]Nenhum template disponível. Por favor, importe um template primeiro.[/yellow]")
        return None
    
    template_name = quiet_select(
        "Selecione o template a ser utilizado:",
        choices=templates,
        style=get_menu_style()
    )
    
    return template_name

def select_theme(theme_manager):
    """
    Permite ao usuário selecionar um tema.
    
    Args:
        theme_manager: Instância do ThemeManager
    
    Returns:
        str: Nome do tema selecionado ou None se nenhum tema
    """
    themes = ["Nenhum"] + theme_manager.list_themes()
    selected_theme = quiet_select(
        "Selecione um tema para os certificados:",
        choices=themes,
        style=get_menu_style()
    )
    
    return None if selected_theme == "Nenhum" else selected_theme

def review_institutional_parameters(parameter_manager):
    """
    Mostra e permite modificar parâmetros institucionais.
    
    Args:
        parameter_manager: Instância do ParameterManager
    
    Returns:
        bool: True se continuou, False se cancelou
    """
    institutional_params = parameter_manager.get_institutional_placeholders()
    
    console.print("\n[bold]Parâmetros Institucionais[/bold]")
    if institutional_params:
        table = Table(box=box.SIMPLE)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")
        
        for campo, valor in institutional_params.items():
            table.add_row(campo, valor)
        
        console.print(table)
        
        # Perguntar se deseja modificar os parâmetros
        modify = quiet_confirm("Deseja modificar os parâmetros institucionais?")
        
        if modify:
            for campo, valor in institutional_params.items():
                novo_valor = quiet_text(f"{campo}:", default=valor)
                institutional_params[campo] = novo_valor
            
            # Atualizar parâmetros
            parameter_manager.update_institutional_placeholders(institutional_params)
            console.print("[green]✓[/green] Parâmetros institucionais atualizados.")
    else:
        console.print("[yellow]Nenhum parâmetro institucional configurado.[/yellow]")
    
    return True

def configure_output_directory(certificate_service):
    """
    Configura o diretório de saída para os certificados.
    
    Args:
        certificate_service: Instância do CertificateService
    
    Returns:
        str: Caminho do diretório de saída
    """
    output_dir_input = quiet_path(
        "Pasta de destino para os certificados:",
        default=certificate_service.output_dir,
        only_directories=True
    )

    output_dir = output_dir_input if output_dir_input else certificate_service.output_dir

    # Atualizar o diretório de saída do serviço
    certificate_service.output_dir = output_dir
    certificate_service.pdf_generator.output_dir = output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def display_generation_summary(event_data, num_participants, template_name, theme_name, output_dir):
    """
    Exibe resumo da operação de geração.
    
    Args:
        event_data (dict): Dados do evento
        num_participants (int): Número de participantes
        template_name (str): Nome do template
        theme_name (str): Nome do tema
        output_dir (str): Diretório de saída
    
    Returns:
        bool: True se confirmou, False se cancelou
    """
    console.print("\n[bold]Resumo da operação:[/bold]")
    console.print(f"- Evento: [cyan]{event_data['evento']}[/cyan]")
    console.print(f"- Data: [cyan]{event_data['data']}[/cyan]")
    console.print(f"- Local: [cyan]{event_data['local']}[/cyan]")
    console.print(f"- Carga horária: [cyan]{event_data['carga_horaria']} horas[/cyan]")
    
    if num_participants:
        console.print(f"- Participantes: [cyan]{num_participants}[/cyan]")
    
    console.print(f"- Template: [cyan]{template_name}[/cyan]")
    console.print(f"- Tema: [cyan]{theme_name or 'Nenhum'}[/cyan]")
    console.print(f"- Destino: [cyan]{output_dir}[/cyan]")
    
    return quiet_confirm("Deseja iniciar a geração dos certificados?")

def display_generation_results(generation_result):
    """
    Exibe os resultados da geração de certificados.
    
    Args:
        generation_result (dict): Resultado da geração
    """
    console.print("\n[bold blue]== Resultados da Geração ==[/bold blue]")
    
    if generation_result["success_count"] > 0:
        console.print(f"[bold green]✓ {generation_result['success_count']} certificados gerados com sucesso![/bold green]")
        for file_path in generation_result["generated_files"]:
            console.print(f"  [green]•[/green] {file_path}")
    
    if generation_result["failed_count"] > 0:
        console.print(f"[bold red]✗ {generation_result['failed_count']} certificados falharam ao gerar.[/bold red]")

    if generation_result["errors"]:
        console.print("\n[bold yellow]Erros e Avisos:[/bold yellow]")
        for error_msg in generation_result["errors"]:
            console.print(f"  [yellow]•[/yellow] {error_msg}")

def offer_zip_creation(generation_result, event_data, output_dir, zip_exporter):
    """
    Oferece opção para criar arquivo ZIP com os certificados gerados.
    
    Args:
        generation_result (dict): Resultado da geração
        event_data (dict): Dados do evento
        output_dir (str): Diretório de saída
        zip_exporter: Instância do ZipExporter
    """
    if not generation_result["generated_files"]:
        return
    
    zip_option = quiet_confirm("Deseja empacotar os certificados gerados em um arquivo ZIP?")
    if not zip_option:
        return
    
    zip_name_default = f"{event_data['evento'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.zip"
    zip_name = quiet_text(
        "Nome do arquivo ZIP:",
        default=zip_name_default
    )
    
    if not zip_name.endswith('.zip'):
        zip_name += '.zip'
    
    zip_path = os.path.join(output_dir, zip_name)
    
    with console.status("[bold green]Criando arquivo ZIP..."):
        try:
            zip_exporter.create_zip(generation_result["generated_files"], zip_path)
            console.print(f"[bold green]✓ Arquivo ZIP criado em:[/bold green] {zip_path}")
        except Exception as e_zip:
            console.print(f"[bold red]Erro ao criar arquivo ZIP:[/bold red] {str(e_zip)}")

def offer_pdf_open(pdf_path):
    """
    Oferece opção para abrir um arquivo PDF gerado.
    
    Args:
        pdf_path (str): Caminho para o arquivo PDF
    """
    open_option = quiet_confirm("Deseja abrir o certificado gerado?")
    
    if open_option:
        import subprocess
        try:
            os.startfile(pdf_path)  # Windows
        except AttributeError:
            try:
                subprocess.call(["open", pdf_path])  # macOS
            except:
                subprocess.call(["xdg-open", pdf_path])  # Linux

def check_connectivity_and_warn(connectivity_manager):
    """
    Verifica conexão e exibe aviso se offline.
    
    Args:
        connectivity_manager: Instância do ConnectivityManager
    """
    connection_info = connectivity_manager.check_connection()
    if connection_info["status"] == "Desconectado":
        console.print(
            "[bold yellow]AVISO:[/] Você está offline. Os certificados serão gerados localmente, "
            "mas serão considerados inválidos até que sejam sincronizados com o servidor. "
            "Por favor, conecte-se à internet e sincronize os certificados posteriormente."
        )

def prepare_template_for_service(template_path, template_manager, console):
    """
    Prepara um template para uso pelo serviço de certificados.
    
    Args:
        template_path (str): Caminho para o template
        template_manager: Instância do TemplateManager
        console: Console para mensagens
    
    Returns:
        tuple: (template_file_name, original_template_in_managed_dir)
    """
    template_file_name = os.path.basename(template_path)
    managed_template_path = os.path.join(template_manager.templates_dir, template_file_name)
    
    try:
        # Verificar se o template já está no diretório gerenciado
        if os.path.abspath(template_path) == os.path.abspath(managed_template_path):
            original_template_in_managed_dir = True
            console.print(f"[dim]Template '{template_file_name}' já está no diretório gerenciado.[/dim]")
        else:
            with open(template_path, 'r', encoding='utf-8') as f:
                original_template_content = f.read()
            # Salvar no diretório gerenciado
            template_manager.save_template(template_file_name, original_template_content)
            original_template_in_managed_dir = False
            console.print(f"[green]✓[/green] Template '{template_file_name}' preparado para o serviço.")
        
        return template_file_name, original_template_in_managed_dir
        
    except Exception as e:
        console.print(f"[bold red]Erro ao preparar template '{template_path}': [/bold red]{str(e)}")
        return None, False

def cleanup_temporary_template(template_file_name, original_template_in_managed_dir, template_manager, console):
    """
    Limpa template temporário se foi copiado.
    
    Args:
        template_file_name (str): Nome do arquivo do template
        original_template_in_managed_dir (bool): Se o template original estava no diretório gerenciado
        template_manager: Instância do TemplateManager
        console: Console para mensagens
    """
    if not original_template_in_managed_dir:
        managed_template_path = os.path.join(template_manager.templates_dir, template_file_name)
        if os.path.exists(managed_template_path):
            try:
                os.remove(managed_template_path)
                console.print(f"[dim]Template temporário '{template_file_name}' limpo.[/dim]")
            except Exception as e:
                console.print(f"[yellow]Aviso: Não foi possível limpar o template temporário: {str(e)}[/yellow]")
