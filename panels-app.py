import datetime

import hvplot.pandas
from bokeh.server.contexts import BokehSessionContext
from dafni_cli.api.exceptions import LoginError
from dafni_cli.api.session import SessionData
from pandas import read_csv
from panel import bind, config, extension, serve, state, widgets
from panel.io.liveness import LivenessHandler

from dafni_glue import VisDAFNISession, app, dafni_template, download_to_files
from settings import (
    DATA_LOCATION,
    KEYCLOAK_SECRET,
    LOCAL_DEPLOYMENT,
    VISUALISATION_INSTANCE,
)
from visualisation import create_plot

# --- Panel code ---

extension(design="material", template="bootstrap")

# --- DAFNI Glue code ---


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
    session = VisDAFNISession(session_data=session_data)
    try:
        vis_instance = session.get_request(
            f"https://dafni-nivs-api.secure.dafni.rl.ac.uk/instances/{VISUALISATION_INSTANCE}"
        )
    except LoginError:
        return False
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


base_url = "https://keycloak.secure.dafni.rl.ac.uk/auth/realms/Production/protocol/openid-connect/"
# state.on_session_created(download_data)
config.reuse_sessions = False
config.log_level = "DEBUG"
config.authorize_callback = download_data
# done in days ~5 mins
config.oauth_expiry = 0.003
config.autoreload = True

dafni_endpoint = f"/instance/{VISUALISATION_INSTANCE}/"
dafni_redirect_uri = f"https://vis.secure.dafni.rl.ac.uk"
if LOCAL_DEPLOYMENT:
    dafni_redirect_uri = f"http://localhost:3000"

server = serve(
    dafni_template,
    prefix=dafni_endpoint,
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
    oauth_refresh_tokens=True,
    oauth_redirect_uri=f"{dafni_redirect_uri}{dafni_endpoint}",
    cookie_secret="dafni",
    websocket_origin=["localhost:3000", "vis.secure.dafni.rl.ac.uk"],
    extra_patterns=[
        (
            r"/liveness",
            LivenessHandler,
            dict(applications={dafni_endpoint: dafni_template}),
        )
    ],
)
