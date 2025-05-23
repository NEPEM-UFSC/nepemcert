"""
NEPEM Certificados - Interface de Linha de Comando
Ferramenta para geração de certificados em lote.
"""

import os
import sys
import click
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
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

# Importação dos módulos da aplicação
from app.csv_manager import CSVManager
from app.template_manager import TemplateManager
from app.pdf_generator import PDFGenerator
from app.field_mapper import FieldMapper
from app.zip_exporter import ZipExporter
from app.connectivity_manager import ConnectivityManager
from app.parameter_manager import ParameterManager
from app.theme_manager import ThemeManager

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
    
    # Layout para as caixas de informação
    layout = Layout()
    layout.split_column(
        Layout(name="header"),
        Layout(name="info_boxes")
    )
    
    # Divisão para as caixas de informação lado a lado
    layout["info_boxes"].split_row(
        Layout(name="version"),
        Layout(name="connection")
    )
    
    # Conteúdo das caixas
    layout["version"].update(
        Panel(
            f"[bold]Versão:[/bold] {APP_VERSION}",
            title="Informações do Sistema",
            border_style="green"
        )
    )
    
    connection_status = check_connection_status()
    status_color = {
        "Conectado": "green",
        "Desconectado": "red",
        "Aguardando": "yellow"
    }.get(connection_status, "yellow")
    
    layout["connection"].update(
        Panel(
            f"[bold]Status:[/bold] [{status_color}]{connection_status}[/{status_color}]",
            title="Conexão com Servidor",
            border_style=status_color
        )
    )
    
    console.print(layout["info_boxes"])
    console.print("\n[bold cyan]Gerador de Certificados em Lote[/bold cyan]")
    console.print("[dim]Use os comandos abaixo para gerenciar seus certificados.[/dim]\n")


def main_menu():
    """Exibe o menu principal da aplicação."""
    print_header()
    
    choice = questionary.select(
        "Selecione uma opção:",
        choices=[
            "🔖 Gerar Certificados",
            "🎨 Gerenciar Templates",
            "⚙️ Configurações",
            "🔄 Sincronização e Conectividade",
            "❓ Ajuda",
            "🚪 Sair"
        ],
        use_indicator=True,
        style=questionary.Style([
            ('selected', 'bg:#0A1128 #ffffff'),
            ('instruction', 'fg:#0A1128'),
            ('pointer', 'fg:#0A1128'),
        ])
    ).ask()
    
    if choice == "🔖 Gerar Certificados":
        generate_certificates_menu()
    elif choice == "🎨 Gerenciar Templates":
        manage_templates_menu()
    elif choice == "⚙️ Configurações":
        settings_menu()
    elif choice == "🔄 Sincronização e Conectividade":
        connectivity_menu()
    elif choice == "❓ Ajuda":
        show_help()
    elif choice == "🚪 Sair":
        console.print("[bold green]Obrigado por usar o NEPEM Cert. Até logo![/bold green]")
        return False
    
    return True


def generate_certificates_menu():
    """Menu para geração de certificados."""
    console.clear()
    console.print("[bold blue]== Geração de Certificados ==[/bold blue]\n")
    
    choice = questionary.select(
        "O que você deseja fazer?",
        choices=[
            "📄 Gerar certificados em lote",
            "📋 Visualizar dados importados",
            "🔍 Testar geração com um único registro",
            "↩️ Voltar ao menu principal"
        ]
    ).ask()
    
    if choice == "📄 Gerar certificados em lote":
        generate_batch_certificates()
    elif choice == "📋 Visualizar dados importados":
        preview_imported_data()
    elif choice == "🔍 Testar geração com um único registro":
        test_certificate_generation()
    elif choice == "↩️ Voltar ao menu principal":
        return


def manage_templates_menu():
    """Menu para gerenciamento de templates."""
    console.clear()
    console.print("[bold blue]== Gerenciamento de Templates ==[/bold blue]\n")
    
    choice = questionary.select(
        "O que você deseja fazer?",
        choices=[
            "📝 Listar templates disponíveis",
            "➕ Importar novo template",
            "🖌️ Editar template existente",
            "🗑️ Excluir template",
            "👁️ Visualizar template",
            "↩️ Voltar ao menu principal"
        ]
    ).ask()
    
    if choice == "📝 Listar templates disponíveis":
        list_templates()
    elif choice == "➕ Importar novo template":
        import_template()
    elif choice == "🖌️ Editar template existente":
        edit_template()
    elif choice == "🗑️ Excluir template":
        delete_template()
    elif choice == "👁️ Visualizar template":
        preview_template()
    elif choice == "↩️ Voltar ao menu principal":
        return


def settings_menu():
    """Menu de configurações."""
    console.clear()
    console.print("[bold blue]== Configurações ==[/bold blue]\n")
    
    choice = questionary.select(
        "O que você deseja configurar?",
        choices=[
            "📁 Diretórios de trabalho",
            "🎨 Aparência e tema",
            "📊 Parâmetros de geração",
            "💾 Salvar/carregar presets",
            "↩️ Voltar ao menu principal"
        ]
    ).ask()
    
    if choice == "📁 Diretórios de trabalho":
        configure_directories()
    elif choice == "🎨 Aparência e tema":
        configure_appearance()
    elif choice == "📊 Parâmetros de geração":
        configure_generation_parameters()
    elif choice == "💾 Salvar/carregar presets":
        manage_presets()
    elif choice == "↩️ Voltar ao menu principal":
        return


def connectivity_menu():
    """Menu de conectividade e sincronização."""
    console.clear()
    console.print("[bold blue]== Sincronização e Conectividade ==[/bold blue]\n")
    
    choice = questionary.select(
        "O que você deseja fazer?",
        choices=[
            "🔄 Verificar status da conexão",
            "📡 Configurar servidor remoto",
            "⬆️ Enviar certificados para servidor",
            "⬇️ Baixar templates do servidor",
            "🔒 Configurar credenciais",
            "↩️ Voltar ao menu principal"
        ]
    ).ask()
    
    if choice == "🔄 Verificar status da conexão":
        check_connection()
    elif choice == "📡 Configurar servidor remoto":
        configure_remote_server()
    elif choice == "⬆️ Enviar certificados para servidor":
        upload_certificates()
    elif choice == "⬇️ Baixar templates do servidor":
        download_templates()
    elif choice == "🔒 Configurar credenciais":
        configure_credentials()
    elif choice == "↩️ Voltar ao menu principal":
        return


def show_help():
    """Exibe informações de ajuda."""
    console.clear()
    
    help_text = """
    # Ajuda do NEPEM Cert
    
    ## Como usar
    
    O NEPEM Cert é uma ferramenta para geração de certificados em lote. Você pode:
    
    1. **Gerar Certificados em Lote**:
       - Importe um CSV com os nomes dos participantes
       - Forneça detalhes do evento (nome, data, local, carga horária)
       - Selecione um template HTML
       - Gere os certificados com códigos de verificação únicos
    
    2. **Gerenciar Templates**:
       - Crie, edite e visualize templates HTML
       - Use placeholders para campos dinâmicos
    
    3. **Configurações**:
       - Defina diretórios de trabalho
       - Configure parâmetros de geração
    
    4. **Conectividade**:
       - Sincronize com servidor remoto
       - Importe/exporte templates e certificados
    
    ## Contato e Suporte
    
    Para mais informações ou suporte, entre em contato:
    - Email: contato@nepem.com
    - Site: www.nepem.com
    """
    
    md = Markdown(help_text)
    console.print(md)
    console.print("\n[dim]Pressione Enter para voltar ao menu principal...[/dim]")
    input()


# Função de geração de certificados implementada conforme o fluxo solicitado
def generate_batch_certificates():
    """Gera certificados em lote."""
    console.clear()
    console.print("[bold blue]== Geração de Certificados em Lote ==[/bold blue]\n")
    
    # Selecionar arquivo CSV
    csv_path = questionary.path(
        "Selecione o arquivo CSV com nomes dos participantes:",
        validate=lambda path: os.path.exists(path) and path.endswith('.csv')
    ).ask()
    
    if not csv_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Verificar se o CSV tem cabeçalho
    has_header = questionary.confirm("O arquivo CSV possui linha de cabeçalho?").ask()
    
    # Carregar dados do CSV
    with console.status("[bold green]Carregando dados do CSV..."):
        try:
            if has_header:
                df = pd.read_csv(csv_path)
            else:
                df = pd.read_csv(csv_path, header=None, names=["nome"])
            
            # Verificar se o CSV tem apenas uma coluna
            if len(df.columns) > 1:
                console.print("[bold red]Erro:[/bold red] O arquivo CSV deve conter apenas uma coluna com os nomes dos participantes.")
                console.print(f"Colunas encontradas: {', '.join(df.columns)}")
                return
            
            # Garantir que a coluna se chame "nome" para compatibilidade
            if df.columns[0] != "nome":
                df.columns = ["nome"]
            
            num_records = len(df)
            console.print(f"[green]✓[/green] Dados carregados com sucesso. {num_records} participantes encontrados.")
        except Exception as e:
            console.print(f"[bold red]Erro ao carregar CSV:[/bold red] {str(e)}")
            return
    
    # Solicitar informações do evento
    console.print("\n[bold]Informações do Evento[/bold]")
    evento = questionary.text("Nome do evento:").ask()
    data = questionary.text("Data do evento (ex: 15/05/2023):", default=datetime.now().strftime("%d/%m/%Y")).ask()
    local = questionary.text("Local do evento:").ask()
    carga_horaria = questionary.text("Carga horária (horas):").ask()
    
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
        choice = questionary.select(
            "Deseja modificar alguma informação?",
            choices=[
                "Não, continuar",
                "Modificar nome do evento",
                "Modificar data",
                "Modificar local",
                "Modificar carga horária",
                "Cancelar operação"
            ]
        ).ask()
        
        if choice == "Não, continuar":
            break
        elif choice == "Modificar nome do evento":
            evento = questionary.text("Nome do evento:", default=evento).ask()
        elif choice == "Modificar data":
            data = questionary.text("Data do evento:", default=data).ask()
        elif choice == "Modificar local":
            local = questionary.text("Local do evento:", default=local).ask()
        elif choice == "Modificar carga horária":
            carga_horaria = questionary.text("Carga horária (horas):", default=carga_horaria).ask()
        elif choice == "Cancelar operação":
            console.print("[yellow]Operação cancelada.[/yellow]")
            return
    
    # Selecionar template
    templates = template_manager.list_templates()
    if not templates:
        console.print("[yellow]Nenhum template disponível. Por favor, importe um template primeiro.[/yellow]")
        return
    
    template_name = questionary.select(
        "Selecione o template a ser utilizado:",
        choices=templates
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Selecionar tema
    themes = ["Nenhum"] + theme_manager.list_themes()
    selected_theme = questionary.select(
        "Selecione um tema para os certificados:",
        choices=themes
    ).ask()
    
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
        modify = questionary.confirm("Deseja modificar os parâmetros institucionais?").ask()
        
        if modify:
            for campo, valor in institutional_params.items():
                novo_valor = questionary.text(f"{campo}:", default=valor).ask()
                institutional_params[campo] = novo_valor
            
            # Atualizar parâmetros
            parameter_manager.update_institutional_placeholders(institutional_params)
            console.print("[green]✓[/green] Parâmetros institucionais atualizados.")
    else:
        console.print("[yellow]Nenhum parâmetro institucional configurado.[/yellow]")
      # Configurar diretório de saída
    output_dir = questionary.path(
        "Pasta de destino para os certificados:",
        default=pdf_generator.output_dir,
        only_directories=True
    ).ask()
    
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
    
    confirm = questionary.confirm("Deseja iniciar a geração dos certificados?").ask()
    
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
            
            # Gerar código de verificação único
            codigo = f"CERT-{participante_data['nome'].strip()[0:2].upper()}-{datetime.now().strftime('%Y')}-{index+1:03d}"
            participante_data["codigo_verificacao"] = codigo
            
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
                
                # Renderizar template com os dados
                html_content = template_manager.render_template(temp_name, final_data)
                
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
        generated_paths = pdf_generator.batch_generate(html_contents, file_names)
        console.print(f"[bold green]✓ {len(generated_paths)} certificados gerados com sucesso![/bold green]")
        
        # Oferecer opção para criar ZIP
        zip_option = questionary.confirm("Deseja empacotar os certificados em um arquivo ZIP?").ask()
        
        if zip_option:
            zip_name = questionary.text(
                "Nome do arquivo ZIP:",
                default=f"{evento.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.zip"
            ).ask()
            
            if not zip_name.endswith('.zip'):
                zip_name += '.zip'
                
            zip_path = os.path.join(output_dir, zip_name)
            
            # Criar arquivo ZIP
            with console.status("[bold green]Criando arquivo ZIP..."):
                zip_exporter.create_zip(generated_paths, zip_path)
            
            console.print(f"[bold green]✓ Arquivo ZIP criado em:[/bold green] {zip_path}")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao gerar certificados:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def preview_imported_data():
    """Visualiza dados importados de um CSV."""
    console.clear()
    console.print("[bold blue]== Visualização de Dados Importados ==[/bold blue]\n")
    
    # Selecionar arquivo CSV
    csv_path = questionary.path(
        "Selecione o arquivo CSV para visualizar:",
        validate=lambda path: os.path.exists(path) and path.endswith('.csv')
    ).ask()
    
    if not csv_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Verificar se o CSV tem cabeçalho
    has_header = questionary.confirm("O arquivo CSV possui linha de cabeçalho?").ask()
    
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
        
    template_name = questionary.select(
        "Selecione o template a ser utilizado:",
        choices=templates
    ).ask()
    
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
    
    for placeholder in placeholders:
        value = questionary.text(f"Valor para '{placeholder}':").ask()
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
                
                # Renderizar o template com os dados
                html_content = template_manager.render_template(temp_name, test_data)
                
                # Gerar PDF
                pdf_generator.generate_pdf(html_content, output_path)
            finally:
                # Limpar arquivo temporário
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        console.print(f"[bold green]✓ Certificado de teste gerado com sucesso![/bold green]")
        console.print(f"[bold]Caminho:[/bold] {output_path}")
        
        # Oferecer opção para abrir o PDF
        open_option = questionary.confirm("Deseja abrir o certificado gerado?").ask()
        
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
    template_path = questionary.path(
        "Selecione o arquivo HTML do template:",
        validate=lambda path: os.path.exists(path) and path.lower().endswith('.html')
    ).ask()
    
    if not template_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Solicitar nome para salvar o template
    template_name = questionary.text(
        "Nome para salvar o template:",
        default=os.path.basename(template_path)
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    if not template_name.lower().endswith('.html'):
        template_name += '.html'
    
    # Verificar se já existe um template com esse nome
    templates = template_manager.list_templates()
    if template_name in templates:
        overwrite = questionary.confirm(
            f"Já existe um template com o nome '{template_name}'. Deseja sobrescrever?"
        ).ask()
        
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
    template_name = questionary.select(
        "Selecione o template para editar:",
        choices=templates
    ).ask()
    
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
    open_option = questionary.confirm("Deseja abrir o template em um editor externo?").ask()
    
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
    template_name = questionary.select(
        "Selecione o template para excluir:",
        choices=templates
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Confirmar exclusão
    confirm = questionary.confirm(
        f"Tem certeza que deseja excluir o template '{template_name}'? Esta ação não pode ser desfeita."
    ).ask()
    
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
    template_name = questionary.select(
        "Selecione o template para visualizar:",
        choices=templates
    ).ask()
    
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
    preview_option = questionary.confirm("Deseja gerar uma prévia em PDF com dados de exemplo?").ask()
    
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
                    pdf_generator.generate_pdf(html_content, preview_path)
                finally:
                    # Limpar arquivo temporário
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            console.print(f"[bold green]✓ Prévia gerada com sucesso![/bold green]")
            console.print(f"[bold]Caminho:[/bold] {preview_path}")
            
            # Oferecer opção para abrir o PDF
            open_option = questionary.confirm("Deseja abrir a prévia em PDF?").ask()
            
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
    
    choice = questionary.select(
        "O que você deseja configurar?",
        choices=[
            "📝 Valores para campos institucionais",
            "🔤 Valores padrão para campos",
            "🖼️ Valores específicos para temas",
            "↩️ Voltar"
        ]
    ).ask()
    
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
    choice = questionary.select(
        "O que você deseja fazer?",
        choices=[
            "➕ Adicionar/editar campo",
            "🗑️ Remover campo",
            "↩️ Voltar"
        ]
    ).ask()
    
    if choice == "➕ Adicionar/editar campo":
        field = questionary.text("Nome do campo:").ask()
        if field:
            value = questionary.text(f"Valor para '{field}':").ask()
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
            
        field_to_remove = questionary.select(
            "Selecione o campo para remover:",
            choices=list(institutional.keys()) + ["Cancelar"]
        ).ask()
        
        if field_to_remove and field_to_remove != "Cancelar":
            confirm = questionary.confirm(f"Tem certeza que deseja remover '{field_to_remove}'?").ask()
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
    
    console.print(f"[bold]Status:[/bold] [{status_color}]{result['status']}[/{status_color}]")
    console.print(f"[bold]Mensagem:[/bold] {result['message']}")
    console.print(f"[bold]Horário:[/bold] {result['timestamp']}")
    
    if "server_url" in connectivity_manager.config and connectivity_manager.config["server_url"]:
        console.print(f"[bold]URL do servidor:[/bold] {connectivity_manager.config['server_url']}")
    else:
        console.print("[yellow]Servidor não configurado.[/yellow]")
    
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
