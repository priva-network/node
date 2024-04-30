import os
import json
from pathlib import Path
from web3 import Web3

class Config:
    """Base config."""
    DATA_BASE_DIR = str(Path.home() / '.priva/')
    CONFIG_FILE_PATH = str(Path.home() / '.priva/config.json')
    DATABASE_FILE_PATH = str(Path.home() / '.priva/data')

    APP_HOST = '0.0.0.0'
    APP_PORT = 8000

    ETHERSCAN_URL = None

    NODE_IP_ADDRESS = 'http://127.0.0.1:8000'

    IPFS_PORT = 5201
    IPFS_CONTAINER_IMAGE = 'ipfs/kubo:latest'
    IPFS_DATA_DIR = str(Path.home() / '.priva/ipfs')

    DEFAULT_LOGGING_LEVEL = 'DEBUG'
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
        },
        'root': {
            'level': 'DEBUG',
        },
    }

    SUPPORTED_MODELS = [
        # FIXME: Commented out mistral as it takes too long to download
        #'mistralai/mistral-7b-v0.1',
        'tinyllama/tinyllama-1.1b-chat-v1.0',
    ]

    USD_COST_PER_1000_TOKENS = {
        'default': 0.01,
        'mistralai/mistral-7b-v0.1': 0.02,
    }

    LOCAL_INFERENCE_ENABLED = True

    def __init__(self):
        """
        Load the configuration from the config file.
        """
        config_filepath = self.CONFIG_FILE_PATH
        if os.path.exists(config_filepath):
            with open(config_filepath, 'r') as file:
                data = json.load(file)
                self.__dict__.update(data)
        else:
            self.save()

    def save(self):
        """
        Save the configuration to the config file.
        """
        config_filepath = self.CONFIG_FILE_PATH
        os.makedirs(os.path.dirname(config_filepath), exist_ok=True)
        with open(config_filepath, 'w') as file:
            json.dump(self.__dict__, file)

    def set(self, key, value, do_save=True):
        """
        Set a configuration value.
        """
        self.__dict__[key] = value
        if do_save:
            self.save()

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    CACHE_MAX_SIZE = 1000
    CACHE_DEFAULT_TTL = 60 * 5 # 5 minutes

    DEFAULT_LOGGING_LEVEL = 'INFO'

    PRIVA_API_BASE_URL = 'https://api.privanetwork.xyz'

    ETHEREUM_NETWORK_URL = 'https://sepolia.base.org'
    ETHERSCAN_URL = 'https://sepolia.basescan.org'

    MIN_CONFIRMATIONS = 3
    NODE_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x2d1e3da7e3f729216731e00b2a112f1587875550')
    NODE_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/NodeRegistry.json'
    SESSION_MANAGER_CONTRACT_ADDRESS = Web3.to_checksum_address('0xA93AE84154f166B64a4C330A284762a96d04CD4a')
    SESSION_MANAGER_CONTRACT_ABI_PATH = 'app/chain/abis/SessionManager.json'
    MODEL_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x9c227cb361C0Cd5DdFeefEe985ad6aA7d83A900c')
    MODEL_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/ModelRegistry.json'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

    DATA_BASE_DIR = str(Path.home() / '.priva/dev/')
    CONFIG_FILE_PATH = str(Path.home() / '.priva/dev/config.json')
    DATABASE_FILE_PATH = str(Path.home() / '.priva/dev/data')

    CACHE_MAX_SIZE = 1000
    CACHE_DEFAULT_TTL = 60 * 5 # 5 minutes

    PRIVA_API_BASE_URL = 'http://localhost:8080'

    ETHEREUM_NETWORK_URL = 'http://127.0.0.1:8545'
    MIN_CONFIRMATIONS = 0 # No confirmations needed for local testing
    NODE_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512')
    NODE_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/NodeRegistry.json'
    SESSION_MANAGER_CONTRACT_ADDRESS = Web3.to_checksum_address('0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0')
    SESSION_MANAGER_CONTRACT_ABI_PATH = 'app/chain/abis/SessionManager.json'
    MODEL_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x5FbDB2315678afecb367f032d93F642f64180aa3')
    MODEL_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/ModelRegistry.json'

# Global config instance
cfg = None
if os.environ.get('PRIVA_ENV') == 'DEV':
    cfg = DevelopmentConfig()
else:
    cfg = ProductionConfig()

def get_config():
    global cfg
    return cfg
