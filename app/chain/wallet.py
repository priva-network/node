from web3 import Web3
from eth_abi import encode
from eth_account.messages import encode_defunct
import logging
import json
import os

class Wallet:
    def __init__(self):
        self.account = None
        self.address = None
        self.private_key = None
        self.w3 = None

        self.config_filepath = None

    def init_config(self, config):
        self.w3 = Web3(Web3.HTTPProvider(config.ETHEREUM_NETWORK_URL))
        self.config_filepath = os.path.join(config.DATA_BASE_DIR, 'wallet.json')

        self.load_or_create_account(self.config_filepath)

    def load_or_create_account(self, config_filepath):
        """
        Load or create an Ethereum account
        """
        try:
            with open(config_filepath, 'r') as file:
                data = json.load(file)
                self.address = data['address']
                self.private_key = data['private_key']
                self.account = self.w3.eth.account.from_key(self.private_key)

            logging.info(f"Loaded account with address: {self.address}")
        except FileNotFoundError:
            account = self.w3.eth.account.create()
            self.account = account
            self.address = account.address
            self.private_key = self.w3.to_hex(account.key)
            os.umask(0o077) # Set umask to 0o077 to ensure that the file is only readable by the owner
            # make parent directories recursively if they don't exist
            os.makedirs(os.path.dirname(config_filepath), exist_ok=True)
            with open(config_filepath, 'w') as file:
                json.dump({'address': self.address, 'private_key': self.private_key}, file)

            logging.info(f"Created account with address: {self.address}")

    def sign_close_message(self, session_id, amount_paid_wei) -> bytes:
        encoded_message = encode(['uint256', 'uint256'], [session_id, amount_paid_wei])
        message_hash = Web3.keccak(encoded_message)
        message = encode_defunct(primitive=message_hash)
        signed_message = self.w3.eth.account.sign_message(message, private_key=self.private_key)

        signature = signed_message.signature.hex()
        signature_bytes = Web3.to_bytes(hexstr=signed_message.signature.hex())

        return signature, signature_bytes

# Global instance of the Wallet
wallet = Wallet()
