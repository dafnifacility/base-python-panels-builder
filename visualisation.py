from numpy import abs


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
