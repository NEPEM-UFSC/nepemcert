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
  
    
    def gerar_qrcode_data(self, codigo_autenticacao, url_base="https://nepemufsc.com/verificar-certificados?="):
        """
        Gera os dados para um QR Code que pode ser usado para verificar o certificado.
        
        Args:
            codigo_autenticacao (str): Código de autenticação do certificado.
            url_base (str, optional): URL base para o serviço de verificação.
            
        Returns:
            str: URL completa para verificação do certificado.
        """
        return f"{url_base}{codigo_autenticacao}"
        
    def gerar_qrcode_base64(self, codigo_autenticacao, url_base="https://nepemufsc.com/verificar-certificados?=", box_size=10, border=4):
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
        codigo_file = os.path.join(codigo_dir, f"{codigo_autenticacao}.json")          # Dados do certificado
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
