# Mandatory imports
import atexit
import logging
import numpy as np
import pandas as pd
import socket
from serial import Serial
from systemd.journal import JournaldLogHandler
from time import sleep
from argparse import ArgumentParser
from configparser import ConfigParser
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.exceptions import InfluxDBError
import influxdb_client.client.util.date_utils as date_utils
from influxdb_client.client.util.date_utils_pandas import PandasDateTimeHelper

# Relative imports
try:
    from ..version import version
except (ValueError, ModuleNotFoundError):
    version = '[VERSION-NOT-FOUND]'


__all__ = ['UART']


# Set PandasDate helper which supports nanoseconds.
date_utils.date_helper = PandasDateTimeHelper()


class UART(object):

    def __init__(self, config_file='config.ini', journald=False,
                 debug=False, dry_run=False):
        """Sensorboard serial readout via UART with data storage in a local
        Influx database.

        Configure all parameters via configuration file. The configuration file
        has to contain the sections 'influx2' and 'serial'.

        config.ini example::
            [influx2]
              url=http://localhost:8086
              org=my-org
              token=my-token
              timeout=6000
              connection_pool_maxsize=25
              auth_basic=false
              profilers=query,operator
              proxy=http:proxy.domain.org:8080
              bucket=database/retention_policy
            [tags]
              id = 132-987-655
              customer = California Miner
              data_center = ${env.data_center}
            [serial]
              port = /dev/ttyAMA0
              baudrate = 115200
              timeout = 2000
        """
        # logging
        self.__log = logging.getLogger(__name__)

        # instantiate the JournaldLogHandler to hook into systemd
        if journald:
            journald_handler = JournaldLogHandler()
            journald_handler.setFormatter(logging.Formatter(
                '[%(levelname)s] %(message)s'
            ))
            self.__log.addHandler(journald_handler)

        # set log level
        self.__log.setLevel(logging.DEBUG if debug else logging.INFO)

        # parse configuration file
        self.__config_file = config_file
        self.__config = ConfigParser()
        self.__config.read(config_file)

        # influx database connection
        self.__db_client = InfluxDBClient.from_config_file(config_file)
        self._log.info(f"Influx client = {repr(self.__db_client.health())}")
        self.__bucket = self._config_value('influx2', 'bucket')

        # influx database write api with callback to logger
        self.__callback = BatchingCallback(self._log)
        self.__write_api = self.__db_client.write_api(
            success_callback=self.__callback.success,
            error_callback=self.__callback.error,
            retry_callback=self.__callback.retry,
        )

        # uart serial port connection
        self.__serial = Serial(
            port=self._config_value('serial', 'port'),
            baudrate=int(self._config_value('serial', 'baudrate')),
            timeout=int(self._config_value('serial', 'timeout')) / 1000,  # [s]
        )
        self._log.info(f"Serial connection = {self.__serial}")

        # set options
        self.__debug = debug or False
        self.__dry_run = dry_run or False

        # configure
        self.__pck_start = b'\x11\x99\x22\x88\x33\x73'
        self.__pck_start_len = len(self.__pck_start)
        self.__pck_header_len = 11
        self.__buffer_min_len = self.__pck_start_len + 1
        self.__sampling_rate = 16  # [Hz]
        self.__delta = pd.Timedelta(1/self.__sampling_rate, 's')
        self.__measurement = 'multi_ear'
        self.__hostname = socket.gethostname()

        # init
        self.__buffer = b''
        self.__time = None
        self.__points = []

        # terminate at exit
        atexit.register(self.close)

    def close(self):
        """Close clients.
        """
        self._log.info("Shutdown clients")
        self._db_client.close()
        self._write_api.close()
        self._serial.close()

    @property
    def _bucket(self):
        return self.__bucket

    @property
    def _buffer(self):
        """Return the raw buffer sequence
        """
        return self.__buffer

    @property
    def _buffer_length(self):
        return len(self.__buffer)

    @property
    def _buffer_min_length(self):
        return self.__buffer_min_len

    def _frombuffer(self, offset=0, count=1, dtype=np.int8, like=None):
        """Return a dtype sequence from the buffer
        """
        return np.frombuffer(self._buffer, dtype, count, offset, like=like)

    @property
    def config_file(self):
        return self.__config_file

    @property
    def config(self):
        return self.__config

    def _config_value(self, sec: str, key: str):
        return self.__config[sec][key].strip('"')

    @property
    def _data_points(self):
        return self.__points

    @property
    def _db_client(self):
        return self.__db_client

    @property
    def _hostname(self):
        return self.__hostname

    @property
    def _log(self):
        return self.__log

    @property
    def _measurement(self):
        return self.__measurement

    @property
    def _packet_header_length(self):
        return self.__pck_header_len

    @property
    def _packet_start(self):
        return self.__pck_start

    @property
    def _packet_start_length(self):
        return self.__pck_start_len

    def _packet_starts(self, i):
        """Returns True if the read buffer at the given start index matches the
        packet start sequence.
        """
        return self._buffer[i:i+self.__pck_start_len] == self.__pck_start

    def _parse_buffer(self):
        """Parse the read buffer for data points.
        """

        # init packet parsing
        buffer_len = self._buffer_length
        start_len = self._packet_start_length
        header_len = self._packet_header_length
        i = 0

        # scan for packet start sequence
        while i < buffer_len - self._buffer_min_length:

            # packet header match?
            if self._packet_starts(i):

                # get packet length
                packet_len = start_len + int(self._buffer[i+start_len])

                # check buffer length
                if i + packet_len > buffer_len:
                    i += 1
                    break

                # increase local time
                self.__time += self.__delta

                # get payload length
                payload_len = int(self._buffer[i+header_len-1])

                # convert payload to point
                point = self._parse_payload(
                    i + header_len, payload_len, self.__time
                )

                # append point to data points
                self.__points.append(point)

                # shift buffer to next packet
                i += packet_len + 1

            else:
                i += 1

        self.__buffer = self.__buffer[i:]

    def _parse_payload(self, offset, length, local_time=None) -> Point:
        """Convert payload from Level-1 data to counts.
        Returns
        -------
        point : :class:`Point`
            Influx Point object with all tags, fields for the given time step.
        """
        # Get payload from buffer
        payload = self._buffer[offset:offset+length]

        # Get date, time, and cycle step from payload
        y, m, d, H, M, S, step = np.frombuffer(payload, np.uint8, 7, 0)

        # GNSS clock?
        gnss = y != 0
        if gnss:
            time = pd.Timestamp(2000 + y, m, d, H, M, S) + step * self.__delta
            clock = 'GNSS'
        else:
            time = local_time or pd.to_datetime('now')
            clock = 'local'

        # Create point
        point = (Point(self._measurement)
                 .time(time)
                 .tag('clock', clock)
                 .tag('host', self._hostname))

        # DLVR-F50D differential pressure (14-bit ADC)
        tmp = payload[7] | (payload[8] << 8)
        tmp = (tmp | 0xF000) if (tmp & 0x1000) else (tmp & 0x1FFF)
        point.field(
            'DLVR',
            np.int16(tmp)
        )

        # SP210
        point.field(
            'SP210',
            np.int16((payload[9] << 8) | payload[10])
        )

        # LPS33HW barometric pressure (24-bit)
        point.field(
            'LPS33HW',
            np.uint32(payload[11] + (payload[12] << 8) + (payload[13] << 16))
        )

        # LIS3DH 3-axis accelerometer and gyroscope (3x 16-bit)
        point.field(
            'LIS3DH_X',
            np.int16(payload[14] | (payload[15] << 8))
        )
        point.field(
            'LIS3DH_Y',
            np.int16(payload[16] | (payload[17] << 8))
        )
        point.field(
            'LIS3DH_Z',
            np.int16(payload[18] | (payload[19] << 8))
        )

        if length == 26 or length == 50:
            point.field(
                'SHT85_T',
                np.uint16((payload[20] << 8) | payload[21])
            )
            point.field(
                'SHT85_H',
                np.uint16((payload[22] << 8) | payload[23])
            )
            point.field(
                'ICS',
                np.uint16((payload[24] << 8) | payload[25])
            )
        else:
            point.field(
                'ICS',
                np.uint16((payload[20] << 8) | payload[21])
            )

        # Counts to unit conversions
        # DLVR counts_to_Pa = 0.01*250/6553
        # SP210 counts_to_Pa = 249.08/(0.9*32768)
        # LPS33HW counts_to_hPa = 1 / 4096
        # LIS3DH counts_to_ms2 = 0.076
        # SHT8x ...
        # ICS counts_to_dB = 100/4096

        # GNSS
        if gnss and length > 26:
            i = length - 24
            point.field(
                'GNSS_LAT',
                payload[i] + (payload[i+1] << 8) + (payload[i+2] << 16)
            )
            i += 3
            point.field(
                'GNSS_LON',
                payload[i] + (payload[i+1] << 8) + (payload[i+2] << 16)
            )
            i += 3
            point.field(
                'GNSS_ALT',
                payload[i] + (payload[i+1] << 8) + (payload[i+2] << 16)
            )

        return point

    def _read_lines(self):
        """Read all available lines from the serial port
        and append to the read buffer.
        """
        read = self._serial.readline()
        sleep(.2)
        in_waiting = self._serial.in_waiting
        read += self._serial.readline(in_waiting)

        self.__buffer += read

    @property
    def _points(self):
        return self.__points

    @property
    def _serial(self):
        return self.__serial

    @property
    def _write_api(self):
        return self.__write_api

    def _write_points(self, clear=True):
        """Write points to Influx database
        """
        if not self.dry_run and len(self._points) > 0:
            self._write_api.write(
                bucket=self._bucket,
                record=self._points,
            )
        if clear:
            self.__points = []

    @property
    def debug(self):
        return self.__debug

    @debug.setter
    def debug(self, debug):
        if not isinstance(debug, bool):
            raise TypeError("debug should be a of type bool")
        self.__debug = debug

    @property
    def dry_run(self):
        return self.__dry_run

    @dry_run.setter
    def dry_run(self, dry_run):
        if not isinstance(dry_run, bool):
            raise TypeError("dry_run should be a of type bool")
        self.__dry_run = dry_run

    def readout(self):
        """Contiously read UART serial data into a binary buffer, parse the
        payload and write measurements to the Influx time series database.
        """

        self._log.info("Start serial readout to influx database")

        # init
        self.__buffer = b''
        self.__points = []

        # set local time as backup if GNSS fails
        self.__time = pd.to_datetime("now")

        while self._serial.isOpen():
            self._read_lines()
            self._parse_buffer()
            self._write_points()

        self._log.info("Serial port closed")


class BatchingCallback(object):

    def __init__(self, logger):
        self.log = logger

    def success(self, conf: (str, str, str), data: str):
        """Successfully writen batch."""
        self.log.debug(f"Written batch: {conf}, data:")
        self.log.debug(f".. {d}" for d in data.split('\n'))

    def error(self, conf: (str, str, str), data: str,
              exception: InfluxDBError):
        """Unsuccessfully writen batch."""
        self.log.error("Cannot write batch: "
                       f"{conf}, due: {exception}, data:")
        self.log.debug(f".. {d}" for d in data.split('\n'))

    def retry(self, conf: (str, str, str), data: str,
              exception: InfluxDBError):
        """Retryable error."""
        self.log.error("Retryable error occurs for batch: "
                       f"{conf}, retry: {exception}, data:")
        self.log.debug(f".. {d}" for d in data.split('\n'))


def main():
    """Main script function.
    """
    # arguments
    parser = ArgumentParser(
        prog='multi-ear-uart',
        description=('Sensorboard serial readout via UART with '
                     'data storage in a local Influx database.'),
    )

    parser.add_argument(
        '-c', '--config', metavar='..', type=str, default='config.ini',
        help='Path to configuration file'
    )
    parser.add_argument(
        '-j', '--journald', action='store_true', default=False,
        help='Logging to systemd journal'
    )
    parser.add_argument(
        '--dry-run', action='store_true', default=False,
        help='UART readout without storage in the Influx database'
    )
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='Make the operation a lot more talkative'
    )

    parser.add_argument(
        '--version', action='version', version=version,
        help='Print xcorr version and exit'
    )

    args = parser.parse_args()

    uart = UART(args.config, args.journald, args.debug, args.dry_run)
    uart.readout()


if __name__ == "__main__":
    main()
