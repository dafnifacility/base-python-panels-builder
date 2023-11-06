from pathlib import Path

from dafni_cli.api.datasets_api import get_latest_dataset_metadata
from dafni_cli.api.session import DAFNISession
from dafni_cli.datasets.dataset_download import download_dataset
from dafni_cli.datasets.dataset_metadata import DataFile

from settings import DAFNI_PASSWORD, DAFNI_USERNAME, DATA_LOCATION

session = DAFNISession.login(DAFNI_USERNAME, DAFNI_PASSWORD)

dataset_json = get_latest_dataset_metadata(
    session, "e03d4783-be48-414f-8933-8746e50a2ce7"
)

files = [
    DataFile(
        d["spdx:fileName"],
        d["dcat:byteSize"],
        d["dcat:mediaType"],
        d["dcat:downloadURL"],
    )
    for d in dataset_json["dcat:distribution"]
]

download_dataset(session, files, Path(DATA_LOCATION))
