"""
Módulo para mapeamento de campos CSV para placeholders nos templates.
"""

class FieldMapper:
    def __init__(self):
        pass
    
    def map_data_to_template(self, data_row, placeholders):
        """
        Mapeia dados de uma linha do CSV para os placeholders do template.
        Retorna um dicionário apenas com os campos que existem como placeholders.
        """
        template_data = {}
        for field, value in data_row.items():
            if field in placeholders:
                template_data[field] = value
        
        return template_data
    
    def validate_mapping(self, csv_columns, template_placeholders):
        """
        Valida se todos os placeholders do template existem nas colunas do CSV.
        Retorna uma lista de placeholders que não têm correspondência.
        """
        missing_fields = [p for p in template_placeholders if p not in csv_columns]
        return missing_fields
    
    def create_sample_data(self, placeholders):
        """
        Cria dados de exemplo para os placeholders.
        Útil para testes e previews quando não há dados reais.
        """
        sample_data = {}
        for placeholder in placeholders:
            sample_data[placeholder] = f"Exemplo de {placeholder}"
        
        return sample_data
    
    def get_field_info(self, field_name, df):
        """
        Retorna informações sobre um campo específico no DataFrame.
        Inclui tipo de dados, valores únicos, etc.
        """
        if field_name not in df.columns:
            return None
        
        column = df[field_name]
        return {
            "name": field_name,
            "type": str(column.dtype),
            "unique_values": column.nunique(),
            "sample_values": column.unique()[:5].tolist() if column.nunique() < 10 else [],
            "has_nulls": column.isnull().any()
        }
