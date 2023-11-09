from pathlib import Path

import requests
from dafni_cli.api.datasets_api import get_latest_dataset_metadata
from dafni_cli.api.exceptions import LoginError
from dafni_cli.api.session import DAFNISession, LoginError, LoginResponse, SessionData
from dafni_cli.consts import LOGIN_API_ENDPOINT, REQUESTS_TIMEOUT
from dafni_cli.datasets.dataset_download import download_dataset
from dafni_cli.datasets.dataset_metadata import DataFile
from dafni_cli.utils import dataclass_from_dict
from panel import Column, template

from settings import DATA_LOCATION

dafni_template = template.MaterialTemplate(title="DAFNI Visualisation")
dafni_template.header_background = "#000000de"
dafni_template.favicon = "static/favicon.png"
app = Column()
dafni_template.main.append(app)


class VisDAFNISession(DAFNISession):
    def _refresh_tokens(self):
        # Request a new refresh token
        response = requests.post(
            LOGIN_API_ENDPOINT,
            data={
                "client_id": "dafni-main",
                "grant_type": "refresh_token",
                "refresh_token": self._session_data.refresh_token,
            },
            timeout=REQUESTS_TIMEOUT,
        )
        if response.status_code == 400 and response.json()["error"] == "invalid_grant":
            pass
        #     # This means the refresh token has expired, so login again
        #     self.attempt_login()
        else:
            response.raise_for_status()

            login_response = dataclass_from_dict(LoginResponse, response.json())

            if not login_response.was_successful():
                raise LoginError("Unable to refresh login.")

            self._session_data = SessionData.from_login_response(
                self._session_data.username, login_response
            )

            if self._use_session_data_file:
                self._save_session_data()


def download_to_files(session: DAFNISession, dataset_uuid: str):
    dir = Path(f"{DATA_LOCATION}{dataset_uuid}")
    dataset_json = get_latest_dataset_metadata(session, dataset_uuid)
    if dir.exists():
        return
    files = [
        DataFile(
            d["spdx:fileName"],
            d["dcat:byteSize"],
            d["dcat:mediaType"],
            d["dcat:downloadURL"],
        )
        for d in dataset_json["dcat:distribution"]
    ]
    download_dataset(session, files, dir)
