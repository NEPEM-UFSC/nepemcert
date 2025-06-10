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
import sqlite3

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
        
        # Determine the base directory of the project (nepem-sice)
        # __file__ is app/authentication_manager.py
        # os.path.dirname(__file__) is app/
        # os.path.dirname(os.path.dirname(__file__)) is the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(project_root, 'codigos', 'auth_codes.db')
        
        # Ensure 'codigos' directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row # Access columns by name
        self._create_table()

    def _create_table(self):
        """Cria a tabela auth_codes se ela não existir."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_codes (
                    codigo_autenticacao TEXT PRIMARY KEY,
                    nome_participante TEXT,
                    evento TEXT,
                    data_evento TEXT,
                    local_evento TEXT,
                    carga_horaria TEXT,
                    data_geracao TEXT,
                    url_verificacao TEXT,
                    qrcode_base64 TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao criar tabela SQLite: {e}")
            # Depending on the application, might want to raise this or handle more gracefully

    def close_connection(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()

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
    
    def gerar_qrcode_adaptado(self, codigo_autenticacao, template_content):
        """
        Gera QR code e retorna informações adaptadas para o template.
        
        Args:
            codigo_autenticacao (str): Código de autenticação
            template_content (str): Conteúdo do template HTML
            
        Returns:
            dict: Dicionário com informações do QR code
        """
        # Gerar QR code base64
        qrcode_base64 = self.gerar_qrcode_base64(codigo_autenticacao)
        
        # Retornar informações estruturadas
        return {
            "qrcode_base64": qrcode_base64,
            "codigo_autenticacao": codigo_autenticacao,
            "url_verificacao": "https://nepemufsc.com/verificar",
            "template_has_qr_placeholder": "qr-placeholder" in template_content or "qr-code-placeholder" in template_content
        }

    def salvar_codigo(self, codigo_autenticacao, nome_participante, evento, data_evento, local_evento, carga_horaria):
        """
        Salva as informações do certificado associadas ao código de autenticação no banco de dados SQLite.
        
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
        dados = {
            "codigo_autenticacao": codigo_autenticacao,
            "nome_participante": nome_participante,
            "evento": evento,
            "data_evento": data_evento,
            "local_evento": local_evento,
            "carga_horaria": carga_horaria,
            "data_geracao": datetime.now().isoformat(),
            "url_verificacao": self.gerar_qrcode_data(codigo_autenticacao),
            "qrcode_base64": self.gerar_qrcode_base64(codigo_autenticacao) # Storing for consistency, though can be regenerated
        }
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO auth_codes (
                    codigo_autenticacao, nome_participante, evento, data_evento, 
                    local_evento, carga_horaria, data_geracao, url_verificacao, qrcode_base64
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dados["codigo_autenticacao"], dados["nome_participante"], dados["evento"], dados["data_evento"],
                dados["local_evento"], dados["carga_horaria"], dados["data_geracao"],
                dados["url_verificacao"], dados["qrcode_base64"]
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao salvar código de autenticação no SQLite: {e}")
            return False
    
    def substituir_qr_placeholder(self, html_content, qrcode_base64):
        """
        Substitui o placeholder <div id="qr-code-placeholder"></div> pelo QR code real no HTML.
        O QR code (imagem) será inserido DENTRO deste div.
        
        Args:
            html_content (str): Conteúdo HTML do template com o placeholder.
            qrcode_base64 (str): QR code em base64 para inserir.
            
        Returns:
            str: HTML com o QR code inserido, ou o HTML original se o placeholder não for encontrado.
        """
        placeholder_tag = '<div id="qr-code-placeholder"></div>'
        
        # The image will be styled to take 100% width and height of its container (the placeholder div).
        # Specific sizing of the QR code should be handled by styling the #qr-code-placeholder div in CSS.
        qr_image_html = f'<img src="{qrcode_base64}" alt="QR Code de verificação" style="width:100%; height:100%; display:block;">'
        
        # Replacement inserts the image inside the div
        replacement_html = f'<div id="qr-code-placeholder">{qr_image_html}</div>'
        
        if placeholder_tag in html_content:
            # Using simple string replacement as the placeholder is fixed.
            new_html_content = html_content.replace(placeholder_tag, replacement_html)
            # Optionally, log that replacement occurred (using print to stderr for simplicity here)
            # import sys
            # print(f"QR Code placeholder found and replaced.", file=sys.stderr)
            return new_html_content
        else:
            # import sys
            # print(f"QR Code placeholder '{placeholder_tag}' not found in HTML content.", file=sys.stderr)
            return html_content # Return original content if placeholder is not found
    def verificar_codigo(self, codigo):
        """
        Verifica se um código de autenticação é válido.
        
        Args:
            codigo (str): Código de autenticação do certificado.
            
        Returns:
            dict or None: Dados do certificado se o código for válido, None caso contrário.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM auth_codes WHERE codigo_autenticacao = ?", (codigo[:32],)) # Ensure we use the same length as before if it was truncated
            row = cursor.fetchone()
            
            if row:
                return dict(row) # Convert sqlite3.Row to dict
            else:
                return None
        except sqlite3.Error as e:
            print(f"Erro ao verificar código no SQLite: {e}")
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
    # Exemplo de verificação
    dados_verificados = auth_manager.verificar_codigo(codigo)
    if dados_verificados:
        print(f"\nCódigo verificado com sucesso. Nome: {dados_verificados['nome_participante']}")
    else:
        print(f"\nFalha ao verificar código: {codigo}")

    # Fechar conexão ao final do uso (importante em aplicações reais)
    auth_manager.close_connection()

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
