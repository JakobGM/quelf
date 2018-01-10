import yaml


class Config:
    def __init__(self, config_file_path='config.yaml'):
        with open(config_file_path, 'r') as config_file:
            self.yaml = yaml.load(config_file)

    def __getitem__(self, key):
        return self.yaml[key]

