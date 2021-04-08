"""Configuration variables for the backend"""

import os


URL_ROOT = os.environ.get("EXPHEWAS_URL_ROOT", "/")
STATIC_FOLDER = os.environ.get("EXPHEWAS_STATIC_FOLDER")

if STATIC_FOLDER is None:
    raise RuntimeError("No static folder specified for the frontend. Use "
                       "EXPHEWAS_STATIC_FOLDER environment variable.")
