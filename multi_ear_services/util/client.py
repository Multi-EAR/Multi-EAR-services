import os
from influxdb_client import InfluxDBClient

__client__ = None

__location__ = os.path.realpath(os.path.join(
                   os.getcwd(),
                   os.path.dirname(__file__)
               ))


def get_client():
    """
    """
    global __client__

    if __client__ is None:
        __client__ = InfluxDBClient.from_config_file(
            os.path.join(__location__, '../uart/config.ini')
        )

    return __client__
