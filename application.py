from app import create_app
from config import DevelopmentConfig, ProductionConfig
import logging.config
import os

cfg = DevelopmentConfig
if os.environ.get('CORTEX_ENV') == 'production':
    cfg = ProductionConfig

logging.config.dictConfig(cfg.LOGGING_CONFIG)
app = create_app(cfg)
