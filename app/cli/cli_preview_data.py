import os
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary
from contextlib import redirect_stderr
from io import StringIO
import sys

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