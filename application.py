from app import create_app
from config import DevelopmentConfig
import logging.config

logging.config.dictConfig(DevelopmentConfig.LOGGING_CONFIG)
app = create_app(DevelopmentConfig)
