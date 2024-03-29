from web3 import Web3
from .models import NodeDetails
import logging
import json

class NodeRegistry:
    def __init__(self):
        self.w3 = None
        self.contract = None
        self.node_id = None

    def init_config(self, config):
        """
        Initialize Web3 Client and load the contract.
        """
        network_url = config.ETHEREUM_NETWORK_URL
        self.w3 = Web3(Web3.HTTPProvider(network_url))
        
        # Load contract
        contract_address = config.NODE_REGISTRY_CONTRACT_ADDRESS
        with open(config.NODE_REGISTRY_CONTRACT_ABI_PATH) as abi_file:
            contract_abi = json.load(abi_file)
        self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)

    def initialize_node(self, ip_address, wallet) -> int:
        """
        Registers compute node if not already registered and sets the node active status.
        """
        node_id = self._get_node_id_by_owner(wallet.address)
        if node_id == -1:
            node_id = self._register_node(ip_address, wallet)
            if node_id == -1:
                raise Exception("Failed to register compute node")
        self.node_id = node_id

        details = self._get_node_details(node_id)
        if details.ip_address != ip_address:
            if not self._set_node_ip_address(node_id, ip_address, wallet):
                raise Exception("Failed to set compute node IP address")

        return node_id

    def _get_node_id_by_owner(self, owner) -> int:
        node_id = self.contract.functions.getNodeIdByOwner(owner).call()
        if node_id == 0:
            logging.debug("No node found for owner")
            return -1
        
        logging.info(f"Found compute node with id: {node_id}")
        return node_id

    def _register_node(self, ip_address, wallet) -> int:
        txn = self.contract.functions.registerNode(ip_address, wallet.address).build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': 2000000,
            'nonce': self.w3.eth.get_transaction_count(wallet.address),
        })
        signed_txn = wallet.account.sign_transaction(txn)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(txn_hash)

        if receipt.status != 1:
            logging.error("Failed to register compute node")
            return -1

        # Assuming node_registry is already defined and contains the ABI
        node_registered_event = self.contract.events.NodeRegistered().process_receipt(receipt)
        if node_registered_event:
            # Extract the nodeId from the first (and should be only) event
            node_id = node_registered_event[0]['args']['nodeId']
            logging.info(f"Registered compute node with id: {node_id}")
            return node_id
        else:
            logging.error("Failed to register compute node")
            return -1
    
    def _get_node_details(self, node_id) -> NodeDetails:
        details = self.contract.functions.getNodeDetails(node_id).call()
        return NodeDetails(
            id=node_id,
            ip_address=details[0],
            owner=details[1]
        )

    def _set_node_ip_address(self, node_id, ip_address, wallet):
        txn = self.contract.functions.setNodeIPAddress(node_id, ip_address).build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': 2000000,
            'nonce': self.w3.eth.get_transaction_count(wallet.address),
        })
        signed_txn = wallet.account.sign_transaction(txn)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(txn_hash)

        if receipt.status != 1:
            logging.error("Failed to set node IP address")
            return False

        node_ip_address_event = self.contract.events.NodeIPAddressUpdated().process_receipt(receipt)
        if node_ip_address_event:
            return True
        else:
            logging.error("Failed to set node IP address")
            return False

# Global instance of the ContractService
node_registry = NodeRegistry()
