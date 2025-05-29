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
    
    def generate_pdf(self, html_content, output_path=None, orientation='landscape'):
        """
        Gera um PDF a partir de conteúdo HTML.
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
            # Adiciona CSS para definir orientação da página
            css = f"@page {{ size: {orientation}; margin: 1cm; }}"
            html_with_css = f"<style>{css}</style>{html_content}"
            
            # Se não houver caminho de saída, retorna os bytes
            if output_path is None:
                pdf_buffer = BytesIO()
                pisa.CreatePDF(BytesIO(html_with_css.encode('utf-8')), pdf_buffer)
                pdf_data = pdf_buffer.getvalue()
                pdf_buffer.close()
                return pdf_data
            else:
                # Se tiver caminho de saída, salva o arquivo
                with open(output_path, "wb") as output_file:
                    pisa.CreatePDF(BytesIO(html_with_css.encode('utf-8')), output_file)
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
