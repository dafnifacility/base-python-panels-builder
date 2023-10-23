import datetime
from pathlib import Path

import hvplot.pandas
import requests
from bokeh.server.contexts import BokehSessionContext
from dafni_cli.api.datasets_api import get_latest_dataset_metadata
from dafni_cli.api.exceptions import LoginError
from dafni_cli.api.session import DAFNISession, LoginError, LoginResponse, SessionData
from dafni_cli.consts import LOGIN_API_ENDPOINT, REQUESTS_TIMEOUT
from dafni_cli.datasets.dataset_download import download_dataset
from dafni_cli.datasets.dataset_metadata import DataFile
from dafni_cli.utils import dataclass_from_dict
from numpy import abs
from pandas import read_csv
from panel import Column, bind, config, extension, indicators, serve, state, widgets
from panel.io.liveness import LivenessHandler

from settings import DATA_LOCATION, KEYCLOAK_SECRET, VISUALISATION_INSTANCE

# --- Panel code ---

extension(design="material", loading_indicator=True, template="bootstrap")

loading = indicators.LoadingSpinner(value=True, size=20, name="Downloading data...")
app = Column(loading)


def transform_data(data, variable, window, sigma):
    """Calculates the rolling average and the outliers"""
    avg = data[variable].rolling(window=window).mean()
    residual = data[variable] - avg
    std = residual.rolling(window=window).std()
    outliers = abs(residual) > std * sigma
    return avg, avg[outliers]


def create_plot(data, variable="Values", window=30, sigma=10):
    """Plots the rolling average and the outliers"""
    avg, highlight = transform_data(data, variable, window, sigma)
    return avg.hvplot(height=300, width=400, legend=False) * highlight.hvplot.scatter(
        color="orange", padding=0.1, legend=False
    )


# --- DAFNI code ---


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
        print(self._session_data.refresh_token)
        print(response.raw)
        if response.status_code == 400 and response.json()["error"] == "invalid_grant":
            print("No")
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


def download_data(context: BokehSessionContext):
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
    print("user???", state.user)
    print("cookies ???", state.cookies)
    print("REFRESH???", state.refresh_token)
    session = VisDAFNISession(session_data=session_data)
    try:
        vis_instance = session.get_request(
            f"https://dafni-nivs-api.secure.dafni.rl.ac.uk/instances/{VISUALISATION_INSTANCE}"
        )
    except LoginError:
        return False
    print("Hello", vis_instance)
    # Just doing this to get it working, obviously there's going to be a better way to do it
    dataset_uuid = None
    for dataset in vis_instance.get("visualisation_assets"):
        dataset_uuid = dataset.get("asset_id")
        download_to_files(session, dataset_uuid)

    csv_file = f"{DATA_LOCATION}{dataset_uuid}/maximum-temperature-prediction.csv"
    data = read_csv(csv_file, parse_dates=["YearMonth"], index_col="YearMonth")

    data.tail()
    variable_widget = widgets.Select(
        name="variable", value="Values", options=list(data.columns)
    )
    window_widget = widgets.IntSlider(name="window", value=30, start=1, end=60)
    sigma_widget = widgets.IntSlider(name="sigma", value=10, start=0, end=20)
    bound_plot = bind(
        create_plot,
        data=data,
        variable=variable_widget,
        window=window_widget,
        sigma=sigma_widget,
    )
    app.objects = [variable_widget, window_widget, sigma_widget, bound_plot]
    return True


def add_load(context, *args, **kwargs):
    state.onload(download_data, context)


def logout(*args, **kwargs):
    state.clear_caches()


base_url = "https://keycloak.secure.dafni.rl.ac.uk/auth/realms/Production/protocol/openid-connect/"
# state.on_session_created(download_data)
config.reuse_sessions = False
config.log_level = "INFO"
config.authorize_callback = download_data

server = serve(
    {f"{VISUALISATION_INSTANCE}": app},
    title="DAFNI Visualisation",
    verbose=True,
    port=3000,
    oauth_provider="generic",
    oauth_key="dafni-main",
    oauth_secret=KEYCLOAK_SECRET,
    oauth_extra_params={
        "TOKEN_URL": f"{base_url}token",
        "AUTHORIZE_URL": f"{base_url}auth",
        "USER_URL": f"{base_url}userinfo",
    },
    cookie_secret="dafni",
    # done in days ~5 mins
    oauth_expiry=0.003,
    extra_patterns=[
        (
            r"/liveness",
            LivenessHandler,
            dict(applications={f"{VISUALISATION_INSTANCE}": app}),
        )
    ],
)
