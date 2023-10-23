import os

from dotenv import load_dotenv


def string_to_bool(string: str) -> bool:
    if string:
        return string.lower() in ["true", "t", "1", 1]
    return None


load_dotenv(".env")
DAFNI_USERNAME = os.getenv("DAFNI_USERNAME")
DAFNI_PASSWORD = os.getenv("DAFNI_PASSWORD")
DATA_LOCATION = os.getenv("DATA_LOCATION")
LOCAL_DEPLOYMENT = string_to_bool(os.getenv("LOCAL_DEPLOYMENT", False))
KEYCLOAK_SECRET = os.getenv("KEYCLOAK_SECRET")
VISUALISATION_INSTANCE = os.getenv("VISUALISATION_INSTANCE")
