import logging.config
from pathlib import Path


def configure_logging():
    # from app import settings  # Avoid circular import

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            },
            "file": {
                "format": "[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "DEBUG",
            },
            "file_debug": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_dir / "debug.log"),
                "maxBytes": 1024 * 1024 * 5,
                "backupCount": 3,
                "formatter": "file",
                "level": "DEBUG",
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_dir / "error.log"),
                "maxBytes": 1024 * 1024 * 5,
                "backupCount": 3,
                "formatter": "file",
                "level": "ERROR",
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file_debug", "file_error"],
        },
        "loggers": {
            "": {  # Root logger
                "level": "DEBUG",
                "handlers": ["console", "file_debug", "file_error"],
            },
            "tortoise": {"level": "WARNING"},
            "aiosqlite": {"level": "WARNING"},
            "uvicorn": {"level": "INFO", "propagate": False},
            "uvicorn.error": {
                "level": "DEBUG",
                "handlers": ["console", "file_debug", "file_error"],
                "propagate": False,
            },
            "uvicorn.access": {"level": "WARNING", "propagate": False},
            "starlette": {
                "level": "WARNING",
                "handlers": ["console", "file_debug", "file_error"],
                "propagate": False,
            },
            "jinja2": {
                "level": "ERROR",
                "handlers": ["console", "file_debug", "file_error"],
                "propagate": False,
            },
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file_debug", "file_error"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)
