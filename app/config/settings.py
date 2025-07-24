import yaml 
from typing import Dict, List

class CategoryKeywordLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path

    def load(self) -> Dict[str, List[str]]:
        with open(self.config_path, 'r') as file:
            data = yaml.safe_load(file)
        if not isinstance(data, dict):
            raise ValueError('YAML root must be a dictionary of categories.')
        for category, keywords in data.items():
            if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
                raise ValueError(f'Category "{category}" must map to a list of strings.')
        return data

