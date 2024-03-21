from pathlib import Path
from web3 import Web3

class Config:
    """Base config."""
    DATA_BASE_DIR = str(Path.home() / '.cortex/')
    DATABASE_FILE_PATH = str(Path.home() / '.cortex/data')

    NODE_IP_ADDRESS = 'http://127.0.0.1:8000'

    IPFS_PORT = 5201
    IPFS_CONTAINER_IMAGE = 'ipfs/kubo:latest'
    IPFS_DATA_DIR = str(Path.home() / '.cortex/ipfs')

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
        'mistralai/mistral-7b-v0.1',
        'tinyllama/tinyllama-1.1b-chat-v1.0',
    ]

    USD_COST_PER_1000_TOKENS = {
        'default': 0.01,
        'mistralai/mistral-7b-v0.1': 0.02,
    }

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DATA_BASE_DIR = str(Path.home() / '.cortex/prod/')
    DATABASE_FILE_PATH = str(Path.home() / '.cortex/prod/data')

    CACHE_MAX_SIZE = 1000
    CACHE_DEFAULT_TTL = 60 * 5 # 5 minutes

    ETHEREUM_NETWORK_URL = 'https://sepolia.base.org'
    NODE_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x98e61B44D85C866bd040d733479A1431555dC6FE')
    NODE_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/NodeRegistry.json'
    SESSION_MANAGER_CONTRACT_ADDRESS = Web3.to_checksum_address('0x9e975b6E3e72FDD91Edfa71183B4a38997eFc560')
    SESSION_MANAGER_CONTRACT_ABI_PATH = 'app/chain/abis/SessionManager.json'
    MODEL_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x9c227cb361C0Cd5DdFeefEe985ad6aA7d83A900c')
    MODEL_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/ModelRegistry.json'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

    CACHE_MAX_SIZE = 1000
    CACHE_DEFAULT_TTL = 60 * 5 # 5 minutes

    ETHEREUM_NETWORK_URL = 'http://127.0.0.1:8545'
    NODE_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x5FbDB2315678afecb367f032d93F642f64180aa3')
    NODE_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/NodeRegistry.json'
    SESSION_MANAGER_CONTRACT_ADDRESS = Web3.to_checksum_address('0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512')
    SESSION_MANAGER_CONTRACT_ABI_PATH = 'app/chain/abis/SessionManager.json'
    MODEL_REGISTRY_CONTRACT_ADDRESS = Web3.to_checksum_address('0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0')
    MODEL_REGISTRY_CONTRACT_ABI_PATH = 'app/chain/abis/ModelRegistry.json'
