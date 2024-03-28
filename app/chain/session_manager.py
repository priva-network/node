from web3 import Web3
from .models import SessionDetails
import json

class SessionManager:
    def __init__(self):
        self.w3 = None
        self.contract = None

    def init_config(self, config):
        """
        Initialize Web3 Client and load the contract.
        """
        network_url = config.ETHEREUM_NETWORK_URL
        self.w3 = Web3(Web3.HTTPProvider(network_url))
        
        # Load contract
        contract_address = config.SESSION_MANAGER_CONTRACT_ADDRESS
        with open(config.SESSION_MANAGER_CONTRACT_ABI_PATH) as abi_file:
            contract_abi = json.load(abi_file)
        self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)

    def get_session(self, session_id) -> SessionDetails:
        session = self.contract.functions.getSessionDetails(session_id).call()
        return SessionDetails(
            id=session_id,
            start_time=session[0],
            compute_cost_limit=session[1],
            user=session[2],
            node_id=session[3],
            is_active=session[4],
            amount_paid=session[5]
        ) 

# Global instance of the SessionManager
session_manager = SessionManager()
