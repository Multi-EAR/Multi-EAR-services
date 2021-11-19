import traceback as tb
import pandas as pd
from flask import Response
from influxdb_client import InfluxDBClient


__all__ = ['DataSelect']


class DataSelect(object):
    """
    DataSelect object.

    For details see the :meth:`__init__()` method.
    """

    def __init__(self, client, starttime=None, endtime=None, duration=None,
                 field=None, measurement=None, bucket=None, database=None,
                 retention_policy=None, format=None, nodata=None, query=True):
        """
        Initializes a Multi-EAR DataSelect object.

        Parameters
        ----------
        client : InfluxDBClient
            Set the InfluxDB client and corresponding query api.
        starttime : str or Timestamp
            Set the start time.
        endtime : str or Timestamp
            Set the end time.
        duration : str or Timedelta
            Set the duration.
        field : str
            Set the field code.
        measurement : str
            Set the measurement code.
        bucket : str
            Set the bucket code.
        database : str
            Set the database.
        retention_policy : str
            Set the retention policy.
        format : str
            Set the format code ("json", "csv" or "miniseed").
        nodata : int
            Set the nodata HTML status code (204 or 404).
        query : bool
            Process the query (default: `True`).

        Example
        -------
        Create a DataSelect object without a request.
        >>> from multi_ear_services import DataSelect
        >>> q = DataSelect(..., request=False)
        """

        if not isinstance(client, InfluxDBClient):
            raise TypeError('InfluxDBClient should be set')

        self.__db_client__ = client
        self.__query_api__ = client.query_api()
        self.__status__ = 100
        self.__error__ = None
        self.__df__ = None

        self.set_time(starttime, endtime, duration)
        self.field = field
        self.measurement = measurement
        if bucket is not None:
            database, retention_policy = bucket.split('/')
        self.database = database
        self.retention_policy = retention_policy
        self.format = format
        self.nodata = nodata
        if query:
            self.query()

    def keys(self):
        """DataSelect object dictionary keys.
        """
        return ['starttime', 'endtime', 'field', 'format', 'nodata']

    def __getitem__(self, key):
        """DataSelect object dictionary key selector.
        """
        if key not in self.keys():
            raise KeyError(key)
        return eval(f"self.{key}")

    def asdict(self):
        """Returns the DataSelect object as a dictionary.
        """
        return {key: self[key] for key in self.keys}

    def __str__(self):
        """Print the DataSelect query
        """
        return "<DataSelect/query?{}&{}&{}&{}&{}>".format(
            f"starttime={self.starttime.asm8}Z",
            f"endtime={self.endtime.asm8}Z",
            f"field={self.field}",
            f"format={self.format}",
            f"nodata={self.nodata}",
        )

    def _repr_pretty_(self, p, cycle):
        p.text(self.__str__())

    @property
    def duration(self):
        """DataSelect time duration.
        """
        return self.__endtime__ - self.__starttime__

    @property
    def start(self):
        """DataSelect start time.
        """
        return self.starttime

    @property
    def starttime(self):
        """DataSelect start time.
        """
        return self.__starttime__

    @property
    def end(self):
        """DataSelect end time.
        """
        return self.endtime

    @property
    def endtime(self):
        """DataSelect end time.
        """
        return self.__endtime__

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
        self.__endtime__ = pd.to_datetime(end or 'now', unit='ns', utc=True)
        if start is None:
            delta = pd.to_timedelta(delta or '15min')
            self.__starttime__ = self.__endtime__ - delta
        else:
            self.__starttime__ = pd.to_datetime(start, unit='ns', utc=True)

    @property
    def field(self):
        """DataSelect field code (default: '*')
        """
        return self.__field__

    @field.setter
    def field(self, field):
        field = field or '*'
        if not isinstance(field, str):
            raise TypeError('field code should be a string')
        self.__field__ = field

    @property
    def measurement(self):
        """DataSelect measurement code (default: '*')
        """
        return self.__measurement__

    @measurement.setter
    def measurement(self, measurement):
        measurement = measurement or '*'
        if not isinstance(measurement, str):
            raise TypeError('measurement code should be a string')
        self.__measurement__ = measurement

    @property
    def bucket(self):
        """DataSelect bucket code of format 'database/retention_policy'
        """
        return f"{self.__database__}/{self.__retention_policy__}"

    @bucket.setter
    def bucket(self, bucket):
        bucket = bucket or 'telegraf/'
        if not isinstance(bucket, str):
            raise TypeError('bucket code should be a string')
        if '/' not in bucket:
            raise ValueError('bucket code should be of format '
                             '"database/retention_policy"')
        self.__database__, self.__retenion_policy__ = bucket.split('/')

    @property
    def database(self):
        """DataSelect database (default: 'telegraf')
        """
        return self.__database__

    @database.setter
    def database(self, database):
        database = database or 'telegraf'
        if not isinstance(database, str):
            raise TypeError('database code should be a string')
        self.__database__ = database

    @property
    def retention_policy(self):
        """DataSelect retention_policy code (default: '')
        """
        return self.__retention_policy__

    @retention_policy.setter
    def retention_policy(self, retention_policy):
        retention_policy = retention_policy or ''
        if not isinstance(retention_policy, str):
            raise TypeError('retention_policy code should be a string')
        self.__retention_policy__ = retention_policy

    @property
    def format(self):
        """DataSelect format code {json|csv|miniseed} (default: 'json').
        """
        return self.__format__

    @format.setter
    def format(self, fmt):
        fmt = fmt or 'json'
        if not isinstance(fmt, str):
            raise TypeError('format code should be a string')
        fmt = fmt.lower()
        if fmt not in ('json', 'csv', 'miniseed'):
            raise ValueError('format code should be {json|csv|miniseed}')
        self.__format__ = fmt

        if fmt == 'csv':
            self.__mimetype__ = 'text/csv'
        if fmt == 'json':
            self.__mimetype__ = 'application/json'
        if fmt == 'miniseed':
            self.__mimetype__ = 'application/octet-stream'

    @property
    def nodata(self):
        """DataSelect nodata HTTP status code
        """
        return self.__nodata__

    @nodata.setter
    def nodata(self, nodata):
        nodata = nodata or 204
        if not isinstance(nodata, int):
            raise TypeError('nodata HTTP status code should be an integer')
        if nodata not in (204, 404):
            raise ValueError(
                'nodata HTTP status code should be "204" or "404"'
            )
        self.__nodata__ = nodata

    @property
    def _client(self):
        """Returns the InfluxDB client
        """
        return self.__db_client__

    @property
    def _query_api(self):
        """Returns the InfluxDB query api
        """
        return self.__query_api__

    @property
    def _q(self):
        """Returns the Flux query string
        """

        # Query InfluxDB using Flux
        # https://docs.influxdata.com/flux/v0.x/query-data/influxdb/

        q = 'from(bucket: "{}")'.format(self.bucket)

        q += '|> range(start: {}Z, stop: {}Z)'.format(self.start.asm8,
                                                      self.end.asm8)

        if self.measurement != '*':
            _filter = f'r["_measurement"] == "{self.measurement}"'
            if self.field != '*':
                _filter += f' and r["_field"] == "{self.field}"'
            q += '|> filter(fn: (r) => {})'.format(_filter)

        q += ('|> pivot('
              'rowKey:["_time"], '
              'columnKey: ["_measurement", "_field"], '
              'valueColumn: "_value")')

        q += '|> drop(columns: ["_start", "_stop", "host"])'

        return q

    def query(self):
        """Process the DataSelect request.
        """
        try:
            self.__df__ = self._query_api.query_data_frame(self._q)
            if self._df.size == 0:
                self.__status__ = self.nodata
            else:
                self.__status__ = 200
                self.__df__ = (self.__df__
                               .drop(['result', 'table'], axis=1)
                               .set_index('_time'))
        except Exception as e:
            self.__error__ = "Server Error: {}\n{}".format(
                repr(e), ''.join(tb.format_exception(None, e, e.__traceback__))
            )
            self.__status__ = 500

    @property
    def _df(self):
        """Returns the DataSelect query DataFrame.
        """
        return self.__df__

    def _to_format(self):
        """Returns the DataSelect request as self.format.
        """
        if self._status == 100:
            self.query()
        if self._status == 500:
            return self._error
        try:
            print(f"self._to_{self.__format__}()")
            resp = eval(f"self._to_{self.__format__}()")
        except Exception as e:
            self.__error__ = "Server Error: {}\n{}".format(
                repr(e), ''.join(tb.format_exception(None, e, e.__traceback__))
            )
            self.__status__ = 500
        return resp if self._status == 200 else self._error

    def _to_json(self):
        """Returns the DataSelect request as json.
        """
        if self._status == 100:
            self.query()
        return self._df.to_json(orient='split', date_format='iso', indent=4)

    def _to_csv(self):
        """Returns the DataSelect request as csv.
        """
        if self._status == 100:
            self.query()
        return self._df.to_csv(date_format='iso')

    def _to_miniseed(self):
        """Returns the DataSelect request as miniseed.
        """
        if self._status == 100:
            self.query()
        return self._df.to_string()

    @property
    def _status(self):
        """Returns the HTTP status code (int).
        """
        return self.__status__

    @property
    def _mimetype(self):
        """Returns the HTTP mimetype.
        """
        return self.__mimetype__ or 'text/plain'

    @property
    def _error(self):
        """Returns the HTTP status code (int).
        """
        return self.__error__

    def response(self):
        """Return the DataSelect query response.
        """
        return Response(
            response=self._to_format(),
            status=self._status,
            mimetype=self._mimetype,
            headers={"Access-Control-Allow-Methods", "GET",
                     "Access-Control-Allow-Origin": "*"},
        )
