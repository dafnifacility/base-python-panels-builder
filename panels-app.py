import datetime
from http.cookies import BaseCookie
from pathlib import Path

import hvplot.pandas
from bokeh.models import ColumnDataSource
from bokeh.server.contexts import BokehSessionContext
from dafni_cli.api.datasets_api import get_latest_dataset_metadata
from dafni_cli.api.session import DAFNISession, SessionData
from dafni_cli.datasets.dataset_download import download_dataset
from dafni_cli.datasets.dataset_metadata import DataFile
from keycloak import KeycloakOpenID
from numpy import abs
from pandas import read_csv
from panel import Column, Row, bind, extension, indicators, pane, serve, state, widgets
from panel.io.location import Location

from settings import DATA_LOCATION, KEYCLOAK_SECRET, VISUALISATION_INSTANCE

# --- Panel code ---

extension(design="material")

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


async def download_data(*args, **kwargs):
    timestamp = datetime.datetime.now() + datetime.timedelta(seconds=60)
    session_data = SessionData(
        username=state.user,
        access_token=state.access_token,
        refresh_token=state.refresh_token,
        timestamp_to_refresh=timestamp.timestamp(),
    )
    session = DAFNISession(session_data=session_data)
    vis_instance = session.get_request(
        f"https://dafni-nivs-api.secure.dafni.rl.ac.uk/instances/{VISUALISATION_INSTANCE}"
    )
    # Just doing this to get it working, obviously there's going to be a better way to do it
    dataset_uuid = None
    for dataset in vis_instance.get("visualisation_assets"):
        dataset_uuid = dataset.get("asset_id")
        download_to_files(session, dataset_uuid)

    csv_file = f"{DATA_LOCATION}{dataset_uuid}/maximum-temperature-prediction.csv"
    data = read_csv(csv_file, parse_dates=["YearMonth"], index_col="YearMonth")

    data.tail()
    create_plot(data, variable="Values", window=20, sigma=10)

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


base_url = "https://keycloak.secure.dafni.rl.ac.uk/auth/realms/Production/protocol/openid-connect/"
state.onload(download_data)
serve(
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
)
