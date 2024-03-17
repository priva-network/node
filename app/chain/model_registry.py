from web3 import Web3
from .models import ModelDetails
import json

class ModelRegistry:
    def __init__(self):
        self.w3 = None
        self.contract = None

    def init_config(self, config):
        network_url = config.ETHEREUM_NETWORK_URL
        self.w3 = Web3(Web3.HTTPProvider(network_url))
        
        # Load contract
        contract_address = config.MODEL_REGISTRY_CONTRACT_ADDRESS
        with open(config.MODEL_REGISTRY_CONTRACT_ABI_PATH) as abi_file:
            contract_abi = json.load(abi_file)
        self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)

    def get_model_details(self, model_id) -> ModelDetails:
        # lowercase the model_id
        model_id = model_id.lower()
        try:
            model_details = self.contract.functions.getModelDetails(model_id).call()
            return ModelDetails(
                name=model_details[0],
                ipfs_hash=model_details[1],
            )
        except Exception as e:
            raise Exception(f"Failed to get model details: {e}")

# Create a global instance of the model registry
model_registry = ModelRegistry()
