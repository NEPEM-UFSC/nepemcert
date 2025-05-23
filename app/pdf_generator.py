"""
Módulo para geração de PDFs a partir de HTML.
"""
import os
from io import BytesIO
from xhtml2pdf import pisa

class PDFGenerator:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_pdf(self, html_content, output_path=None):
        """
        Gera um PDF a partir de conteúdo HTML.
        Se output_path for None, retorna os bytes do PDF.
        Caso contrário, salva o PDF no caminho especificado.
        """
        try:
            # Se não houver caminho de saída, retorna os bytes
            if output_path is None:
                pdf_buffer = BytesIO()
                pisa.CreatePDF(BytesIO(html_content.encode('utf-8')), pdf_buffer)
                pdf_data = pdf_buffer.getvalue()
                pdf_buffer.close()
                return pdf_data
            else:
                # Se tiver caminho de saída, salva o arquivo
                with open(output_path, "wb") as output_file:
                    pisa.CreatePDF(BytesIO(html_content.encode('utf-8')), output_file)
                return output_path
                
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar PDF: {str(e)}")
    
    def batch_generate(self, html_contents, file_names):
        """
        Gera múltiplos PDFs a partir de uma lista de conteúdos HTML.
        Retorna uma lista de caminhos para os PDFs gerados.
        """
        if len(html_contents) != len(file_names):
            raise ValueError("O número de conteúdos HTML e nomes de arquivo deve ser igual")
        
        pdf_paths = []
        for i, html in enumerate(html_contents):
            file_path = os.path.join(self.output_dir, file_names[i])
            self.generate_pdf(html, file_path)
            pdf_paths.append(file_path)
        
        return pdf_paths
    
    def clean_output_directory(self):
        """Limpa todos os arquivos do diretório de saída"""
        for file in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
