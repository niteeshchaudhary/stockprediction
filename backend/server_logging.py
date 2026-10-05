"""Configure logs even when Flask is imported by a launcher or WSGI server."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging():
    root = logging.getLogger()
    level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO)
    root.setLevel(level)
    if any(getattr(handler, '_folio', False) for handler in root.handlers):
        return
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    console = logging.StreamHandler(sys.stdout)
    console._folio = True
    console.setFormatter(formatter)
    root.addHandler(console)
    directory = Path(__file__).resolve().parent / 'logs'
    try:
        directory.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(directory / 'server.log', maxBytes=2_000_000, backupCount=3, encoding='utf-8')
        file_handler._folio = True
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        root.exception('Could not open server log file; console logging remains available')
