import hvplot.pandas
from numpy import abs
from pandas import read_csv
from panel import Column, bind, extension, widgets

from settings import DATA_LOCATION

extension(design="material")

csv_file = f"{DATA_LOCATION}maximum-temperature-prediction.csv"
data = read_csv(csv_file, parse_dates=["YearMonth"], index_col="YearMonth")

data.tail()


def transform_data(variable, window, sigma):
    """Calculates the rolling average and the outliers"""
    avg = data[variable].rolling(window=window).mean()
    residual = data[variable] - avg
    std = residual.rolling(window=window).std()
    outliers = abs(residual) > std * sigma
    return avg, avg[outliers]


def create_plot(variable="Values", window=30, sigma=10):
    """Plots the rolling average and the outliers"""
    avg, highlight = transform_data(variable, window, sigma)
    return avg.hvplot(height=300, width=400, legend=False) * highlight.hvplot.scatter(
        color="orange", padding=0.1, legend=False
    )


create_plot(variable="Values", window=20, sigma=10)

variable_widget = widgets.Select(
    name="variable", value="Values", options=list(data.columns)
)
window_widget = widgets.IntSlider(name="window", value=30, start=1, end=60)
sigma_widget = widgets.IntSlider(name="sigma", value=10, start=0, end=20)
bound_plot = bind(
    create_plot, variable=variable_widget, window=window_widget, sigma=sigma_widget
)
first_app = Column(variable_widget, window_widget, sigma_widget, bound_plot)

first_app.servable()
