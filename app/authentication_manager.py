#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerenciador de autenticação para o NEPEMCERT.
Responsável pela geração e validação de códigos de autenticação únicos para certificados.
"""

import hashlib
import time
import random
import uuid
from datetime import datetime
import secrets
import os
import json
import base64
import io
import qrcode
from PIL import Image

class AuthenticationManager:
    """
    Gerenciador de códigos de autenticação para certificados.
    
    Esta classe é responsável por:
    - Gerar códigos de autenticação únicos para certificados
    - Armazenar e recuperar códigos de autenticação
    - Validar códigos de autenticação
    """
    
    # Salt padrão para aumentar a segurança
    DEFAULT_SALT = "NEPEMCERT"
    
    def __init__(self, salt=None):
        """
        Inicializa o gerenciador de autenticação.
        
        Args:
            salt (str, optional): Salt personalizado para aumentar a segurança.
                                 Se não for fornecido, usa o salt padrão.
        """
        self.salt = salt or self.DEFAULT_SALT
        
    def gerar_codigo_autenticacao(self, nome_participante, evento, data_evento=None):
        """
        Gera um código de autenticação único para um certificado.
        
        O código é gerado combinando:
        - Nome do participante
        - Nome do evento
        - Data do evento
        - Timestamp atual (microssegundos)
        - Salt fixo ("NEPEMCERT")
        - Número aleatório
        - UUID parcial
        
        Args:
            nome_participante (str): Nome do participante do certificado.
            evento (str): Nome do evento.
            data_evento (str, optional): Data do evento. Se não for fornecida, usa a data atual.
            
        Returns:
            str: Código de autenticação único no formato hexadecimal de 32 caracteres.
        """
        # Obtém timestamp atual em microssegundos
        timestamp = str(int(time.time() * 1000000))
        
        # Usa a data atual se nenhuma for fornecida
        if data_evento is None:
            data_evento = datetime.now().strftime("%d/%m/%Y")
            
        # Gera um número aleatório
        random_seed = str(random.randint(1000000, 9999999))
        
        # Gera parte de um UUID
        uuid_part = str(uuid.uuid4())[:8]
        
        # Gera token seguro
        secure_token = secrets.token_hex(4)
        
        # Combina todos os elementos para gerar o hash
        data_to_hash = (
            f"{self.salt}:{nome_participante}:{evento}:{data_evento}:"
            f"{timestamp}:{random_seed}:{uuid_part}:{secure_token}"
        )
        
        # Gera o hash usando SHA-256 (mais seguro que MD5)
        codigo = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
        
        # Retorna os primeiros 32 caracteres (128 bits) para um código mais amigável
        return codigo[:32]
    def gerar_qrcode_data(self, codigo_autenticacao, url_base="https://nepemufsc.com/verificar-certificados"):
        """
        Gera os dados para um QR Code que pode ser usado para verificar o certificado.
        
        Args:
            codigo_autenticacao (str): Código de autenticação do certificado.
            url_base (str, optional): URL base para o serviço de verificação.
            
        Returns:
            str: URL completa para verificação do certificado.
        """
        # Retorna a URL com o código como parâmetro para uso no QR code
        return f"{url_base}?codigo={codigo_autenticacao}"
    
    def gerar_qrcode_base64(self, codigo_autenticacao, url_base="https://nepemufsc.com/verificar-certificados", box_size=10, border=4):
        """
        Gera um QR Code como imagem codificada em base64 para uso em certificados.
        
        Args:
            codigo_autenticacao (str): Código de autenticação do certificado.
            url_base (str, optional): URL base para o serviço de verificação.
            box_size (int, optional): Tamanho de cada "caixa" do QR code. Padrão é 10.
            border (int, optional): Tamanho da borda em torno do QR code. Padrão é 4.
            
        Returns:
            str: String em base64 da imagem do QR code, pronta para usar em HTML.
        """
        # Gerar a URL completa
        url = self.gerar_qrcode_data(codigo_autenticacao, url_base)
        
        # Configurar o QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        
        # Adicionar dados
        qr.add_data(url)
        qr.make(fit=True)
        
        # Criar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_str}"
    
    def gerar_qrcode_adaptado(self, codigo_autenticacao, html_template, url_base="https://nepemufsc.com/verificar-certificados"):
        """
        Gera um QR Code adaptado às dimensões do placeholder no template.
        Extrai o tamanho do placeholder do QR e gera um QR code ajustado.
        
        Args:
            codigo_autenticacao (str): Código de autenticação do certificado.
            html_template (str): O conteúdo HTML do template para extrair dimensões.
            url_base (str, optional): URL base para o serviço de verificação.
            
        Returns:
            dict: Dicionário contendo:
                - qrcode_base64: QR code em base64 para inserção no template
                - qrcode_width: Largura extraída do placeholder
                - qrcode_height: Altura extraída do placeholder
        """
        # Extrair dimensões do placeholder do QR do template
        import re
        
        # Valores padrão caso não encontre as dimensões
        qr_width = 60
        qr_height = 60
        box_size = 3
        border = 2
        
        # Estratégia 1: Encontrar definição de classe CSS específica para qr-placeholder
        css_pattern = r'\.qr-placeholder\s*\{([^}]*)\}'
        css_match = re.search(css_pattern, html_template, re.DOTALL)
        
        if css_match:
            style_content = css_match.group(1)
            
            # Extrair largura
            width_match = re.search(r'width:\s*(\d+)px', style_content)
            if width_match:
                qr_width = int(width_match.group(1))
            
            # Extrair altura
            height_match = re.search(r'height:\s*(\d+)px', style_content)
            if height_match:
                qr_height = int(height_match.group(1))
        else:
            # Estratégia 2: Buscar elemento específico com atributos inline ou classes relacionadas a QR
            # Primeiro, procura por div com classe qr-placeholder
            element_pattern = r'<div\s+class="qr-placeholder"([^>]*)>'
            element_match = re.search(element_pattern, html_template)
            
            if element_match:
                # Busca atributos de estilo inline
                style_attr = element_match.group(1)
                
                # Extrair inline style se existir
                inline_style_match = re.search(r'style=["\']([^"\']*)["\']', style_attr)
                if inline_style_match:
                    inline_style = inline_style_match.group(1)
                    
                    # Extrair largura e altura do estilo inline
                    width_match = re.search(r'width:\s*(\d+)px', inline_style)
                    if width_match:
                        qr_width = int(width_match.group(1))
                        
                    height_match = re.search(r'height:\s*(\d+)px', inline_style)
                    if height_match:
                        qr_height = int(height_match.group(1))
                        
                # Procurar atributos width e height diretamente no elemento
                width_attr_match = re.search(r'width=["\'](\d+)["\']', style_attr)
                if width_attr_match:
                    qr_width = int(width_attr_match.group(1))
                    
                height_attr_match = re.search(r'height=["\'](\d+)["\']', style_attr)
                if height_attr_match:
                    qr_height = int(height_attr_match.group(1))
        
        # Ajustar parâmetros do QR code baseado nas dimensões encontradas
        # Usar no mínimo 60x60 pixels para garantir legibilidade
        qr_width = max(60, qr_width)
        qr_height = max(60, qr_height)
        
        # Calcular box_size com base no tamanho disponível
        # Um QR code típico tem cerca de 25-30 blocos de largura
        box_size = max(2, min(qr_width, qr_height) // 25)
        
        # Definir um valor de borda reduzido para maximizar o QR code
        border = min(2, max(1, int(min(qr_width, qr_height) * 0.05)))  # 5% da dimensão como borda
        
        # Gerar URL completa
        url = self.gerar_qrcode_data(codigo_autenticacao, url_base)
        
        # Configurar o QR code com dimensões otimizadas
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # Média correção de erro para melhor leitura
            box_size=box_size,
            border=border,
        )
        
        # Adicionar dados
        qr.add_data(url)
        qr.make(fit=True)
        
        # Criar imagem com alta qualidade
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Dimensionar para o tamanho exato do placeholder, garantindo alta qualidade
        from PIL import Image
        qr_img = img.resize((qr_width, qr_height), Image.LANCZOS)  # Usa LANCZOS para melhor qualidade
        
        # Converter para base64
        buffered = io.BytesIO()
        qr_img.save(buffered, format="PNG", optimize=True, quality=95)  # Alta qualidade de PNG
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return {
            "qrcode_base64": f"data:image/png;base64,{img_str}",
            "qrcode_width": qr_width,
            "qrcode_height": qr_height
        }
    
    def salvar_codigo(self, codigo_autenticacao, nome_participante, evento, data_evento, local_evento, carga_horaria):
        """
        Salva as informações do certificado associadas ao código de autenticação.
        Implementação básica - em uma versão real, isso seria salvo em um banco de dados.
        
        Args:
            codigo_autenticacao (str): Código de autenticação do certificado.
            nome_participante (str): Nome do participante.
            evento (str): Nome do evento.
            data_evento (str): Data do evento.
            local_evento (str): Local do evento.
            carga_horaria (str): Carga horária do evento.
            
        Returns:
            bool: True se o código foi salvo com sucesso, False caso contrário.
        """
        # Diretório para armazenar os códigos
        codigo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'codigos')
        os.makedirs(codigo_dir, exist_ok=True)
        
        # Arquivo JSON para armazenar o código
        codigo_file = os.path.join(codigo_dir, f"{codigo_autenticacao}.json")        # Dados do certificado
        dados = {
            "codigo_autenticacao": codigo_autenticacao,
            "nome_participante": nome_participante,
            "evento": evento,
            "data_evento": data_evento,
            "local_evento": local_evento,
            "carga_horaria": carga_horaria,
            "data_geracao": datetime.now().isoformat(),
            "url_verificacao": self.gerar_qrcode_data(codigo_autenticacao),
            "qrcode_base64": self.gerar_qrcode_base64(codigo_autenticacao)
        }
        
        # Salva os dados em um arquivo JSON
        try:
            with open(codigo_file, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Erro ao salvar código de autenticação: {e}")
            return False
    
    def substituir_qr_placeholder(self, html_content, qrcode_base64):
        """
        Substitui o placeholder do QR code pelo QR code real no HTML.
        Preserva posicionamento e estilo exato do placeholder original.
        
        Args:
            html_content (str): Conteúdo HTML do template com o placeholder
            qrcode_base64 (str): QR code em base64 para inserir
            
        Returns:
            str: HTML com o QR code inserido
        """        
        import re
        import logging
        
        # Configurar logging básico para debug
        logging.basicConfig(level=logging.INFO, 
                            filename=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qrcode_debug.log'),
                            filemode='a',
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger('qrcode_substituicao')
        
        # Padrão específico para div com classe qr-placeholder (mais comum)
        pattern1 = r'<div\s+class="qr-placeholder"([^>]*)>(.*?)</div>'
        match = re.search(pattern1, html_content, re.DOTALL)        
        if match:
            # Captura atributos adicionais (como style inline ou id)
            attrs = match.group(1)
            # Mantém a mesma classe para preservar estilos CSS
            replacement = f'<div class="qr-placeholder"{attrs}><img src="{qrcode_base64}" alt="QR Code de verificação" style="width:100%; height:100%; display:block; margin:0; padding:0; border:none;" /></div>'
            
            # Log para debug
            logger.info(f"QR placeholder encontrado: padrão 1 (div com classe qr-placeholder)")
            logger.info(f"Atributos encontrados: {attrs}")
            
            return re.sub(pattern1, replacement, html_content, flags=re.DOTALL)
          # Busca elemento com classe que contenha 'qr' (mais genérico)
        pattern2 = r'<([a-z]+)\s+class="([^"]*qr[^"]*)"([^>]*)>(.*?)</\1>'
        match = re.search(pattern2, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            tag = match.group(1)
            cls = match.group(2)  # Preservar classe original
            attrs = match.group(3)
            replacement = f'<{tag} class="{cls}"{attrs}><img src="{qrcode_base64}" alt="QR Code de verificação" style="width:100%; height:100%; display:block; margin:0; padding:0; border:none;" /></{tag}>'
            
            # Log para debug
            logger.info(f"QR placeholder encontrado: padrão 2 (elemento com classe contendo 'qr')")
            logger.info(f"Tag: {tag}, Classe: {cls}, Outros atributos: {attrs}")
            
            return re.sub(pattern2, replacement, html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Busca qualquer elemento com id que contenha 'qr'
        pattern3 = r'<([a-z]+)\s+id="([^"]*qr[^"]*)"([^>]*)>(.*?)</\1>'
        match = re.search(pattern3, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            tag = match.group(1)
            id_attr = match.group(2)  # Preservar ID original
            attrs = match.group(3)
            replacement = f'<{tag} id="{id_attr}"{attrs}><img src="{qrcode_base64}" alt="QR Code de verificação" style="width:100%; height:100%; display:block; margin:0; padding:0; border:none;" /></{tag}>'
            return re.sub(pattern3, replacement, html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Busca elementos com style inline que define posição
        pattern4 = r'<([a-z]+)([^>]*position:\s*absolute[^>]*)>(.*?QR.*?)</\1>'
        match = re.search(pattern4, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            tag = match.group(1)
            style_attrs = match.group(2)
            replacement = f'<{tag}{style_attrs}><img src="{qrcode_base64}" alt="QR Code de verificação" style="width:100%; height:100%; display:block; margin:0; padding:0; border:none;" /></{tag}>'
            return re.sub(pattern4, replacement, html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Comentário HTML com 'QR'
        pattern5 = r'<!--.*?QR.*?-->'
        match = re.search(pattern5, html_content, re.DOTALL | re.IGNORECASE)
        if match:
            # Se encontrou um comentário, insere o QR na posição padrão
            replacement = f'<div class="qr-placeholder" style="position: absolute; bottom: 50px; left: 50px; width: 60px; height: 60px;"><img src="{qrcode_base64}" alt="QR Code de verificação" style="width:100%; height:100%; display:block; margin:0; padding:0; border:none;" /></div>'
            return html_content.replace(match.group(0), replacement)
          # Se nenhum padrão corresponder, tentar inserir antes do fechamento do body
        body_closing = '</body>'
        if body_closing in html_content:
            # Inserir um QR code com posição absoluta padrão
            qr_code_html = f'<div class="qr-placeholder" style="position: absolute; bottom: 50px; left: 50px; width: 60px; height: 60px; z-index: 1000;"><img src="{qrcode_base64}" alt="QR Code de verificação" style="width:100%; height:100%; display:block; margin:0; padding:0; border:none;" /></div>\n'
            
            # Log para debug
            logger.warning("QR placeholder não encontrado no template, inserindo QR Code padrão antes do fechamento do body")
            
            return html_content.replace(body_closing, qr_code_html + body_closing)
            
        # Se não encontrar nada, retornar o HTML original e registrar erro
        logger.error("Não foi possível inserir o QR code no HTML - nenhum padrão correspondente e nenhuma tag </body> encontrada")
        return html_content
    def verificar_codigo(self, codigo):
        """
        Verifica se um código de autenticação é válido.
        
        Args:
            codigo (str): Código de autenticação do certificado.
            
        Returns:
            dict or None: Dados do certificado se o código for válido, None caso contrário.
        """
        # Diretório dos códigos
        codigo_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'codigos')
        
        # Verificar pelo código de autenticação
        codigo_file = os.path.join(codigo_dir, f"{codigo[:32]}.json")
        if os.path.exists(codigo_file):
            try:
                with open(codigo_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass                
        return None
        
    def gerar_codigo_verificacao(self, codigo_autenticacao):
        """
        [DEPRECATED] Essa função está depreciada e será removida em versões futuras.
        Use apenas o código de autenticação completo.
        
        Args:
            codigo_autenticacao (str): Código de autenticação completo.
            
        Returns:
            str: O mesmo código de autenticação fornecido.
        """
        # Função depreciada - retornando apenas o código de autenticação original
        return codigo_autenticacao
        
    @classmethod
    def gerar_codigo_exemplo(cls):
        """
        Gera um exemplo de código de autenticação com dados de exemplo.
        Útil para demonstração ou testes.
        
        Returns:
            str: código de autenticação
        """
        auth_manager = cls()
        codigo = auth_manager.gerar_codigo_autenticacao(
            "Maria Joaquina de Jesus", 
            "Workshop de Python", 
            "01/06/2025"
        )
        return codigo


if __name__ == "__main__":
    # Exemplo de uso
    auth_manager = AuthenticationManager()
    
    # Gera um código de autenticação
    codigo = auth_manager.gerar_codigo_autenticacao(
        "João Silva", 
        "Congresso de Enfermagem", 
        "15/05/2025"
    )
    
    # Gera URL para QR Code
    qrcode_url = auth_manager.gerar_qrcode_data(codigo)
    
    # Gera QR Code em base64
    qrcode_base64 = auth_manager.gerar_qrcode_base64(codigo)
    
    print(f"Código de autenticação: {codigo}")
    print(f"URL para QR Code: {qrcode_url}")
    print(f"QR Code em base64: {qrcode_base64[:50]}...")  # Mostra apenas o início do base64
    
    # Salva o código
    auth_manager.salvar_codigo(
        codigo,
        "João Silva",
        "Congresso de Enfermagem",
        "15/05/2025",
        "Auditório Central",
        "40 horas"
    )
    
    # Para testar a visualização do QR code, podemos criar um HTML simples
    test_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Teste QR Code NEPEMCERT</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; }}
            .certificate {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .qrcode {{ width: 200px; height: auto; margin: 20px auto; }}
        </style>
    </head>
    <body>
        <div class="certificate">
            <h1>Certificado de Teste</h1>
            <p>Certificamos que <b>João Silva</b> participou do evento <b>Congresso de Enfermagem</b>.</p>
            <p>Código de autenticação: {codigo}</p>
            <p>Verifique a autenticidade em: {qrcode_url}</p>
            <img class="qrcode" src="{qrcode_base64}" alt="QR Code de verificação" />
        </div>
    </body>
    </html>
    """
    
    # Salva o HTML de teste
    test_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output', 'qrcode_test.html')
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print(f"\nArquivo de teste gerado: {test_file}")
