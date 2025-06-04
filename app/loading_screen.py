#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NEPEM Certificados - Tela de carregamento
Fornece uma tela de carregamento falsa para ocultar mensagens verbosas do sistema.
"""

import time
import random
import os
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.align import Align
from pyfiglet import Figlet

console = Console()

# Controle para garantir que a tela de carregamento seja exibida apenas uma vez
_loading_already_shown = False

def loading_already_shown():
    """
    Verifica se a tela de carregamento já foi exibida.
    
    Returns:
        bool: True se a tela já foi exibida, False caso contrário.
    """
    global _loading_already_shown
    return _loading_already_shown

def loading_dummy(duration=4.0, refresh_rate=0.04, force=False):
    """
    Exibe uma tela de carregamento falsa que limpa a tela constantemente.
    
    Args:
        duration (float): Duração em segundos da tela de carregamento
        refresh_rate (float): Taxa de atualização da tela em segundos (padrão: 0.04 = 25fps)
            Valores menores resultam em mais atualizações por segundo.
            Use valores entre 0.01-0.05 para ocultar eficientemente mensagens verbosas.
        force (bool): Se True, força a exibição mesmo se já tiver sido mostrada antes
    """
    global _loading_already_shown
    
    # Se a tela de carregamento já foi exibida e não estamos forçando, não fazer nada
    if _loading_already_shown and not force:
        return
    
    tasks = [
        "Inicializando componentes...",
        "Carregando gerenciadores de sistema...",
        "Verificando dependências...",
        "Configurando ambiente...",
        "Otimizando performance...",
        "Carregando interface...",
        "Verificando conectividade...",
        "Preparando recursos...",
        "Configurando renderização...",
        "Inicializando NEPEMCERT..."
    ]
    
    random_steps = [random.randint(3, 8) for _ in range(len(tasks))]
    start_time = time.time()
    total_tasks = sum(random_steps)
    completed_tasks = 0
    task_index = 0
    current_step = 0
    
    # Configurações do spinners e mensagens aleatórias
    spinners = ["dots", "dots2", "dots3", "dots4", "dots5", "dots6", "dots7", "dots8", "dots9", "dots10", "dots11", "dots12"]
    tips = [
        "Dica: Use 'CTRL+C' para interromper operações longas",
        "Dica: Templates HTML podem ser personalizados",
        "Dica: É possível exportar múltiplos certificados em ZIP",
        "Dica: QR Codes são gerados automaticamente para verificação",
        "Dica: Testes de geração ajudam a evitar erros em lotes grandes",
        "Dica: Você pode salvar conjuntos de configurações como presets",
        "Dica: Múltiplos temas estão disponíveis para seus certificados"
    ]

    # Loop principal da tela de carregamento
    while time.time() - start_time < duration:
        # Limpar a tela constantemente (mais de 20x por segundo)
        console.clear()
        
        # Escolher um spinner aleatório periodicamente
        if random.random() < 0.1:  # 10% de chance de mudar o spinner
            current_spinner = random.choice(spinners)
        else:
            current_spinner = "dots"
        
        # Exibir cabeçalho
        f = Figlet(font="slant")
        ascii_art = f.renderText("NEPEM Cert")
        console.print(ascii_art, style="bold blue")
        console.print(Align.center("[bold cyan]Carregando Sistema[/bold cyan]"))
        
        # Exibir barra de progresso geral
        with Progress(
            SpinnerColumn(spinner_name=current_spinner),
            TextColumn("[bold blue]Inicializando...[/bold blue]"),
            BarColumn(bar_width=None, complete_style="green", finished_style="bold green"),
            TaskProgressColumn(),
            expand=True
        ) as progress:
            main_task = progress.add_task("", total=100)
            overall_percent = min(100, int((time.time() - start_time) / duration * 100))
            progress.update(main_task, completed=overall_percent)
        
        # Mostrar tarefas sendo executadas
        if task_index < len(tasks):
            panel = Panel(
                f"[bold green]{tasks[task_index]}[/bold green]",
                title="Operação atual",
                border_style="green"
            )
            console.print(panel)
            
            current_step += random.uniform(0.2, 0.5)  # Avançar em passos aleatórios
            if current_step >= random_steps[task_index]:
                current_step = 0
                task_index += 1
                completed_tasks += random_steps[task_index-1] if task_index > 0 else 0
        
        # Mostrar dica aleatória no rodapé
        tip = random.choice(tips)
        console.print(f"\n[dim]{tip}[/dim]")
        
        # Calcular porcentagem completa na barra de progresso
        percent_complete = min(100, int((completed_tasks / total_tasks) * 100))
        console.print(f"[bold]{percent_complete}% completo[/bold]")
          # Pausar por um curto período para limitar a frequência de atualizações
        time.sleep(refresh_rate)  # Taxa de atualização configurável, padrão ~25 fps
    
    console.clear()
    for i in range(3):
        console.clear()
        console.print("\n\n")
        console.print(Align.center("[bold green]Sistema inicializado com sucesso![/bold green]"))
        time.sleep(0.2)
    
    # Marcar que a tela de carregamento foi exibida
    _loading_already_shown = True

if __name__ == "__main__":
    loading_dummy()
