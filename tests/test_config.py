from config import Config

def test_retrieving_config_variable():
    config = Config('tests/test_config.yaml')
    assert config['dropbox']['app_key'] == 'testappkey'
