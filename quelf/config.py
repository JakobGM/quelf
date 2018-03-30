from pathlib import Path
from typing import Optional

import yaml


class Config:
    def __init__(self, config_file: Optional[Path] = None) -> None:
        if not config_file:
            config_file = Path(__file__).parents[1] / 'config.yaml'

        with open(config_file, 'r') as file:
            self.yaml = yaml.load(file)

    def __getitem__(self, key):
        return self.yaml[key]

