from getpass import getpass
from .chain import Wallet
from config import Config
from .http import priva_api
from colorama import Fore, Style


def is_node_setup_complete(
    wallet: Wallet,
    config: Config
):
    """
    Check if the app setup is complete.
    """
    return wallet.saved_private_key_exists() and config.NODE_IP_ADDRESS is not None

def prompt_user_for_node_setup(
    wallet: Wallet,
    config: Config
):
    """
    Prompt user for how they want to configure their node.
    
    - Wallet Setup (Address and Balance Check)
    - Node Setup (Use ngrok or not, etc.) TODO: Implement this
    - TODO: any others?

    Saves config to files, and returns the config object.
    """

    if wallet.saved_private_key_exists():
        print("Node Setup Exists. Prompting to Double-Check Configuration.")
        print("")

        # Prompt user for password to decrypt the wallet
        wallet_password = getpass("Enter your password to decrypt the wallet: ")
        try:
            wallet_private_key = wallet.load_private_key_from_file(wallet_password)
        except Exception as e:
            print(f"{Fore.RED}Failed to decrypt the wallet{Style.RESET_ALL}")
            print("Exiting...")
            exit(1)
        address, private_key = wallet.setup_account_with_private_key(wallet_private_key)
        print(f"Wallet Address: {address}")
        print("")
    else:
        print("New Node Setup.")
        print("")

        # Ask user if they have an existing wallet on Base Testnet
        existing_wallet = input("Do you have an existing wallet on Base Testnet (https://sepolia.basescan.org/) that you would like to use for your Node? (y/N): ")
        if existing_wallet.lower() == "y":
            # Prompt user for the private key of the wallet
            wallet_private_key = getpass("Enter the private key of the wallet: ")

            address, private_key = wallet.setup_account_with_private_key(wallet_private_key)
            # Prompt for password to encrypt the wallet
            wallet_password = getpass("Enter a password to encrypt the wallet: ")

            # Reprompt to check password
            wallet_password_confirm = getpass("Re-enter the password to confirm: ")
            if wallet_password != wallet_password_confirm:
                print(f"{Fore.RED}Passwords do not match.{Style.RESET_ALL}")
                print("Exiting...")
                exit(1)
        else:
            # otherwise need to create a new wallet
            address, private_key = wallet.create_new_account()
            print(f"New Wallet Created. Address: {address}")
            # Prompt user for password to encrypt the wallet
            wallet_password = getpass("Enter a password to encrypt the wallet: ")
            # Reprompt to check password
            wallet_password_confirm = getpass("Re-enter the password to confirm: ")
            if wallet_password != wallet_password_confirm:
                print(f"{Fore.RED}Passwords do not match.{Style.RESET_ALL}")
                print("Exiting...")
                exit(1)
            print("")

        # Save the private key to a file
        wallet.save_private_key_to_file(wallet_password)

    # Should have at least enough ETH to register the node
    min_eth_required = 0.001 # TODO: should be dynamically determined based on gas prices
    balance = wallet.get_balance(currency='ether')
    # convert balance to float
    balance = float(balance)
    if balance < min_eth_required:
        print(f"Wallet Balance: {balance} ETH")
        print(f"Minimum Balance Required: {min_eth_required} ETH")
        print(f"{Fore.BLUE}You need at least {min_eth_required} ETH to register your node.{Style.RESET_ALL}")
        print("")

        print("You can request ETH from the Priva Network if this is a new node.")
        api_key = getpass("Enter your Priva API Key (privanetwork.xyz/api-keys) to request ETH (or Enter to skip): ")

        if api_key == "":
            print(f"{Fore.YELLOW}No API Key entered. You can manually fund your wallet by sending ETH to {address}.{Style.RESET_ALL}")
            print("Exiting...")
            exit(1)

        try:
            print(f"Requesting ETH from the Priva Network...")
            res = priva_api.request_eth(address, api_key)
            transaction_hash = res.get("transaction_hash")
            print(f"ETH Requested. Transaction Hash: {transaction_hash}")
            print("Waiting for transaction to be confirmed...")

            # Wait for the transaction to be confirmed
            wallet.wait_for_confirmations(transaction_hash)
            print("Transaction Confirmed.")
            print("")

            # Check the balance again
            balance = wallet.get_balance(currency='ether')
            print(f"New Wallet Balance: {balance}")
            # convert balance to float
            balance = float(balance)
            if balance < min_eth_required:
                print(f"Minimum ETH Required: {min_eth_required}")
                print(f"{Fore.RED}You still need at least {min_eth_required} ETH to register your node.{Style.RESET_ALL}")
                print("Exiting...")
                exit(1)

        except Exception as e:
            print(f"{Fore.RED}Failed to request ETH: {e}{Style.RESET_ALL}")
            print("Exiting...")
            exit(1)

    # Prompt for IP address
    if config.NODE_IP_ADDRESS is not None:
        # Ask if they want to keep the existing IP address
        keep_existing_ip = input(f"Your current configured network address is {config.NODE_IP_ADDRESS}. Is this correct? (Y/n): ")
        if keep_existing_ip.lower() != "y" and keep_existing_ip != "":
            ip_address = input("Enter the IP address of your Node: ")
        else:
            ip_address = config.NODE_IP_ADDRESS
    else:
        ip_address = input("Enter the network address (IP Address, Domain Name) of your Node: ")

    if ip_address is None or ip_address == "":
        print(f"{Fore.RED}IP address is required.{Style.RESET_ALL}")
        print("Exiting...")
        exit(1)

    config.set("NODE_IP_ADDRESS", ip_address, do_save=False)
    config.set("WALLET_ADDRESS", address)

    print("")
    print("Node Configuration Complete.")
    print("")

    return {
        "wallet_address": address,
        "ip_address": ip_address,
    }
