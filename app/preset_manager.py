"""
Módulo para gerenciamento de presets de configurações do gerador de certificados.
"""
import os
import json
from slugify import slugify

class PresetManager:
    def __init__(self, preset_dir="presets"):
        self.preset_dir = preset_dir
        os.makedirs(preset_dir, exist_ok=True)
    
    def save_preset(self, name, data):
        """Salva um preset com o nome especificado"""
        preset_path = os.path.join(self.preset_dir, f"{slugify(name)}.json")
        with open(preset_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return preset_path
    
    def load_preset(self, name):
        """Carrega um preset pelo nome"""
        preset_path = os.path.join(self.preset_dir, f"{slugify(name)}.json")
        if os.path.exists(preset_path):
            with open(preset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def list_presets(self):
        """Lista todos os presets disponíveis"""
        if not os.path.exists(self.preset_dir):
            return []
        return [os.path.splitext(f)[0] for f in os.listdir(self.preset_dir) if f.endswith(".json")]
    
    def delete_preset(self, name):
        """Exclui um preset pelo nome"""
        preset_path = os.path.join(self.preset_dir, f"{slugify(name)}.json")
        if os.path.exists(preset_path):
            os.remove(preset_path)
            return True
        return False
    
    def get_preset_info(self, name):
        """Retorna informações sobre um preset específico"""
        preset = self.load_preset(name)
        if preset:
            info = {
                "name": name,
                "template": preset.get("template", ""),
                "csv_columns": len(preset.get("csv_columns", [])),
                "created": preset.get("created", "Desconhecido"),
                "description": preset.get("description", "")
            }
            return info
        return None
