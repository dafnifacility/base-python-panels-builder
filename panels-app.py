import hvplot.pandas
from bokeh.server.contexts import BokehSessionContext
from pandas import read_csv
from panel import bind, config, extension, serve, state, widgets
from panel.io.liveness import LivenessHandler

from dafni_glue import (
    app,
    dafni_template,
    download_datasets_for_instance,
    get_dafni_session,
    get_vis_instance,
)
from settings import (
    BASE_KEYCLOAK_URL,
    DAFNI_ENDPOINT,
    DAFNI_REDIRECT_URI,
    DATA_LOCATION,
    KEYCLOAK_SECRET,
)
from visualisation import create_plot

# --- Panel code ---

extension(design="material", template="bootstrap")

# --- DAFNI Glue code ---


def download_data(context: BokehSessionContext):
    session = get_dafni_session(state)
    instance = get_vis_instance(session)
    dataset_uuids = download_datasets_for_instance(session, instance)
    csv_file = f"{DATA_LOCATION}{dataset_uuids[0]}/maximum-temperature-prediction.csv"
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


config.reuse_sessions = False
config.log_level = "DEBUG"
config.authorize_callback = download_data
# done in days ~5 mins
config.oauth_expiry = 0.003
config.autoreload = True

server = serve(
    dafni_template,
    prefix=DAFNI_ENDPOINT,
    title="DAFNI Visualisation",
    verbose=True,
    port=3000,
    oauth_provider="generic",
    oauth_key="dafni-main",
    oauth_secret=KEYCLOAK_SECRET,
    oauth_extra_params={
        "TOKEN_URL": f"{BASE_KEYCLOAK_URL}token",
        "AUTHORIZE_URL": f"{BASE_KEYCLOAK_URL}auth",
        "USER_URL": f"{BASE_KEYCLOAK_URL}userinfo",
    },
    oauth_refresh_tokens=True,
    oauth_redirect_uri=f"{DAFNI_REDIRECT_URI}{DAFNI_ENDPOINT}",
    cookie_secret="dafni",
    websocket_origin=["localhost:3000", "vis.secure.dafni.rl.ac.uk"],
    extra_patterns=[
        (
            r"/liveness",
            LivenessHandler,
            dict(applications={DAFNI_ENDPOINT: dafni_template}),
        )
    ],
)
