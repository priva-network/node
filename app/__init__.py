from flask import Flask
from .storage import redis_storage
from .chain import node_registry, wallet
from config import DevelopmentConfig


def create_app(config=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config)

    from app.management.routes import management_bp
    app.register_blueprint(management_bp)
    from app.inference.routes import inference_bp
    app.register_blueprint(inference_bp)

    redis_storage.init_app(app)

    wallet.init_app(app)
    node_registry.init_app(app)

    node_registry.initialize_node('TODO_IP_ADDRESS', wallet)

    return app
