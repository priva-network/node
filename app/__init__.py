from fastapi import FastAPI
from .storage import cache_storage, persistent_storage
from .chain import node_registry, wallet, session_manager, model_registry
from .cost import cost_calculator
from .ipfs import ipfs_node
from .models import model_storage
from config import DevelopmentConfig
from contextlib import asynccontextmanager

selected_config = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ipfs_node.init_config(selected_config)
    ipfs_client = ipfs_node.get_client()
    model_storage.init(selected_config, ipfs_client)

    # Ensure the supported models are downloaded and available
    supported_models = model_storage.get_supported_models()
    for model in supported_models:
        is_downloaded = await model_storage.is_model_downloaded(model)
        if not is_downloaded:
            await model_storage.download_model(model)
    yield

def create_app(config=DevelopmentConfig):
    global selected_config
    selected_config = config

    app = FastAPI(lifespan=lifespan)

    from app.management.routes import management_router
    app.include_router(management_router)
    from app.inference.routes import inference_router
    app.include_router(inference_router)

    cache_storage.init_config(config)
    persistent_storage.init_config(config)

    cost_calculator.init_config(config)

    wallet.init_config(config)
    node_registry.init_config(config)
    session_manager.init_config(config)
    model_registry.init_config(config)

    node_registry.initialize_node(config.NODE_IP_ADDRESS, wallet)

    return app