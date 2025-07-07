import os
import sys
from datetime import datetime
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box
import questionary
from contextlib import redirect_stderr
from io import StringIO

# Importações dos módulos da aplicação
from app.template_manager import TemplateManager
from app.theme_manager import ThemeManager
from app.parameter_manager import ParameterManager
from app.connectivity_manager import ConnectivityManager
from app.cert_auth_manager import CertAuthenticationManager
from app.zip_exporter import ZipExporter
from app.certificate_service import CertificateService

# Inicializar console e componentes
console = Console()
template_manager = TemplateManager()
theme_manager = ThemeManager()
parameter_manager = ParameterManager()
connectivity_manager = ConnectivityManager()
auth_manager = CertAuthenticationManager()
zip_exporter = ZipExporter()
certificate_service = CertificateService()

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

def generate_certificates_batch():
    """Menu para geração de certificados."""
    console.clear()
    console.print("[bold blue]== Geração de Certificados em Lote ==[/bold blue]\n")
    # Selecionar arquivo CSV
    csv_path = quiet_path(
        "Selecione o arquivo CSV com nomes dos participantes:",
        validate=lambda path: os.path.exists(path) and path.endswith('.csv')
    )
    
    if not csv_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    # Verificar se o CSV tem cabeçalho
    has_header = quiet_confirm("O arquivo CSV possui linha de cabeçalho?")

    with console.status("[bold green]Carregando dados do CSV..."):
        try:
            console.print(f"[dim]Tentando carregar CSV de: {csv_path}[/dim]")
            console.print(f"[dim]Arquivo com cabeçalho? {has_header}[/dim]")
            
            try:                # Tentativa com diferentes separadores caso o padrão falhe
                separators = [',', ';', '\t', '|']
                encoding_options = ['utf-8', 'latin1', 'cp1252']
                
                success = False
                
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
                    console.print("[bold red]Erro:[/bold red] Não foi possível ler o arquivo CSV em nenhum formato reconhecido.")
                    console.print("[dim]Dica: Verifique se o arquivo está no formato CSV correto.[/dim]")
                    return
                
                if has_header and "nome" not in df.columns and len(df.columns) > 1:
                    console.print("[bold red]Erro:[/bold red] O arquivo CSV com cabeçalho deve conter uma coluna chamada 'nome'.")
                    console.print(f"Colunas encontradas: {', '.join(df.columns)}")
                    console.print("[dim]Dica: Se o arquivo possui apenas nomes, selecione 'Não' na opção de cabeçalho[/dim]")
                    return
                
                # Mostrar os primeiros registros para debug
                console.print("[dim]Primeiros registros carregados:[/dim]")
                for i, row in df.head(2).iterrows():
                    console.print(f"[dim]Registro {i+1}: {row.to_dict()}[/dim]") #type: ignore
                
                # Verificar se o arquivo tem mais informações além do nome, caso tenha apenas os nomes
                if len(df.columns) > 1:
                    console.print("[yellow]Aviso: O arquivo CSV contém múltiplas colunas.[/yellow]")
                    console.print(f"Colunas encontradas: {', '.join(df.columns)}")
                    console.print("[yellow]O sistema utilizará apenas a coluna 'nome'.[/yellow]")
                    
                    # Garantir que temos a coluna "nome"
                    if "nome" not in df.columns:
                        console.print("[bold red]Erro:[/bold red] Não foi encontrada uma coluna 'nome' no arquivo.")
                        console.print("[dim]Colunas disponíveis:[/dim]")
                        for i, col in enumerate(df.columns):
                            console.print(f"[dim]  {i+1}. {col}[/dim]")
                        return
                
            except pd.errors.EmptyDataError:
                console.print("[bold red]Erro:[/bold red] O arquivo CSV está vazio.")
                return
            except pd.errors.ParserError as e:
                console.print(f"[bold red]Erro de formatação no CSV:[/bold red] {str(e)}")
                console.print("[dim]Dica: Verifique se o arquivo está no formato CSV correto, sem erros de sintaxe.[/dim]")
                return
              # Verificar valores nulos
            if df["nome"].isna().any():
                null_count = df["nome"].isna().sum()
                console.print(f"[yellow]Aviso: Existem {null_count} valores vazios na coluna 'nome'.[/yellow]")
                console.print("[dim]Estes registros serão ignorados ou podem gerar certificados com nomes em branco.[/dim]")
            
            # Remover valores nulos para contagem correta
            df = df.dropna(subset=["nome"])
            
            num_records = len(df)
            
            if num_records == 0:
                console.print("[bold red]Erro:[/bold red] Não foram encontrados participantes válidos no arquivo.")
                return
            
            console.print(f"[green]✓[/green] Dados carregados com sucesso. {num_records} participantes encontrados.")
            
            # Exibir uma prévia dos nomes carregados
            preview_limit = min(5, num_records)
            console.print(f"\n[bold]Prévia dos primeiros {preview_limit} participantes:[/bold]")
            for i, nome in enumerate(df["nome"].head(preview_limit)):
                console.print(f"  {i+1}. {nome}")

        except UnicodeDecodeError:
            console.print("[bold red]Erro de codificação:[/bold red] O arquivo não está em formato UTF-8.")
            console.print("[dim]Dica: Salve seu arquivo CSV com codificação UTF-8.[/dim]")
            return
        except FileNotFoundError:
            console.print(f"[bold red]Erro:[/bold red] O arquivo {csv_path} não foi encontrado.")
            return
        except PermissionError:
            console.print("[bold red]Erro de permissão:[/bold red] Não foi possível acessar o arquivo.")
            console.print("[dim]Dica: Verifique se o arquivo está sendo usado por outro programa.[/dim]")
            return
        except Exception as e:
            console.print(f"[bold red]Erro ao carregar CSV:[/bold red] {str(e)}")
            console.print(f"[bold yellow]Tipo de erro:[/bold yellow] {type(e).__name__}")
            console.print("[dim]Stack trace para referência:[/dim]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return
    
    # Solicitar informações do evento
    console.print("\n[bold]Informações do Evento[/bold]")
    evento = quiet_text("Nome do evento:")
    data = quiet_text("Data do evento (ex: 15/05/2023):", default=datetime.now().strftime("%d/%m/%Y"))
    local = quiet_text("Local do evento:")
    carga_horaria = quiet_text("Carga horária (horas):")
    
    # Revisar informações
    while True:
        console.clear()
        console.print("[bold blue]== Revisão das Informações do Evento ==[/bold blue]\n")
        
        table = Table(box=box.SIMPLE)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")
        
        table.add_row("Nome do evento", evento)
        table.add_row("Data", data)
        table.add_row("Local", local)
        table.add_row("Carga horária", f"{carga_horaria} horas")
        table.add_row("Número de participantes", str(num_records))
        
        console.print(table)
        
        # Perguntar se deseja modificar algo
        choice = quiet_select(
            "Deseja modificar alguma informação?",
            choices=[
                "Não, continuar",
                "Modificar nome do evento",
                "Modificar data",
                "Modificar local",
                "Modificar carga horária",
                "Cancelar operação"
            ],
            style=get_menu_style()
        )
        
        if choice == "Não, continuar":
            break
        elif choice == "Modificar nome do evento":
            evento = quiet_text("Nome do evento:", default=evento)
        elif choice == "Modificar data":
            data = quiet_text("Data do evento:", default=data)
        elif choice == "Modificar local":
            local = quiet_text("Local do evento:", default=local)
        elif choice == "Modificar carga horária":
            carga_horaria = quiet_text("Carga horária (horas):", default=carga_horaria)
        elif choice == "Cancelar operação":
            console.print("[yellow]Operação cancelada.[/yellow]")
            return
    
    # Selecionar template
    templates = template_manager.list_templates()
    if not templates:
        console.print("[yellow]Nenhum template disponível. Por favor, importe um template primeiro.[/yellow]")
        return
    template_name = quiet_select(
        "Selecione o template a ser utilizado:",
        choices=templates,
        style=get_menu_style()
    )
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Selecionar tema
    themes = ["Nenhum"] + theme_manager.list_themes()
    selected_theme = quiet_select(
        "Selecione um tema para os certificados:",
        choices=themes,
        style=get_menu_style()
    )
    
    theme = None if selected_theme == "Nenhum" else selected_theme
    
    # Mostrar e revisar parâmetros institucionais
    # This section is kept for user review, but actual loading/applying of template and theme is done by the service.
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
      # Configurar diretório de saída
    output_dir_input = quiet_path(
        "Pasta de destino para os certificados:",
        default=certificate_service.output_dir, # Use service's default
        only_directories=True
    )

    output_dir = output_dir_input if output_dir_input else certificate_service.output_dir

    # Update the service's output directory and its pdf_generator's output_dir
    certificate_service.output_dir = output_dir
    certificate_service.pdf_generator.output_dir = output_dir
    os.makedirs(output_dir, exist_ok=True) # Ensure directory exists
    
    # Confirmação final
    console.print("\n[bold]Resumo da operação:[/bold]")
    console.print(f"- Evento: [cyan]{evento}[/cyan]")
    console.print(f"- Data: [cyan]{data}[/cyan]")
    console.print(f"- Local: [cyan]{local}[/cyan]")
    console.print(f"- Carga horária: [cyan]{carga_horaria} horas[/cyan]")
    console.print(f"- Participantes: [cyan]{num_records}[/cyan]")
    console.print(f"- Template: [cyan]{template_name}[/cyan]")
    console.print(f"- Tema: [cyan]{selected_theme}[/cyan]")
    console.print(f"- Destino: [cyan]{output_dir}[/cyan]")
    
    confirm = quiet_confirm("Deseja iniciar a geração dos certificados?")
    
    if not confirm:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Preparar informações do evento
    event_data = {
        "evento": evento,
        "data": data,
        "local": local,
        "carga_horaria": carga_horaria,
    }

    # Verificar conexão antes de iniciar a geração
    connection_info = connectivity_manager.check_connection()
    if connection_info["status"] == "Desconectado":
        console.print(
            "[bold yellow]AVISO:[/] Você está offline. Os certificados serão gerados localmente, "
            "mas serão considerados inválidos até que sejam sincronizados com o servidor. "
            "Por favor, conecte-se à internet e sincronize os certificados posteriormente."
        )

    # Chamar o serviço de geração de certificados
    console.print("\n[bold]Iniciando geração de certificados com o serviço...[/bold]")
    with console.status("[bold green]Processando certificados..."):
        generation_result = certificate_service.generate_certificates_batch(
            csv_file_path=csv_path,
            event_details=event_data,
            template_name=template_name,
            theme_name=theme, # theme can be None or the selected theme name
            has_header=has_header
        )

    # Exibir resultados
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

    # Oferecer opção para criar ZIP
    if generation_result["generated_files"]:
        zip_option = quiet_confirm("Deseja empacotar os certificados gerados em um arquivo ZIP?")
        if zip_option:
            zip_name_default = f"{evento.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.zip"
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
    elif not generation_result["errors"] and generation_result["success_count"] == 0 : # No files generated and no specific errors reported by service yet
        console.print("[yellow]Nenhum certificado foi gerado. Verifique as configurações e o arquivo CSV.[/yellow]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()

def generate_certificates_menu():
    console.clear()
    console.print("[bold blue]== Menu de Geração de Certificados ==[/bold blue]\n")
    opcao = quiet_select(
        "Como deseja gerar certificados?",
        choices=[
            "Geração em lote (arquivo CSV)",
            "Geração de um único certificado",
            "Voltar ao menu anterior"
        ],
        style=get_menu_style()
    )

    if opcao == "Geração em lote (arquivo CSV)":
        generate_certificates_batch()
    elif opcao == "Geração de um único certificado":
        generate_certificate_single()
    else:
        return


def generate_certificate_single():
    """Testa a geração de um certificado único."""
    console.clear()
    console.print("[bold blue]== Teste de Geração de Certificado ==[/bold blue]\n")
    
    # Selecionar template
    templates = template_manager.list_templates()
    if not templates:
        console.print("[yellow]Nenhum template disponível. Por favor, importe um template primeiro.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
    template_name = quiet_select(
        "Selecione o template a ser utilizado:",
        choices=templates,
        style=get_menu_style()
    )
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Solicitar informações do participante e evento
    console.print("[bold]Informações do Participante e Evento:[/bold]\n")
    
    nome = quiet_text("Nome do participante:")
    if not nome:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    evento = quiet_text("Nome do evento:")
    data = quiet_text("Data do evento (ex: 15/05/2025):", default=datetime.now().strftime("%d/%m/%Y"))
    local = quiet_text("Local do evento:")
    carga_horaria = quiet_text("Carga horária (horas):")
    
    # Selecionar tema
    themes = ["Nenhum"] + theme_manager.list_themes()
    selected_theme = quiet_select(
        "Selecione um tema para o certificado:",
        choices=themes,
        style=get_menu_style()
    )
    
    theme = None if selected_theme == "Nenhum" else selected_theme
    
    # Preparar dados do evento
    event_data = {
        "evento": evento,
        "data": data,
        "local": local,
        "carga_horaria": carga_horaria
    }
    
    # Gerar certificado usando o serviço
    try:
        with console.status("[bold green]Gerando certificado de teste..."):
            result = certificate_service.generate_single_certificate(
                participant_name=nome,
                event_details=event_data,
                template_name=template_name,
                theme_name=theme
            )
        
        if result["success"]:
            console.print(f"[bold green]✓ Certificado de teste gerado com sucesso![/bold green]")
            console.print(f"[bold]Caminho:[/bold] {result['generated_file']}")
            
            # Oferecer opção para abrir o PDF
            open_option = quiet_confirm("Deseja abrir o certificado gerado?")
            
            if open_option:
                import subprocess
                try:
                    os.startfile(result['generated_file'])  # Windows
                except AttributeError:
                    try:
                        subprocess.call(["open", result['generated_file']])  # macOS
                    except:
                        subprocess.call(["xdg-open", result['generated_file']])  # Linux
        else:
            console.print(f"[bold red]Erro ao gerar certificado:[/bold red] {result['error']}")
    
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()
