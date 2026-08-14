"""
Módulo centralizado de logging com loguru.
- Saída colorida no console
- Arquivo de log rotativo em _temp/pipeline.log
- Contexto de tempo para medir cada etapa do pipeline
"""
import os
import sys
from loguru import logger

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "_temp"))
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")

# Garante que a pasta _temp existe
os.makedirs(LOG_DIR, exist_ok=True)

# Remove handlers padrão do loguru
logger.remove()

# Handler colorido no console
logger.add(
    sys.stdout,
    colorize=True,
    format=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
        "<level>{message}</level>"
    ),
    level="DEBUG",
)

# Handler em arquivo com rotação diária (sem cores no arquivo)
logger.add(
    LOG_FILE,
    rotation="1 day",
    retention="7 days",
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
    level="DEBUG",
    colorize=False,
)

logger.info(f"Logger inicializado. Arquivo de log: {LOG_FILE}")
