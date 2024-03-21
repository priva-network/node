from web3 import Web3
import logging
import json

class NodeRegistry:
    def __init__(self):
        self.w3 = None
        self.contract = None
        self.node_id = None

    def init_config(self, config):
        network_url = config.ETHEREUM_NETWORK_URL
        self.w3 = Web3(Web3.HTTPProvider(network_url))
        
        # Load contract
        contract_address = config.NODE_REGISTRY_CONTRACT_ADDRESS
        with open(config.NODE_REGISTRY_CONTRACT_ABI_PATH) as abi_file:
            contract_abi = json.load(abi_file)
        self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)

    def initialize_node(self, ip_address, wallet) -> int:
        # TODO: I should update the IP address if it's different than what's in the contract
        node_id = self._get_node_id_by_owner(wallet.address)
        if node_id == -1:
            node_id = self._register_node(ip_address, wallet)
            if node_id == -1:
                raise Exception("Failed to register compute node")
        self.node_id = node_id

        if not self._get_node_active_status(node_id):
            if not self._set_node_active_status(node_id, True, wallet):
                raise Exception("Failed to set compute node active status")

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
        
    def _get_node_active_status(self, node_id) -> bool:
        return self.contract.functions.isNodeActive(node_id).call()
        
    def _set_node_active_status(self, node_id, active, wallet):
        txn = self.contract.functions.setNodeActiveStatus(node_id, active).build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': 2000000,
            'nonce': self.w3.eth.get_transaction_count(wallet.address),
        })
        signed_txn = wallet.account.sign_transaction(txn)
        txn_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(txn_hash)

        if receipt.status != 1:
            logging.error("Failed to set node active status")
            return False

        node_status_event = self.contract.events.NodeStatusChanged().process_receipt(receipt)
        if node_status_event:
            return True
        else:
            logging.error("Failed to set node active status")
            return False

# Global instance of the ContractService
node_registry = NodeRegistry()
