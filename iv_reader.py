import pandas as pd


def read_iv(path):

    data = pd.read_csv(
        path,
        sep=r"\s+"
    )

    voltage = data["voltage"].to_numpy()
    current = data["current"].to_numpy()

    return voltage, current


def read_experimental_iv(path):

    data = pd.read_csv(path)

    required = {
        "voltage",
        "current"
    }

    if not required.issubset(data.columns):
        raise ValueError(
            "experimental_iv.csv должен "
            "содержать столбцы:\n"
            "voltage,current"
        )

    voltage = data["voltage"].to_numpy()
    current = data["current"].to_numpy()

    return voltage, current