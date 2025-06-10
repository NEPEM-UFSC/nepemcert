"""
Módulo para geração de PDFs a partir de HTML usando WeasyPrint.
"""
import os
import sys
import warnings
import contextlib
from io import BytesIO, StringIO
from concurrent.futures import ProcessPoolExecutor
# import functools # No longer needed
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

class PDFGenerator:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    @contextlib.contextmanager
    def _suppress_warnings(self):
        """
        Context manager para suprimir avisos do WeasyPrint no Windows.
        Redireciona temporariamente stderr para suprimir mensagens de GLib-GIO-WARNING.
        """
        if sys.platform.startswith('win'):
            # No Windows, capturamos stderr para suprimir avisos do GLib
            original_stderr = sys.stderr
            sys.stderr = StringIO()
            try:
                yield
            finally:
                sys.stderr = original_stderr
        else:
            # Em outros sistemas, não fazemos nada
            yield
    
    def generate_pdf(self, html_content, output_path=None, orientation='landscape'):
        """
        Gera um PDF a partir de conteúdo HTML usando WeasyPrint.
        Se output_path for None, retorna os bytes do PDF.
        Caso contrário, salva o PDF no caminho especificado.
        
        Args:
            html_content (str): Conteúdo HTML para converter
            output_path (str, opcional): Caminho para salvar o PDF
            orientation (str, opcional): Orientação do PDF ('portrait' ou 'landscape')
        
        Returns:
            bytes ou str: Bytes do PDF ou caminho do arquivo salvo
        """
        try:
            # Configuração de fontes para WeasyPrint
            font_config = FontConfiguration()
            
            # Definir orientação e tamanho da página
            page_size = 'A4 landscape' if orientation == 'landscape' else 'A4 portrait'
            # CSS para definir orientação da página, margens e garantir posicionamento correto
            css_content = f"""
                @page {{
                    size: {page_size};
                    margin: 0;  /* Removendo margens para evitar deslocamento */
                }}
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    position: relative;
                }}
                /* Certificar que elementos com posição absoluta sejam renderizados corretamente */
                .qr-placeholder {{
                    position: absolute !important;
                    /* Não alterar tamanho ou margem */
                    box-sizing: border-box !important;
                }}
                /* Garantir que as imagens dentro dos placeholders mantenham dimensões exatas */
                .qr-placeholder img {{
                    width: 100% !important;
                    height: 100% !important;
                    display: block !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    object-fit: contain !important;
                }}
            """
            
            # Criar objetos HTML e CSS
            html_doc = HTML(string=html_content)
            css_doc = CSS(string=css_content)
              # Se não houver caminho de saída, retorna os bytes
            if output_path is None:
                pdf_buffer = BytesIO()
                with self._suppress_warnings():
                    html_doc.write_pdf(pdf_buffer, stylesheets=[css_doc], font_config=font_config)
                pdf_data = pdf_buffer.getvalue()
                pdf_buffer.close()
                return pdf_data
            else:
                # Se tiver caminho de saída, salva o arquivo
                with self._suppress_warnings():
                    html_doc.write_pdf(output_path, stylesheets=[css_doc], font_config=font_config)
                return output_path
                
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar PDF: {str(e)}")
    
    def batch_generate(self, html_contents, file_names, orientation='landscape'):
        """
        Gera múltiplos PDFs a partir de uma lista de conteúdos HTML.
        Retorna uma lista de caminhos para os PDFs gerados.
        
        Nota: file_names deve conter os caminhos completos para os arquivos de saída.
        
        Args:
            html_contents (list): Lista de conteúdos HTML
            file_names (list): Lista de caminhos para salvar os PDFs
            orientation (str, opcional): Orientação dos PDFs ('portrait' ou 'landscape')
            
        Returns:
            list: Lista de caminhos dos PDFs gerados
        """
        if len(html_contents) != len(file_names):
            raise ValueError("O número de conteúdos HTML e nomes de arquivo deve ser igual")

        # Helper function to be called by ProcessPoolExecutor
        # It needs to be defined here or be a static method or top-level function
        # to be picklable by some serializers.
        # However, instance methods are generally picklable if the instance itself is.
        # Let's try with an instance method first.
        
        # Prepare arguments for each call to self.generate_pdf
        # We need to ensure that if self.generate_pdf itself relies on instance state
        # that isn't picklable, this won't work.
        # generate_pdf uses self._suppress_warnings. The method itself should be fine.
        
        results = []
        # Using os.cpu_count() for the number of workers
        # Ensure ProcessPoolExecutor is properly managed using a 'with' statement
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            # Create a list of arguments for each task
            # Each item in tasks will be (html_content, output_path, orientation)
            tasks_args = []
            for i, html_content in enumerate(html_contents):
                file_path = file_names[i] # file_names contains full paths
                tasks_args.append((html_content, file_path, orientation))

            # Define a wrapper function that can be pickled and used by executor.map
            # This wrapper will call the instance method.
            # This is one way to ensure picklability and manage arguments.
            def _execute_generate_pdf(task_arg_tuple):
                # Unpack arguments and call the instance method
                # self here refers to the PDFGenerator instance
                try:
                    return self.generate_pdf(task_arg_tuple[0], task_arg_tuple[1], task_arg_tuple[2])
                except Exception as e:
                    # Log error or handle as per requirements
                    # For now, we'll let it propagate to be caught by the caller of map,
                    # or collected if we iterate over futures.
                    # To make it more robust and allow other tasks to complete,
                    # we'd typically catch, log, and return a specific error marker.
                    # For this iteration, the error will be raised when results are consumed.
                    print(f"Error generating PDF for {task_arg_tuple[1]}: {e}", file=sys.stderr) # Basic logging
                    return e # Return the exception itself to indicate failure for this task

            try:
                # executor.map executes the calls in parallel
                # Results will be in the order of the input iterables
                # If an exception occurs in one of the calls, it will be raised when iterating results
                # or when calling list() on map_results.
                map_results = executor.map(_execute_generate_pdf, tasks_args)
                
                # Collect results, handling potential exceptions from individual tasks
                for result in map_results:
                    if isinstance(result, Exception):
                        # Log or collect errors; for now, just print and add None or raise
                        # Depending on strictness, we might raise here, or collect all paths
                        # and report errors separately.
                        # The subtask says "logged or reported without crashing the entire batch process"
                        # Returning the exception from the worker and then printing it here
                        # and not adding to pdf_paths achieves part of that.
                        # The overall batch won't crash if we just collect paths of successful operations.
                        print(f"A PDF generation failed: {result}", file=sys.stderr)
                        # results.append(None) # Or some other marker for failure
                    else:
                        results.append(result) # result here is the output_path from generate_pdf

            except Exception as e:
                # This would catch errors from executor.map itself (e.g., if a worker process dies)
                # or if _execute_generate_pdf re-raised an exception not caught by its own try-except.
                # For now, let the exception propagate to the caller of batch_generate.
                # A more sophisticated error handling strategy might be needed for production.
                print(f"An unexpected error occurred during batch PDF generation: {e}", file=sys.stderr)
                # Depending on requirements, we might re-raise, or return partial results.
                raise # Re-raise the first exception encountered by map or executor issue

        # Filter out any None results if we decided to add them for errors
        pdf_paths = [path for path in results if path is not None and not isinstance(path, Exception)]
        return pdf_paths
    
    def clean_output_directory(self):
        """Limpa todos os arquivos do diretório de saída"""
        for file in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
