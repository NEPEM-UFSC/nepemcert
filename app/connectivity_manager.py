"""
Módulo para gerenciamento de conectividade com servidor remoto.
"""

import os
import json
import time
from datetime import datetime
import requests

class ConnectivityManager:
    def __init__(self, config_dir="config"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "connectivity.json")
        os.makedirs(config_dir, exist_ok=True)
        self.load_config()

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "NEPEMCertCLI/1.1.0"})
        if self.config.get("api_key"):
            self.session.headers.update({"X-API-Key": self.config["api_key"]})
    
    def load_config(self):
        """Carrega as configurações de conectividade do arquivo."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception:
                self.config = self._get_default_config()
        else:
            self.config = self._get_default_config()
            self.save_config()
    
    def save_config(self):
        """Salva as configurações de conectividade no arquivo."""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
    
    def _get_default_config(self):
        """Retorna as configurações padrão de conectividade."""
        return {
            "server_url": "",
            "api_key": "",
            "username": "",
            "password": "",
            "last_connection": None,
            "connection_status": "Desconectado",
            "auto_sync": False,
            "sync_interval": 60  # minutos
        }
    
    def check_connection(self):
        """Verifica a conexão com o servidor remoto fazendo uma requisição real."""
        if not self.config.get("server_url"):
            self.config["connection_status"] = "Desconectado"
            self.save_config()
            return {
                "status": "Desconectado",
                "message": "Servidor não configurado",
                "timestamp": datetime.now().isoformat()
            }

        server_url = self.config["server_url"]
        status_endpoint = f"{server_url.rstrip('/')}/api/v1/status"
        timestamp = datetime.now().isoformat()

        try:
            response = self.session.get(status_endpoint, timeout=10)
            response.raise_for_status() # Raises HTTPError for 4XX/5XX status codes
            
            response_data = response.json()
            self.config["connection_status"] = "Conectado"
            message = response_data.get("message", "Conexão estabelecida com sucesso")
            
        except requests.exceptions.Timeout:
            self.config["connection_status"] = "Desconectado"
            message = "Falha na conexão: Timeout (tempo de espera esgotado)."
        except requests.exceptions.ConnectionError:
            self.config["connection_status"] = "Desconectado"
            message = "Falha na conexão: Erro de conexão com o servidor."
        except requests.exceptions.HTTPError as e:
            self.config["connection_status"] = "Desconectado"
            message = f"Falha na conexão: Erro HTTP {e.response.status_code} - {e.response.reason}"
            if e.response.status_code == 401:
                 message += ". Verifique sua chave de API."
            elif e.response.status_code == 404:
                 message += ". Verifique a URL do servidor e o endpoint."
        except requests.exceptions.RequestException as e:
            self.config["connection_status"] = "Desconectado"
            message = f"Falha na conexão: {str(e)}"
        except json.JSONDecodeError:
            self.config["connection_status"] = "Desconectado" #
            message = "Falha ao decodificar JSON da resposta do servidor."
        
        self.config["last_connection"] = timestamp
        self.save_config()
        
        return {
            "status": self.config["connection_status"],
            "message": message,
            "timestamp": timestamp
        }
    
    def set_server_url(self, url):
        """Define a URL do servidor."""
        self.config["server_url"] = url.rstrip('/') if url else ""
        # Potentially reset session or base_url if session object uses it directly,
        # but for now, full URLs are constructed per request.
        self.save_config()
    
    def set_credentials(self, username, password):
        """Define as credenciais de acesso ao servidor (para futura estratégia de autenticação)."""
        self.config["username"] = username
        self.config["password"] = password
        # If using basic auth with session, update here:
        # self.session.auth = (username, password) if username and password else None
        self.save_config()
    
    def set_api_key(self, api_key):
        """Define a chave de API para acesso ao servidor."""
        self.config["api_key"] = api_key
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})
        elif "X-API-Key" in self.session.headers:
            del self.session.headers["X-API-Key"]
        self.save_config()
    
    def upload_certificates(self, file_paths):
        """Envia arquivos de certificado para o servidor."""
        if not self.config.get("server_url"):
            return {"success": False, "message": "Servidor não configurado"}

        server_url = self.config["server_url"]
        upload_endpoint = f"{server_url.rstrip('/')}/api/v1/certificates/upload"
        
        files_to_upload = []
        opened_files = []

        try:
            for i, file_path in enumerate(file_paths):
                if not os.path.exists(file_path):
                    # Skip non-existent files or return error for this specific file
                    # For now, let's assume files exist, or open() will raise FileNotFoundError
                    pass 
                
                # It's good practice to use a more specific name for the field if the API expects it
                # e.g., 'files' or 'certificate_files'. Using 'certificate_batch_X' as per plan.
                file_field_name = f'certificate_batch_{i}'
                f = open(file_path, 'rb')
                opened_files.append(f)
                files_to_upload.append((file_field_name, (os.path.basename(file_path), f, 'application/pdf')))
            
            if not files_to_upload:
                return {"success": False, "message": "Nenhum arquivo válido para upload."}

            response = self.session.post(upload_endpoint, files=files_to_upload, timeout=30) # Timeout 30s
            response.raise_for_status() # Raise HTTPError for bad responses (4XX or 5XX)
            
            return response.json() # Assuming server returns JSON like {"success": True, "message": ..., "details": ...}
        
        except FileNotFoundError as e:
            return {"success": False, "message": f"Erro ao abrir arquivo: {str(e)}"}
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Upload falhou: Timeout."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Upload falhou: Erro de conexão."}
        except requests.exceptions.HTTPError as e:
            error_message = f"Upload falhou: Erro HTTP {e.response.status_code} - {e.response.reason}"
            try: # Try to get more details from response
                error_details = e.response.json().get("detail", "")
                if error_details: error_message += f" ({error_details})"
            except json.JSONDecodeError: pass # No JSON body or invalid JSON
            return {"success": False, "message": error_message}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Upload falhou: {str(e)}"}
        except Exception as e: # Catch other potential errors
            return {"success": False, "message": f"Um erro inesperado ocorreu durante o upload: {str(e)}"}
        finally:
            for f in opened_files:
                f.close()
    
    def download_templates(self):
        """Lista templates disponíveis no servidor."""
        if not self.config.get("server_url"):
            return {"success": False, "message": "Servidor não configurado", "templates": []}

        server_url = self.config["server_url"]
        templates_endpoint = f"{server_url.rstrip('/')}/api/v1/templates"
        
        try:
            response = self.session.get(templates_endpoint, timeout=15) # Timeout 15s
            response.raise_for_status()
            response_data = response.json()
            
            return {
                "success": True,
                "templates": response_data.get("templates", []),
                "message": response_data.get("message", f"{len(response_data.get('templates', []))} templates listados."),
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Timeout ao buscar templates.", "templates": []}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": "Erro de conexão ao buscar templates.", "templates": []}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "message": f"Erro HTTP {e.response.status_code} ao buscar templates.", "templates": []}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Erro ao buscar templates: {str(e)}", "templates": []}
        except json.JSONDecodeError:
            return {"success": False, "message": "Falha ao decodificar JSON da lista de templates.", "templates": []}

    def download_specific_template(self, template_name, target_dir):
        """Baixa um template específico do servidor."""
        if not self.config.get("server_url"):
            return {"success": False, "message": "Servidor não configurado"}

        server_url = self.config["server_url"]
        template_endpoint = f"{server_url.rstrip('/')}/api/v1/templates/{template_name}"
        
        try:
            response = self.session.get(template_endpoint, timeout=15) # Timeout 15s
            response.raise_for_status() # Ensure we proceed only for 200 OK
            
            # Assuming the response for a specific template is its raw HTML content
            template_content = response.text 
            
            os.makedirs(target_dir, exist_ok=True)
            file_path = os.path.join(target_dir, template_name)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            return {"success": True, "message": f"Template '{template_name}' baixado para '{file_path}'.", "path": file_path}

        except requests.exceptions.Timeout:
            return {"success": False, "message": f"Timeout ao baixar template '{template_name}'."}
        except requests.exceptions.ConnectionError:
            return {"success": False, "message": f"Erro de conexão ao baixar template '{template_name}'."}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {"success": False, "message": f"Template '{template_name}' não encontrado no servidor."}
            return {"success": False, "message": f"Erro HTTP {e.response.status_code} ao baixar template '{template_name}'."}
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": f"Erro ao baixar template '{template_name}': {str(e)}"}
        except IOError as e: # Catch file system errors
            return {"success": False, "message": f"Erro ao salvar template '{template_name}': {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Um erro inesperado ocorreu ao baixar template '{template_name}': {str(e)}"}

    def get_connection_status(self):
        """Retorna o status atual da conexão e o horário da última verificação."""
        # This method now primarily returns stored status.
        # `check_connection` is the one to actively probe.
        status = self.config.get("connection_status", "Desconhecido")
        last_connection = self.config.get("last_connection", None)
        
        return {
            "status": status,
            "last_check": last_connection # Renamed for clarity vs "last_connection" timestamp in check_connection response
        }
    
    def toggle_auto_sync(self, enabled=None):
        """Ativa ou desativa a sincronização automática."""
        if enabled is None:
            enabled = not self.config.get("auto_sync", False)
        
        self.config["auto_sync"] = enabled
        self.save_config()
        return enabled
    
    def set_sync_interval(self, minutes):
        """Define o intervalo de sincronização automática."""
        if isinstance(minutes, int) and minutes > 0:
            self.config["sync_interval"] = minutes
            self.save_config()
        else:
            # Handle invalid input if necessary, e.g., log a warning or raise error
            pass
