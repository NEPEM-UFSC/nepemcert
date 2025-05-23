"""
Módulo para gerenciamento de templates HTML para certificados.
"""
import os
import re
import jinja2
import base64
from pathlib import Path

class TemplateManager:
    def __init__(self, templates_dir="templates"):
        self.templates_dir = templates_dir
        os.makedirs(templates_dir, exist_ok=True)
        self.docs_dir = os.path.join(templates_dir, "docs")
        os.makedirs(self.docs_dir, exist_ok=True)
    
    def save_template(self, name, content):
        """Salva um template HTML"""
        if not name.endswith('.html'):
            name = f"{name}.html"
        
        template_path = os.path.join(self.templates_dir, name)
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
        return template_path
    
    def load_template(self, name):
        """Carrega o conteúdo de um template"""
        if not name.endswith('.html'):
            name = f"{name}.html"
            
        template_path = os.path.join(self.templates_dir, name)
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        return None
    
    def delete_template(self, name):
        """Exclui um template"""
        if not name.endswith('.html'):
            name = f"{name}.html"
            
        template_path = os.path.join(self.templates_dir, name)
        if os.path.exists(template_path):
            os.remove(template_path)
            return True
        return False
    
    def list_templates(self):
        """Lista todos os templates disponíveis"""
        if not os.path.exists(self.templates_dir):
            return []
        return [f for f in os.listdir(self.templates_dir) if f.endswith('.html')]
    
    def extract_placeholders(self, template_content):
        """Extrai os placeholders de um template"""
        pattern = r'\{\{\s*(\w+)\s*\}\}'
        placeholders = re.findall(pattern, template_content)
        return list(set(placeholders))
    
    def validate_template(self, template_content):
        """Valida se um template contém elementos problemáticos"""
        warnings = []
        
        # Lista de tags e atributos que podem ser problemáticos
        problematic_patterns = [
            (r'<iframe', 'Tags <iframe> não são suportadas'),
            (r'<canvas', 'Tags <canvas> não são suportadas'),
            (r'<svg', 'Tags <svg> podem ter suporte limitado'),
            (r'position\s*:\s*fixed', 'position:fixed não é bem suportado'),
            (r'display\s*:\s*flex', 'display:flex pode não funcionar como esperado'),
            (r'@media', 'Media queries não são suportadas'),
            (r'animation', 'Animações CSS não são suportadas'),
            (r'transition', 'Transições CSS não são suportadas'),
            (r'transform', 'Transformações CSS podem ter suporte limitado')
        ]
        
        for pattern, message in problematic_patterns:
            if re.search(pattern, template_content, re.IGNORECASE):
                warnings.append(message)
        
        return warnings
    
    def render_template(self, template_name, data):
        """Renderiza um template com os dados fornecidos"""
        template_path = os.path.join(self.templates_dir, template_name)
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template {template_name} não encontrado")
        
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(template_path)))
        template = env.get_template(os.path.basename(template_path))
        
        return template.render(data)

    def save_template_documentation(self, template_name, placeholders_docs):
        """Salva a documentação dos placeholders de um template"""
        doc_path = os.path.join(self.docs_dir, f"{os.path.splitext(template_name)[0]}.csv")
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write("placeholder,descrição\n")
            for placeholder, desc in placeholders_docs.items():
                f.write(f'"{placeholder}","{desc}"\n')
        return doc_path

    def load_template_documentation(self, template_name):
        """Carrega a documentação dos placeholders de um template"""
        doc_path = os.path.join(self.docs_dir, f"{os.path.splitext(template_name)[0]}.csv")
        if os.path.exists(doc_path):
            docs = {}
            with open(doc_path, "r", encoding="utf-8") as f:
                next(f)  # pular cabeçalho
                for line in f:
                    if "," in line:
                        parts = line.strip().split(",", 1)
                        placeholder = parts[0].strip('"')
                        desc = parts[1].strip('"') if len(parts) > 1 else ""
                        docs[placeholder] = desc
            return docs
        return {}

    def validate_template_with_docs(self, template_content, documentation):
        """Valida se todos os placeholders do template estão documentados"""
        placeholders = self.extract_placeholders(template_content)
        missing_docs = [p for p in placeholders if p not in documentation]
        extra_docs = [p for p in documentation if p not in placeholders]
        return {
            "missing_docs": missing_docs,
            "extra_docs": extra_docs,
            "valid": len(missing_docs) == 0
        }
    
    def validate_template_for_xhtml2pdf(self, template_content):
        """Valida se um template contém elementos problemáticos para o xhtml2pdf"""
        return self.validate_template(template_content)
    
    def validate_placeholders_against_csv(self, placeholders, csv_columns):
        """Valida se todos os placeholders têm colunas correspondentes no CSV"""
        if not csv_columns:
            return []
        return [p for p in placeholders if p not in csv_columns]
    
    def get_image_as_base64(self, file_obj):
        """Converte um arquivo de imagem para base64"""
        try:
            return base64.b64encode(file_obj.getvalue()).decode('utf-8')
        except Exception:
            return None
    
    def save_uploaded_file(self, uploaded_file, dir_path):
        """Salva um arquivo carregado pelo usuário"""
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
