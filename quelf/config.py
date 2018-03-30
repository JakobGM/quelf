from pathlib import Path
from typing import Optional

import yaml


CONFIG_DIRECTORY = Path(__file__).parents[1]
CONFIG_FILE = CONFIG_DIRECTORY / 'config.yml'
DATA_DIRECTORY = CONFIG_DIRECTORY / 'data'


class Config:
    def __init__(self, config_file: Path = CONFIG_FILE) -> None:
        with open(config_file, 'r') as file:
            self.yaml = yaml.load(file)

    def __getitem__(self, key):
        return self.yaml[key]

