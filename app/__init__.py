from fastapi import FastAPI
from .storage import redis_storage
from .chain import node_registry, wallet
from config import DevelopmentConfig


def create_app(config=DevelopmentConfig):
    app = FastAPI()

    from app.management.routes import management_router
    app.include_router(management_router)
    from app.inference.routes import inference_router
    app.include_router(inference_router)

    redis_storage.init_config(config)

    # wallet.init_config(config)
    # node_registry.init_config(config)

    # node_registry.initialize_node('TODO_IP_ADDRESS', wallet)

    return app
