import sys
from pathlib import Path
from web3 import Web3

class Config:
    """Base config."""
    DATA_BASE_DIR = str(Path.home() / '.cortex/')

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

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    REDIS_URL = 'redis://localhost:6379/0'

    ETHEREUM_NETWORK_URL = 'https://mainnet.infura.io/v3/your_infura_key'
    NODE_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x5FbDB2315678afecb367f032d93F642f64180aa3')
    NODE_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/NodeRegistry.json'
    SESSION_MANAGER_CONTRACT_ADDRESS = Web3.to_checksum_address('0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512')
    SESSION_MANAGER_CONTRACT_ABI_PATH = 'app/chain/abis/SessionManager.json'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

    REDIS_URL = 'redis://localhost:6379/0'

    ETHEREUM_NETWORK_URL = 'http://127.0.0.1:8545'
    NODE_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x5FbDB2315678afecb367f032d93F642f64180aa3')
    NODE_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/NodeRegistry.json'
    SESSION_MANAGER_CONTRACT_ADDRESS = Web3.to_checksum_address('0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512')
    SESSION_MANAGER_CONTRACT_ABI_PATH = 'app/chain/abis/SessionManager.json'
