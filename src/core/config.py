import os
from logging import config as logging_config

from src.core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = os.getenv('PROJECT_NAME', 'Besmedia Web')

# Настройки Redis
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Настройки Elasticsearch
# ELASTIC_HOST = os.getenv('ELASTIC_HOST', '127.0.0.1')
# ELASTIC_PORT = int(os.getenv('ELASTIC_PORT', 9200))

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = os.getenv('DATABASE_URL', os.getenv('ASYNC_DATABASE_URL', 'postgresql+asyncpg://user:password@localhost:5454/db'))
API_RPC_HOST = os.getenv('API_RPC_HOST', "")

ELASTIC_HOST = os.getenv('ELASTIC_HOST', 'elasticsearch')
ELASTIC_PORT = int(os.getenv('ELASTIC_PORT', 9200))
ELASTIC_URL = f'http://{ELASTIC_HOST}:{ELASTIC_PORT}/'