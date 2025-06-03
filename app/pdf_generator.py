"""
Módulo para geração de PDFs a partir de HTML usando WeasyPrint.
"""
import os
import sys
import warnings
import contextlib
from io import BytesIO, StringIO
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
        
        pdf_paths = []
        for i, html in enumerate(html_contents):
            # Usamos o caminho completo fornecido, sem adicionar self.output_dir novamente
            file_path = file_names[i]
            self.generate_pdf(html, file_path, orientation)
            pdf_paths.append(file_path)
        
        return pdf_paths
    
    def clean_output_directory(self):
        """Limpa todos os arquivos do diretório de saída"""
        for file in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
