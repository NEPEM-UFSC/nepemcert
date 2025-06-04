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
from app.field_mapper import FieldMapper
from app.zip_exporter import ZipExporter
from app.connectivity_manager import ConnectivityManager
from app.parameter_manager import ParameterManager
from app.theme_manager import ThemeManager
from app.authentication_manager import AuthenticationManager

# Configuração do console Rich
console = Console()

# Versão do aplicativo
APP_VERSION = "1.1.0"

# Inicialização dos gerenciadores
csv_manager = CSVManager()
template_manager = TemplateManager()
pdf_generator = PDFGenerator()
field_mapper = FieldMapper()
zip_exporter = ZipExporter()
connectivity_manager = ConnectivityManager()
parameter_manager = ParameterManager()
theme_manager = ThemeManager()
auth_manager = AuthenticationManager()


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


def generate_certificates_menu():
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
                    console.print(f"[dim]Registro {i+1}: {row.to_dict()}[/dim]")
                
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

        except pd.errors.UnicodeDecodeError:
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
    
    # Carregar template
    with console.status("[bold green]Carregando template..."):
        template_content = template_manager.load_template(template_name)
        if not template_content:
            console.print(f"[bold red]Erro ao carregar template:[/bold red] Arquivo não encontrado.")
            return
        
        # Aplicar tema se selecionado
        if theme:
            theme_settings = theme_manager.load_theme(theme)
            if theme_settings:
                template_content = theme_manager.apply_theme_to_template(template_content, theme_settings)
                console.print(f"[green]✓[/green] Tema '{theme}' aplicado ao template.")
    
    # Mostrar e revisar parâmetros institucionais
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
    output_dir = quiet_path(
        "Pasta de destino para os certificados:",
        default=pdf_generator.output_dir,
        only_directories=True
    )
    
    if not output_dir:
        output_dir = pdf_generator.output_dir
    else:
        # Atualizar o diretório de saída do gerador de PDF
        pdf_generator.output_dir = output_dir
        # Garantir que o diretório exista
        os.makedirs(output_dir, exist_ok=True)
    
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
    
    # Gerar certificados
    html_contents = []
    file_names = []
    
    # Preparar informações comuns para todos os certificados
    common_data = {
        "evento": evento,
        "data": data,
        "local": local,
        "carga_horaria": carga_horaria,
    }
    
    # Extrair placeholders do template
    placeholders = template_manager.extract_placeholders(template_content)
    console.print(f"\n[bold]Placeholders encontrados no template:[/bold] {len(placeholders)}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False
    ) as progress:
        task = progress.add_task(f"[green]Gerando certificados...", total=num_records)
        
        for index, row in df.iterrows():
            progress.update(task, description=f"[green]Processando certificado {index+1}/{num_records}...")
              # Combinar dados do participante com as informações comuns
            participante_data = {"nome": row["nome"]}
            
            # Gerar código de autenticação único usando nosso gerenciador
            codigo_autenticacao = auth_manager.gerar_codigo_autenticacao(
                nome_participante=participante_data['nome'],
                evento=evento,
                data_evento=data
            )
            # NOTA: O código de verificação curto foi depreciado
            # Usamos o próprio código de autenticação como código de verificação
            codigo_verificacao = codigo_autenticacao
            
            # Salvar informações do certificado
            auth_manager.salvar_codigo(
                codigo_autenticacao=codigo_autenticacao,
                nome_participante=participante_data['nome'],
                evento=evento,
                data_evento=data,
                local_evento=local,
                carga_horaria=carga_horaria
            )            # Gerar URL para QR Code (se aplicável)
            qrcode_url = auth_manager.gerar_qrcode_data(codigo_autenticacao)
            url_base = "https://nepemufsc.com/verificar-certificados"
            
            # Adicionar códigos aos dados do participante
            participante_data["codigo_autenticacao"] = codigo_autenticacao
            participante_data["codigo_verificacao"] = codigo_verificacao
            participante_data["url_verificacao"] = url_base
            participante_data["url_qrcode"] = qrcode_url
            
            # Adicionar data de emissão
            participante_data["data_emissao"] = datetime.now().strftime("%d/%m/%Y")
            
            # Mesclar todos os dados
            csv_data = {**common_data, **participante_data}
            final_data = parameter_manager.merge_placeholders(csv_data, theme)
            
            # Gerar nome do arquivo
            file_name = f"certificado_{participante_data['nome'].strip().replace(' ', '_')}.pdf"
            file_path = os.path.join(output_dir, file_name)
            
            # Preparar template temporário para renderização
            temp_name = f"temp_{random.randint(1000, 9999)}.html"
            temp_path = os.path.join("templates", temp_name)
            
            try:
                # Salvar template temporário
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(template_content)
                
                # Gerar QR code adaptado ao tamanho do placeholder no template
                qr_info = auth_manager.gerar_qrcode_adaptado(codigo_autenticacao, template_content)
                final_data["qrcode_base64"] = qr_info["qrcode_base64"]
                
                # Renderizar template com os dados
                html_content = template_manager.render_template(temp_name, final_data)
                
                # Substituir o placeholder do QR code pelo QR code real
                html_content = auth_manager.substituir_qr_placeholder(html_content, qr_info["qrcode_base64"])
                
                # Adicionar à lista para geração em lote
                html_contents.append(html_content)
                file_names.append(file_path)
            except Exception as e:
                console.print(f"[bold red]Erro ao processar certificado {index+1}:[/bold red] {str(e)}")
            finally:
                # Limpar arquivo temporário
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            progress.update(task, advance=1)
    
    # Gerar PDFs em lote
    console.print("\n[bold]Gerando arquivos PDF...[/bold]")
    
    try:        
        generated_paths = pdf_generator.batch_generate(html_contents, file_names, orientation='landscape')
        console.print(f"[bold green]✓ {len(generated_paths)} certificados gerados com sucesso![/bold green]")
        
        # Oferecer opção para criar ZIP
        zip_option = quiet_confirm("Deseja empacotar os certificados em um arquivo ZIP?")
        
        if zip_option:
            zip_name = quiet_text(
                "Nome do arquivo ZIP:",
                default=f"{evento.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.zip"
            )
            
            if not zip_name.endswith('.zip'):
                zip_name += '.zip'
                
            zip_path = os.path.join(output_dir, zip_name)
            
            # Criar arquivo ZIP
            with console.status("[bold green]Criando arquivo ZIP..."):
                zip_exporter.create_zip(generated_paths, zip_path)
            
            console.print(f"[bold green]✓ Arquivo ZIP criado em:[/bold green] {zip_path}")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao gerar certificados:[/bold red] {str(e)}")
        console.print(f"[bold yellow]Tipo de erro:[/bold yellow] {type(e).__name__}")
        
        # Informações de diagnóstico
        console.print("\n[bold]Informações de diagnóstico:[/bold]")
        console.print(f"- Arquivo CSV: {csv_path}")
        console.print(f"- Template: {template_name}")
        console.print(f"- Tema aplicado: {selected_theme}")
        console.print(f"- Número de participantes: {num_records}")
        console.print(f"- Diretório de saída: {output_dir}")
        
        # Exibir stack trace para referência técnica
        console.print("\n[dim]Stack trace para diagnóstico técnico:[/dim]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def preview_imported_data():
    """Visualiza dados importados de um CSV."""
    console.clear()
    console.print("[bold blue]== Visualização de Dados Importados ==[/bold blue]\n")
    
    # Selecionar arquivo CSV
    csv_path = quiet_path(
        "Selecione o arquivo CSV para visualizar:",
        validate=lambda path: os.path.exists(path) and path.endswith('.csv')
    )
    
    if not csv_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Verificar se o CSV tem cabeçalho
    has_header = quiet_confirm("O arquivo CSV possui linha de cabeçalho?")
    
    # Carregar e mostrar dados
    try:
        df = pd.read_csv(csv_path, header=0 if has_header else None)
        
        # Se não há cabeçalho, atribuir um nome à coluna
        if not has_header:
            df.columns = ["nome"]
        
        # Criar tabela Rich
        table = Table(title=f"Dados do arquivo: {os.path.basename(csv_path)}")
        
        # Adicionar colunas
        for col in df.columns:
            table.add_column(col, style="cyan")
        
        # Adicionar linhas (limitando a 10 registros para visualização)
        for _, row in df.head(10).iterrows():
            table.add_row(*[str(val) for val in row.values])
        
        console.print(table)
        
        # Informações adicionais
        console.print(f"\n[bold]Total de registros:[/bold] {len(df)}")
        console.print(f"[bold]Colunas disponíveis:[/bold] {', '.join(df.columns.tolist())}")
        
        # Verificar valores ausentes
        missing = df.isnull().sum()
        if missing.any():
            console.print("\n[yellow]Aviso: O arquivo contém valores ausentes nas seguintes colunas:[/yellow]")
            for col, count in missing[missing > 0].items():
                console.print(f"- {col}: {count} valores ausentes")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao processar o arquivo:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def test_certificate_generation():
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
    
    # Carregar template
    template_content = template_manager.load_template(template_name)
    if not template_content:
        console.print(f"[bold red]Erro ao carregar template:[/bold red] Arquivo não encontrado.")
        input("\nPressione Enter para voltar...")
        return
    
    # Identificar placeholders
    placeholders = template_manager.extract_placeholders(template_content)
    
    if not placeholders:
        console.print("[yellow]Aviso: Não foram encontrados placeholders no template.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
      # Solicitar valores para os placeholders
    test_data = {}
    console.print("[bold]Informe os valores para os campos:[/bold]\n")
    
    # Solicitar informações principais primeiro
    nome = quiet_text("Nome do participante:")
    evento = quiet_text("Nome do evento:")
    data = quiet_text("Data do evento (ex: 15/05/2025):", default=datetime.now().strftime("%d/%m/%Y"))
    local = quiet_text("Local do evento:")
    carga_horaria = quiet_text("Carga horária (horas):")
      # Gerar código de autenticação para o teste
    codigo_autenticacao = auth_manager.gerar_codigo_autenticacao(
        nome_participante=nome,
        evento=evento,
        data_evento=data
    )    # O código de verificação curto foi depreciado, usando o próprio código de autenticação completo
    codigo_verificacao = codigo_autenticacao
    
    url_base = "https://nepemufsc.com/verificar-certificados"
    qrcode_url = auth_manager.gerar_qrcode_data(codigo_autenticacao)
    
    # Salvar informações do certificado de teste
    auth_manager.salvar_codigo(
        codigo_autenticacao=codigo_autenticacao,
        nome_participante=nome,
        evento=evento,
        data_evento=data,
        local_evento=local,
        carga_horaria=carga_horaria
    )
    
    # Adicionar valores principais e códigos ao dicionário de dados
    test_data["nome"] = nome
    test_data["evento"] = evento
    test_data["data"] = data
    test_data["local"] = local
    test_data["carga_horaria"] = carga_horaria    
    test_data["codigo_autenticacao"] = codigo_autenticacao
    test_data["codigo_verificacao"] = codigo_verificacao
    test_data["url_verificacao"] = url_base
    test_data["url_qrcode"] = qrcode_url
    test_data["data_emissao"] = datetime.now().strftime("%d/%m/%Y")
    
    # Solicitar valores para os demais placeholders que não foram preenchidos
    outros_placeholders = [p for p in placeholders if p not in test_data]
    for placeholder in outros_placeholders:
        value = quiet_text(f"Valor para '{placeholder}':")
        test_data[placeholder] = value
    
    # Gerar PDF de teste
    output_path = os.path.join(pdf_generator.output_dir, "certificado_teste.pdf")
    
    try:
        with console.status("[bold green]Gerando certificado de teste..."):
            # Gerar HTML com os valores substituídos usando o template_manager
            temp_name = f"temp_test_{random.randint(1000, 9999)}.html"
            temp_path = os.path.join("templates", temp_name)
            
            try:
                # Salvar template temporário
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(template_content)
                  # Gerar QR code adaptado ao tamanho do placeholder no template
                qr_info = auth_manager.gerar_qrcode_adaptado(codigo_autenticacao, template_content)
                test_data["qrcode_base64"] = qr_info["qrcode_base64"]
                
                # Renderizar o template com os dados
                html_content = template_manager.render_template(temp_name, test_data)
                
                # Substituir o placeholder do QR code pelo QR code real
                html_content = auth_manager.substituir_qr_placeholder(html_content, qr_info["qrcode_base64"])
                
                # Gerar PDF
                pdf_generator.generate_pdf(html_content, output_path, orientation='landscape')
            finally:
                # Limpar arquivo temporário
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        console.print(f"[bold green]✓ Certificado de teste gerado com sucesso![/bold green]")
        console.print(f"[bold]Caminho:[/bold] {output_path}")
        
        # Oferecer opção para abrir o PDF
        open_option = quiet_confirm("Deseja abrir o certificado gerado?")
        
        if open_option:
            import subprocess
            try:
                os.startfile(output_path)  # Windows
            except AttributeError:
                try:
                    subprocess.call(["open", output_path])  # macOS
                except:
                    subprocess.call(["xdg-open", output_path])  # Linux
    
    except Exception as e:
        console.print(f"[bold red]Erro ao gerar certificado de teste:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


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
        preview_path = os.path.join(pdf_generator.output_dir, "preview_template.pdf")
        
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
    console.print("[yellow]Função ainda não implementada.[/yellow]")
    input("\nPressione Enter para voltar...")


def configure_appearance():
    """Configura aparência e tema."""
    console.print("[yellow]Função ainda não implementada.[/yellow]")
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
    console.print("[yellow]Função ainda não implementada completamente.[/yellow]")
    input("\nPressione Enter para voltar...")


def configure_theme_placeholders():
    """Configura valores para temas."""
    # Implementação básica
    console.print("[yellow]Função ainda não implementada completamente.[/yellow]")
    input("\nPressione Enter para voltar...")


def manage_presets():
    """Gerencia presets de configuração."""
    console.print("[yellow]Função ainda não implementada.[/yellow]")
    input("\nPressione Enter para voltar...")


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
    """Configura servidor remoto."""
    # Implementação básica
    console.print("[yellow]Função ainda não implementada completamente.[/yellow]")
    input("\nPressione Enter para voltar...")


def upload_certificates():
    """Envia certificados para o servidor remoto."""
    # Implementação básica
    console.print("[yellow]Função ainda não implementada completamente.[/yellow]")
    input("\nPressione Enter para voltar...")


def download_templates():
    """Baixa templates do servidor remoto."""
    # Implementação básica
    console.print("[yellow]Função ainda não implementada completamente.[/yellow]")
    input("\nPressione Enter para voltar...")


def configure_credentials():
    """Configura credenciais de acesso ao servidor."""
    # Implementação básica
    console.print("[yellow]Função ainda não implementada completamente.[/yellow]")
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

def debug_compare_themes():
    """Ferramenta de debug para comparar temas usando dados de exemplo."""
    console.clear()
    console.print("[bold blue]== DEBUG: Comparação de Temas ==[/bold blue]\n")
    console.print("[yellow]Esta ferramenta gera certificados com TODOS os temas disponíveis usando dados de exemplo.[/yellow]")
    console.print("[yellow]Útil para debug e comparação visual dos temas.[/yellow]\n")
    
    # Listar templates disponíveis
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[red]❌ Nenhum template disponível.[/red]")
        console.print("Importe um template primeiro antes de usar esta ferramenta.")
        input("\nPressione Enter para voltar...")
        return
    
    # Selecionar template
    template_name = quiet_select(
        "Selecione o template para usar:",
        choices=templates,
        style=get_menu_style()
    )
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar template
    template_content = template_manager.load_template(template_name)
    if not template_content:
        console.print(f"[red]❌ Erro ao carregar template: {template_name}[/red]")
        return
      # Gerar código de autenticação para exemplos de temas
    nome_exemplo = "João da Silva Santos"
    evento_exemplo = "Workshop de Tecnologia e Inovação"
    data_exemplo = "15 a 17 de maio de 2025"
    
    # Gerar código de autenticação para o exemplo    
    codigo_autenticacao_exemplo = auth_manager.gerar_codigo_autenticacao(
        nome_participante=nome_exemplo,
        evento=evento_exemplo,
        data_evento=data_exemplo
    )
    # Usa o próprio código de autenticação como código de verificação
    codigo_verificacao_exemplo = codigo_autenticacao_exemplo
    # Gera a URL base para verificação (sem o código)
    url_verificacao_exemplo = "https://nepemufsc.com/verificar-certificados"
    # Gera a URL completa para o QR code (com o código como parâmetro)
    qrcode_url_exemplo = auth_manager.gerar_qrcode_data(codigo_autenticacao_exemplo)
    
    # Dados de exemplo fixos para todos os certificados
    sample_data = {
        "nome": nome_exemplo,
        "evento": evento_exemplo,
        "local": "Campus Universitário - Sala de Conferências",
        "data": data_exemplo,
        "carga_horaria": "20",
        "coordenador": "Prof. Dr. Maria Fernanda Costa",
        "diretor": "Prof. Dr. Roberto Andrade Lima",
        "cidade": "Florianópolis",        "data_emissao": "29 de maio de 2025",
        "codigo_autenticacao": codigo_autenticacao_exemplo,
        "codigo_verificacao": codigo_verificacao_exemplo,
        "url_verificacao": url_verificacao_exemplo,
        "url_qrcode": qrcode_url_exemplo,
        "intro_text": "Certificamos que",
        "participation_text": "participou com êxito do",
        "location_text": "realizado em",
        "date_text": "no período de",
        "workload_text": "com carga horária total de",
        "hours_text": "horas",
        "coordinator_title": "Coordenador do Evento",
        "director_title": "Diretor da Instituição",
        "title_text": "CERTIFICADO DE PARTICIPAÇÃO"
    }
    
    # Salvar informações do certificado de exemplo
    auth_manager.salvar_codigo(
        codigo_autenticacao=codigo_autenticacao_exemplo,
        nome_participante=nome_exemplo,
        evento=evento_exemplo,
        data_evento=data_exemplo,
        local_evento=sample_data["local"],
        carga_horaria=sample_data["carga_horaria"]
    )
    
    # Listar temas disponíveis
    available_themes = theme_manager.list_themes()
    
    if not available_themes:
        console.print("[red]❌ Nenhum tema disponível.[/red]")
        input("\nPressione Enter para voltar...")
        return
    
    console.print(f"\n[green]✓ Template carregado: {template_name}[/green]")
    console.print(f"[green]✓ Temas encontrados: {len(available_themes)}[/green]")
    console.print(f"[cyan]Temas: {', '.join(available_themes)}[/cyan]\n")
    
    # Confirmar geração
    confirm = quiet_confirm(
        f"Deseja gerar {len(available_themes)} certificados (um para cada tema)?",
        default=True
    )
    
    if not confirm:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Criar diretório de saída específico para debug
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_output_dir = os.path.join("output", f"debug_themes_{timestamp}")
    os.makedirs(debug_output_dir, exist_ok=True)
    
    console.print(f"\n[blue]📁 Diretório de saída: {debug_output_dir}[/blue]\n")
    
    # Gerar certificados para cada tema
    generated_files = []
    
    with console.status("[bold green]Gerando certificados com diferentes temas...") as status:
        for i, theme_name in enumerate(available_themes, 1):
            try:
                status.update(f"[bold green]Processando tema {i}/{len(available_themes)}: {theme_name}")
                
                # Carregar configurações do tema
                theme_settings = theme_manager.load_theme(theme_name)
                
                if not theme_settings:
                    console.print(f"[yellow]⚠️ Aviso: Tema '{theme_name}' não pôde ser carregado[/yellow]")
                    continue
                
                # Mesclar dados de exemplo com configurações do tema
                merged_data = parameter_manager.merge_placeholders(sample_data.copy(), theme_name)
                
                # Renderizar template com dados
                try:
                    # Salvar template temporariamente
                    temp_template_name = f"temp_debug_{theme_name.replace(' ', '_').lower()}_{timestamp}.html"
                    temp_template_path = os.path.join("templates", temp_template_name)
                    
                    with open(temp_template_path, "w", encoding="utf-8") as f:
                        f.write(template_content)
                      # Gerar QR code adaptado ao tamanho do placeholder no template
                    qr_info = auth_manager.gerar_qrcode_adaptado(codigo_autenticacao_exemplo, template_content)
                    merged_data["qrcode_base64"] = qr_info["qrcode_base64"]
                    
                    # Renderizar template
                    html_content = template_manager.render_template(temp_template_name, merged_data)
                    
                    # Substituir o placeholder do QR code pelo QR code real
                    html_content = auth_manager.substituir_qr_placeholder(html_content, qr_info["qrcode_base64"])
                    
                    # Aplicar tema ao HTML
                    if theme_settings:
                        html_content = theme_manager.apply_theme_to_template(html_content, theme_settings)
                    
                    # Gerar nome do arquivo
                    safe_theme_name = theme_name.replace(" ", "_").replace("ã", "a").replace("é", "e").replace("ô", "o")
                    pdf_filename = f"certificado_tema_{safe_theme_name}.pdf"
                    pdf_path = os.path.join(debug_output_dir, pdf_filename)
                    
                    # Gerar PDF
                    pdf_generator.generate_pdf(html_content, pdf_path, orientation='landscape')
                    generated_files.append((pdf_path, theme_name))
                    
                    console.print(f"[green]✓[/green] {theme_name} → {pdf_filename}")
                    
                except Exception as e:
                    console.print(f"[red]❌ Erro no tema '{theme_name}': {str(e)}[/red]")
                    
                finally:
                    # Limpar arquivo temporário
                    if 'temp_template_path' in locals() and os.path.exists(temp_template_path):
                        os.remove(temp_template_path)
                        
            except Exception as e:
                console.print(f"[red]❌ Erro geral no tema '{theme_name}': {str(e)}[/red")
    
    # Relatório final
    console.print(f"\n[bold green]🎉 Geração concluída![/bold green]")
    console.print(f"[green]✓[/green] Versão do aplicativo: {APP_VERSION}")
    console.print(f"[{'green' if templates else 'yellow'}]{'✓' if templates else '⚠️'}[/{'green' if templates else 'yellow'}] Templates: {len(templates) if templates else 0}")
    console.print(f"[{'green' if themes else 'yellow'}]{'✓' if themes else '⚠️'}[/{'green' if themes else 'yellow'}] Temas: {len(themes) if themes else 0}")
    
    if generated_files:
        # Mostrar lista dos arquivos gerados
        console.print("[bold]Arquivos gerados:[/bold]")
        for pdf_path, theme_name in generated_files:
            filename = os.path.basename(pdf_path)
            console.print(f"  • [cyan]{filename}[/cyan] ({theme_name})")
        
        # Oferecer opções adicionais
        console.print("\n[bold]Opções adicionais:[/bold]")
        
        action = quiet_select(
            "O que deseja fazer agora?",
            choices=[
                "📁 Abrir diretório de saída",
                "📊 Criar arquivo ZIP com todos os certificados",
                "👁️ Abrir primeiro certificado",
                "↩️ Voltar ao menu"
            ],
            style=get_menu_style()
        )
        
        if action == "📁 Abrir diretório de saída":
            try:
                import subprocess
                os.startfile(debug_output_dir)  # Windows
            except AttributeError:
                try:
                    subprocess.call(["open", debug_output_dir])  # macOS
                except:
                    subprocess.call(["xdg-open", debug_output_dir])  # Linux
            console.print("[green]✓ Diretório aberto[/green]")
            
        elif action == "📊 Criar arquivo ZIP com todos os certificados":
            zip_filename = f"debug_temas_{timestamp}.zip"
            zip_path = os.path.join(debug_output_dir, zip_filename)
            
            try:
                with console.status("[bold green]Criando arquivo ZIP..."):
                    zip_exporter.create_zip([pdf_path for pdf_path, _ in generated_files], zip_path)
                console.print(f"[green]✓ ZIP criado: {zip_filename}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Erro ao criar ZIP: {str(e)}[/red]")
                
        elif action == "👁️ Abrir primeiro certificado":
            if generated_files:
                first_pdf = generated_files[0][0]
                try:
                    import subprocess
                    os.startfile(first_pdf)  # Windows
                except AttributeError:
                    try:
                        subprocess.call(["open", first_pdf])  # macOS
                    except:
                        subprocess.call(["xdg-open", first_pdf])  # Linux
                console.print("[green]✓ Certificado aberto[/green]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()

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


def debug_system_check():
    """Função de debug para verificar o sistema."""
    console.clear()
    console.print("[bold red]== DEBUG: Verificação do Sistema ==[/bold red]\n")
    
    console.print("[yellow]Esta ferramenta verifica o estado geral do sistema NEPEM Cert.[/yellow]\n")
    
    # Verificar diretórios essenciais
    console.print("[bold]📁 Verificando diretórios essenciais...[/bold]")
    
    directories = {
        "Templates": "templates",
        "Output": "output", 
        "Config": "config",
        "App": "app"
    }
    
    for name, path in directories.items():
        if os.path.exists(path):
            console.print(f"[green]✓[/green] {name}: {path}")
        else:
            console.print(f"[red]❌[/red] {name}: {path} [red](não encontrado)[/red]")
            try:
                os.makedirs(path, exist_ok=True)
                console.print(f"[yellow]  → Diretório criado automaticamente[/yellow]")
            except Exception as e:
                console.print(f"[red]  → Erro ao criar: {str(e)}[/red]")
    
    # Verificar templates disponíveis
    console.print(f"\n[bold]📄 Verificando templates...[/bold]")
    templates = template_manager.list_templates()
    if templates:
        console.print(f"[green]✓[/green] {len(templates)} template(s) encontrado(s):")
        for template in templates[:5]:  # Mostrar apenas os primeiros 5
            console.print(f"[dim]  • {template}[/dim]")
        if len(templates) > 5:
            console.print(f"[dim]  ... e mais {len(templates) - 5} template(s)[/dim]")
    else:
        console.print("[yellow]⚠️[/yellow] Nenhum template encontrado")
    
    # Verificar temas disponíveis
    console.print(f"\n[bold]🎨 Verificando temas...[/bold]")
    themes = theme_manager.list_themes()
    if themes:
        console.print(f"[green]✓[/green] {len(themes)} tema(s) encontrado(s):")
        for theme in themes:
            console.print(f"[dim]  • {theme}[/dim]")
    else:
        console.print("[yellow]⚠️[/yellow] Nenhum tema encontrado")
    
    # Verificar configurações de parâmetros
    console.print(f"\n[bold]⚙️ Verificando configurações...[/bold]")
    try:
        institutional = parameter_manager.get_institutional_placeholders()
        defaults = parameter_manager.get_default_placeholders()
        
        console.print(f"[green]✓[/green] Parâmetros institucionais: {len(institutional)} configurado(s)")
        console.print(f"[green]✓[/green] Parâmetros padrão: {len(defaults)} configurado(s)")
        
        # Verificar arquivo de configuração
        config_path = parameter_manager.config_file
        if os.path.exists(config_path):
            size = os.path.getsize(config_path)
            console.print(f"[green]✓[/green] Arquivo de configuração: {config_path} ({size} bytes)")
        else:
            console.print(f"[yellow]⚠️[/yellow] Arquivo de configuração não encontrado: {config_path}")
            
    except Exception as e:
        console.print(f"[red]❌[/red] Erro ao verificar configurações: {str(e)}")
    
    # Verificar conectividade
    console.print(f"\n[bold]🌐 Verificando conectividade...[/bold]")
    try:
        conn_info = connectivity_manager.get_connection_status()
        status_color = {
            "Conectado": "green",
            "Desconectado": "red", 
            "Aguardando": "yellow"
        }.get(conn_info["status"], "yellow")
        
        console.print(f"[{status_color}]●[/{status_color}] Status: {conn_info['status']}")
        if "last_check" in conn_info:
            console.print(f"[dim]  Última verificação: {conn_info['last_check']}[/dim]")
            
    except Exception as e:
        console.print(f"[red]❌[/red] Erro ao verificar conectividade: {str(e)}")
    
    # Verificar dependências do sistema
    console.print(f"\n[bold]📦 Verificando dependências...[/bold]")
    
    dependencies = [
        ("pandas", "Processamento de CSV"),
        ("rich", "Interface de usuário"),
        ("questionary", "Menus interativos"),
        ("jinja2", "Templates"),
        ("xhtml2pdf", "Geração de PDF"),
        ("qrcode", "Códigos QR"),
        ("PIL", "Processamento de imagens")
    ]
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            console.print(f"[green]✓[/green] {module_name}: {description}")
        except ImportError:
            console.print(f"[red]❌[/red] {module_name}: {description} [red](não encontrado)[/red]")
    
    # Informações do sistema
    console.print(f"\n[bold]💻 Informações do sistema...[/bold]")
    import platform
    console.print(f"[cyan]Python:[/cyan] {platform.python_version()}")
    console.print(f"[cyan]Sistema:[/cyan] {platform.system()} {platform.release()}")
    console.print(f"[cyan]Arquitetura:[/cyan] {platform.machine()}")
    
    # Resumo final
    console.print(f"\n[bold blue]📊 Resumo da verificação:[/bold blue]")
    console.print(f"[green]✓[/green] Sistema operacional: {platform.system()}")
    console.print(f"[green]✓[/green] Versão do aplicativo: {APP_VERSION}")
    console.print(f"[{'green' if templates else 'yellow'}]{'✓' if templates else '⚠️'}[/{'green' if templates else 'yellow'}] Templates: {len(templates) if templates else 0}")
    console.print(f"[{'green' if themes else 'yellow'}]{'✓' if themes else '⚠️'}[/{'green' if themes else 'yellow'}] Temas: {len(themes) if themes else 0}")
    
    console.print("\n[dim]Esta verificação ajuda a identificar problemas de configuração e dependências.[/dim]")
    console.print("[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


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
        test_certificate_generation()
    elif choice == "📊 Visualizar dados CSV":
        preview_imported_data()
    elif choice == "↩️ Voltar ao menu principal":
        return
    
    # Retornar ao menu de templates após cada operação
    manage_templates_menu()


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
    
    choice = quiet_select(
        "O que você deseja fazer?",
        choices=[
            "🔄 Verificar conexão",
            "⚙️ Configurar servidor",
            "📤 Sincronizar dados",
            "📋 Histórico de sincronização",
            "↩️ Voltar ao menu principal"
        ],
        style=get_menu_style()
    )
    
    if choice == "🔄 Verificar conexão":
        with console.status("[bold green]Verificando conexão..."):
            result = connectivity_manager.test_connection()
        
        if result["success"]:
            console.print("[bold green]✓ Conexão bem-sucedida![/bold green]")
        else:
            console.print(f"[bold red]✗ Falha na conexão:[/bold red] {result.get('error', 'Erro desconhecido')}")
        
        input("\nPressione Enter para continuar...")
        connectivity_menu()
    
    elif choice == "⚙️ Configurar servidor":
        console.print("[yellow]Função ainda não implementada.[/yellow]")
        input("\nPressione Enter para voltar...")
        connectivity_menu()
    
    elif choice == "📤 Sincronizar dados":
        console.print("[yellow]Função ainda não implementada.[/yellow]")
        input("\nPressione Enter para voltar...")
        connectivity_menu()
    
    elif choice == "📋 Histórico de sincronização":
        console.print("[yellow]Função ainda não implementada.[/yellow]")
        input("\nPressione Enter para voltar...")
        connectivity_menu()
    
    elif choice == "↩️ Voltar ao menu principal":
        return


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

[bold cyan]Suporte:[/bold cyan]
• Versão atual: v1.1.0
• Para problemas técnicos, ative o modo DEBUG nas configurações
• Templates de exemplo estão disponíveis na pasta 'templates'
"""
    
    console.print(help_content)
    
    input("\n[dim]Pressione Enter para voltar ao menu principal...[/dim]")
