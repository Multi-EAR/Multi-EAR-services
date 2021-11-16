import numpy as np
import pandas as pd


class DataSelect(object):
    """
    DataSelect object.

    For details see the :meth:`__init__()` method.
    """

    def __init__(self, starttime=None, endtime=None, duration=None,
                 channel=None, format=None, nodata=None, autoselect=True):
        """
        Initializes a Multi-EAR DataSelect object.

        Parameters
        ----------
        starttime : str or Timestamp
            Set the start time.
        endtime : str or Timestamp
            Set the end time.
        duration : str or Timedelta
            Set the duration.
        channel : str
            Set the channel code.
        format : str
            Set the format code ("json", "csv" or "miniseed").
        nodata : int
            Set the nodata HTML status code (204 or 404).
        autoselect : bool
            Automatically selects the data from the archive.

        Example
        -------
        Create a DataSelect object without a request.
        >>> from multi_ear_services import DataSelect
        >>> q = DataSelect(..., request=False)
        """
        self.set_time(starttime, endtime, duration)
        self.channel = channel
        self.format = format
        self.nodata = nodata
        self.__data = None
        self.__select = autoselect
        if self.__select:
            self.select()

    def keys(self):
        return ['starttime', 'endtime', 'channel', 'format', 'nodata']

    def __getitem__(self, key):
        if key not in self.keys():
            raise KeyError(key)
        return eval(f"self.{key}") 

    def asdict(self):
        return {key: self[key] for key in self.keys}

    def __str__(self):
        """Print the DataSelect overview
        """
        return "<DataSelect?{}&{}&{}&{}&{}>".format(
            f"starttime={self.starttime.asm8}Z",
            f"endtime={self.endtime.asm8}Z",
            f"channel={self.channel}",
            f"format={self.format}",
            f"nodata={self.nodata}",
        )

    def _repr_pretty_(self, p, cycle):
        p.text(self.__str__())

    @property
    def duration(self):
        return self.__endtime - self.__starttime

    @property
    def start(self):
        return self.starttime

    @property
    def starttime(self):
        return self.__starttime

    @property
    def end(self):
        return self.endtime

    @property
    def endtime(self):
        return self.__endtime

    def set_time(self, start=None, end=None, delta=None):
        """Set the start and end time

        Parameters
        ----------
        start : str or Timestamp, default `None`
            Sets the dataselect start time.
        end : str or Timestamp, default 'now'
            Sets the dataselect end time.
        delta : str or Timedelta, default ‘15min’
            Sets the start time if not explicitely set.
        """
        self.__endtime = pd.to_datetime(end or 'now', unit='ns', utc=True)
        self.__starttime = (pd.to_datetime(start, unit='ns', utc=True)
                            if start is not None else
                            self.__endtime - pd.to_timedelta(delta or '15min'))

    @property
    def chan(self):
        return self.channel

    @property
    def channel(self):
        """
        """
        return self.__channel

    @channel.setter
    def channel(self, channel):
        channel = channel or '*'
        if not isinstance(channel, str):
            raise TypeError('channel code should be a string')
        self.__channel = channel 

    @property
    def format(self):
        return self.__format

    @format.setter
    def format(self, fmt):
        fmt = fmt or 'json'
        if not isinstance(fmt, str):
            raise TypeError('format code should be a string')
        if fmt not in ('json', 'csv', 'miniseed'):
            raise ValueError(
                'format code should be "json", "csv" or "miniseed"'
            )
        self.__format = fmt

    @property
    def nodata(self):
        return self.__nodata

    @nodata.setter
    def nodata(self, nodata):
        nodata = nodata or 204
        if not isinstance(nodata, int):
            raise TypeError('nodata HTTP status code should be an integer')
        if nodata not in (204, 404):
            raise ValueError(
                'nodata HTTP status code should be "204" or "404"'
            )
        self.__nodata = nodata

    def select(self):
        """
        """

    def response(self):
        """
        """
