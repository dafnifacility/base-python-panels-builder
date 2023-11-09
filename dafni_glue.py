import datetime
from pathlib import Path

import requests
from dafni_cli.api.datasets_api import get_latest_dataset_metadata
from dafni_cli.api.exceptions import LoginError
from dafni_cli.api.session import DAFNISession, LoginError, LoginResponse, SessionData
from dafni_cli.consts import LOGIN_API_ENDPOINT, REQUESTS_TIMEOUT
from dafni_cli.datasets.dataset_download import download_dataset
from dafni_cli.datasets.dataset_metadata import DataFile
from dafni_cli.utils import dataclass_from_dict
from panel import Column, state, template

from settings import DATA_LOCATION, VISUALISATION_INSTANCE

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


def get_dafni_session(state: state) -> VisDAFNISession:
    if state.location.pathname == "healthz" or state.location.pathname == "liveness":
        return True
    if state.user == "testadmin@example.com":
        # This seems to be default value from panel
        return False
    timestamp = datetime.datetime.now() + datetime.timedelta(seconds=60)
    session_data = SessionData(
        username=state.user,
        access_token=state.access_token,
        refresh_token=state.refresh_token,
        timestamp_to_refresh=timestamp.timestamp(),
    )
    return VisDAFNISession(session_data=session_data)


def get_vis_instance(session: VisDAFNISession):
    try:
        return session.get_request(
            f"https://dafni-nivs-api.secure.dafni.rl.ac.uk/instances/{VISUALISATION_INSTANCE}"
        )
    except LoginError:
        return False


def download_files_from_dataset(session: VisDAFNISession, dataset_uuid: str):
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


def download_datasets_for_instance(
    session: VisDAFNISession, instance: dict[str, dict]
) -> None:
    dataset_uuid = None
    for dataset in instance.get("visualisation_assets"):
        dataset_uuid = dataset.get("asset_id")
        download_files_from_dataset(session, dataset_uuid)
        yield dataset
