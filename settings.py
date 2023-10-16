import os

from dotenv import load_dotenv

load_dotenv(".env")
DAFNI_USERNAME = os.getenv("DAFNI_USERNAME")
DAFNI_PASSWORD = os.getenv("DAFNI_PASSWORD")
DATA_LOCATION = os.getenv("DATA_LOCATION")
VISUALISATION_INSTANCE = os.getenv("VISUALISATION_INSTANCE")