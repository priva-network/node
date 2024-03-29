from fastapi import FastAPI
from .storage import cache_storage, persistent_storage
from .chain import node_registry, wallet, session_manager, model_registry
from .cost import cost_calculator
from .ipfs import ipfs_node
from .models import model_storage
from .setup import prompt_user_for_node_setup, is_node_setup_complete
from config import get_config
from contextlib import asynccontextmanager
from .http import priva_api

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    await ipfs_node.init_config(config)
    ipfs_client = ipfs_node.get_client()
    model_storage.init(config, ipfs_client)

    yield # this yield is required, it basically tells it the setup is done and it can run the app
    # any cleanup code can go here (after the yield)

async def setup_app(config):
    import logging
    logger = logging.getLogger()

    if config is None:
        config = get_config()

    wallet.init_config(config)
    priva_api.init_config(config)
    prompt_user_for_node_setup(wallet, config)

    model_registry.init_config(config)
    await ipfs_node.init_config(config)
    ipfs_client = ipfs_node.get_client()
    model_storage.init(config, ipfs_client)

    # Ensure the supported models are downloaded and available
    supported_models = model_storage.get_supported_models()
    print("Setting Up Models.")
    for model in supported_models:
        is_downloaded = await model_storage.is_model_downloaded(model)
        if not is_downloaded:
            print(f"{model} model is not downloaded. Downloading now...")

            original_level = logger.getEffectiveLevel()
            logger.setLevel(logging.INFO)
            await model_storage.download_model(model)
            logger.setLevel(original_level)

    print("Model Setup Complete.")

    return

def create_app(config):
    from getpass import getpass
    import os

    if config is None:
        config = get_config()

    cache_storage.init_config(config)
    persistent_storage.init_config(config)
    cost_calculator.init_config(config)

    wallet.init_config(config)
    priva_api.init_config(config)

    # Try to get password from env variable
    wallet_password = os.getenv("WALLET_PASSWORD")
    if wallet_password is not None:
        wallet_private_key = wallet.load_private_key_from_file(wallet_password)
        wallet.setup_account_with_private_key(wallet_private_key)
    else:
        # Prompt user for password to decrypt the wallet
        wallet_password = getpass("Enter your password to decrypt the wallet: ")
        wallet_private_key = wallet.load_private_key_from_file(wallet_password)
        wallet.setup_account_with_private_key(wallet_private_key)

    if not is_node_setup_complete(wallet, config):
        from colorama import Fore, Style
        print(f"{Fore.RED}Node setup is not complete. Please run the setup command first.{Style.RESET_ALL}")

    node_registry.init_config(config)
    session_manager.init_config(config)
    model_registry.init_config(config)
    node_registry.initialize_node(config.NODE_IP_ADDRESS, wallet)

    app = FastAPI(lifespan=lifespan)
    from app.management.routes import management_router
    app.include_router(management_router)
    from app.inference.routes import inference_router
    app.include_router(inference_router)

    return app