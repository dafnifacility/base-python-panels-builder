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

BASE_KEYCLOAK_URL = "https://keycloak.secure.dafni.rl.ac.uk/auth/realms/Production/protocol/openid-connect/"
DAFNI_ENDPOINT = f"/instance/{VISUALISATION_INSTANCE}/"
DAFNI_REDIRECT_URI = f"https://vis.secure.dafni.rl.ac.uk"
if LOCAL_DEPLOYMENT:
    DAFNI_REDIRECT_URI = f"http://localhost:3000"
