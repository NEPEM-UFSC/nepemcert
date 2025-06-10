"""
Módulo para geração de PDFs a partir de HTML usando WeasyPrint.
Fornece funcionalidades para converter templates HTML renderizados em certificados PDF.
"""

import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import weasyprint

def _execute_generate_pdf_task(args):
    """
    Função auxiliar para executar a geração de PDF em processo separado.
    Esta função deve estar no escopo do módulo para ser serializável.
    
    Args:
        args: Tupla contendo (html_content, output_path, orientation)
    
    Returns:
        str: Caminho do arquivo PDF gerado em caso de sucesso
        
    Raises:
        Exception: Em caso de erro na geração
    """
    html_content, output_path, orientation = args
    
    try:
        # Configurar CSS para orientação apenas se não já definido
        css_string = f"""
        @page {{
            size: A4 {orientation};
        }}
        """
        
        # Gerar PDF
        html_doc = weasyprint.HTML(string=html_content)
        
        # Aplicar CSS apenas se necessário
        stylesheets = []
        if not '@page' in html_content:
            css_doc = weasyprint.CSS(string=css_string)
            stylesheets.append(css_doc)
        
        html_doc.write_pdf(output_path, stylesheets=stylesheets)
        
        return output_path
        
    except Exception as e:
        raise Exception(f"Erro ao gerar PDF {output_path}: {str(e)}")

class PDFGenerator:
    """Classe responsável pela geração de PDFs a partir de conteúdo HTML."""
    
    def __init__(self, output_dir="output"):
        """
        Inicializa o gerador de PDF.
        
        Args:
            output_dir (str): Diretório onde os PDFs serão salvos
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Garante que o diretório de saída existe."""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_pdf(self, html_content, output_path=None, orientation="portrait"):
        """
        Gera um PDF a partir de conteúdo HTML.
        
        Args:
            html_content (str): Conteúdo HTML para converter
            output_path (str, optional): Caminho completo para salvar o PDF
            orientation (str): Orientação da página ('portrait' ou 'landscape')
        
        Returns:
            bytes ou str: Bytes do PDF se output_path não fornecido, senão caminho do arquivo
        
        Raises:
            RuntimeError: Se houver erro na geração do PDF
        """
        try:
            # Configurar CSS para orientação (sem sobrescrever margin se já definido)
            css_string = f"""
            @page {{
                size: A4 {orientation};
            }}
            """
            
            # Criar documento HTML e CSS
            html_doc = weasyprint.HTML(string=html_content)
            
            # Aplicar CSS apenas se necessário (não sobrescrever estilos do template)
            stylesheets = []
            if not '@page' in html_content:
                css_doc = weasyprint.CSS(string=css_string)
                stylesheets.append(css_doc)
            
            if output_path:
                # Garantir que o diretório pai existe
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                html_doc.write_pdf(output_path, stylesheets=stylesheets)
                return output_path
            else:
                # Gerar PDF em memória
                return html_doc.write_pdf(stylesheets=stylesheets)
                
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar PDF: {str(e)}")
    
    def batch_generate(self, html_contents, file_names, orientation="portrait", use_multiprocessing=False, max_workers=None):
        """
        Gera múltiplos PDFs em lote.
        
        Args:
            html_contents (list): Lista de conteúdos HTML
            file_names (list): Lista de caminhos de arquivo para salvar os PDFs
            orientation (str): Orientação da página ('portrait' ou 'landscape')
            use_multiprocessing (bool): Se deve usar processamento paralelo (padrão: False)
            max_workers (int, optional): Número máximo de workers paralelos
        
        Returns:
            list: Lista de caminhos dos PDFs gerados com sucesso
        
        Raises:
            ValueError: Se o número de conteúdos HTML não corresponder ao número de nomes de arquivo
        """
        if len(html_contents) != len(file_names):
            raise ValueError("O número de conteúdos HTML deve corresponder ao número de nomes de arquivo")
        
        # Garantir que todos os caminhos são absolutos e criar diretórios pai
        full_paths = []
        for file_name in file_names:
            if not os.path.isabs(file_name):
                full_path = os.path.join(self.output_dir, file_name)
            else:
                full_path = file_name
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            full_paths.append(full_path)
        
        generated_files = []
        
        # Usar processamento sequencial por padrão (mais estável no Windows)
        if not use_multiprocessing:
            for html_content, output_path in zip(html_contents, full_paths):
                try:
                    result_path = self.generate_pdf(html_content, output_path, orientation)
                    generated_files.append(result_path)
                except Exception as e:
                    print(f"Erro ao gerar PDF para {output_path}: {e}", file=sys.stderr)
                    continue
        else:
            # Usar processamento paralelo apenas se explicitamente solicitado
            tasks = [(html_content, output_path, orientation) 
                    for html_content, output_path in zip(html_contents, full_paths)]
            
            # Determinar número de workers
            if max_workers is None:
                max_workers = min(2, os.cpu_count() or 1)  # Reduzido para evitar sobrecarga
            
            try:
                # Suprimir warnings do GLib no Windows
                if sys.platform.startswith('win'):
                    import warnings
                    warnings.filterwarnings("ignore", category=UserWarning)
                
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    # Submeter todas as tarefas
                    future_to_path = {
                        executor.submit(_execute_generate_pdf_task, task): task[1] 
                        for task in tasks
                    }
                    
                    # Coletar resultados
                    for future in as_completed(future_to_path):
                        output_path = future_to_path[future]
                        try:
                            result_path = future.result()
                            generated_files.append(result_path)
                        except Exception as e:
                            print(f"Erro ao gerar PDF para {output_path}: {e}", file=sys.stderr)
                            continue
                            
            except Exception as e:
                print(f"Erro durante geração em lote multiprocesso: {e}", file=sys.stderr)
                print("Voltando para processamento sequencial...", file=sys.stderr)
                # Fallback para processamento sequencial
                generated_files = []
                for html_content, output_path in zip(html_contents, full_paths):
                    try:
                        result_path = self.generate_pdf(html_content, output_path, orientation)
                        generated_files.append(result_path)
                    except Exception as individual_error:
                        print(f"Erro individual ao gerar PDF para {output_path}: {individual_error}", file=sys.stderr)
                        continue
        
        return generated_files
    
    def clean_output_directory(self):
        """Remove todos os arquivos do diretório de saída, mantendo subdiretórios."""
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                file_path = os.path.join(self.output_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass  # Ignorar erros de remoção
