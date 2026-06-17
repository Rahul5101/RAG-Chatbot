# utils.py
import yaml
import os

# Base directory points to the root of your project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_config(file_path: str = os.path.join(BASE_DIR, 'config', 'config.yaml')):
    """
    Load YAML configuration file.

    Args:
        file_path (str): Path to the YAML config file.

    Returns:
        dict: Parsed configuration dictionary.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
    return config
