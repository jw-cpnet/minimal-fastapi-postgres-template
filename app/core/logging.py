import logging

from fastapi.logger import logger as fastapi_logger


def setup_logging():
    logging.basicConfig(level=logging.DEBUG)
    fastapi_logger.setLevel(logging.DEBUG)

    # Create a file handler
    file_handler = logging.FileHandler("fastapi_debug.log")
    file_handler.setLevel(logging.DEBUG)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create a formatting configuration
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    fastapi_logger.addHandler(file_handler)
    fastapi_logger.addHandler(console_handler)

    # Set middleware logging level
    logging.getLogger("fastapi_keycloak_middleware").setLevel(logging.DEBUG)
