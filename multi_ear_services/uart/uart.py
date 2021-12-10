# Mandatory imports
import atexit
import gc
import logging
import numpy as np
import os
import pandas as pd
import socket
import sys
from argparse import ArgumentParser
from configparser import ConfigParser
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import WriteOptions
from influxdb_client.client.exceptions import InfluxDBError
import influxdb_client.client.util.date_utils as date_utils
from influxdb_client.client.util.date_utils_pandas import PandasDateTimeHelper
from serial import Serial
from systemd.journal import JournaldLogHandler
from time import sleep

# Relative imports
try:
    from ..version import version
except (ValueError, ModuleNotFoundError):
    version = 'VERSION-NOT-FOUND'


__all__ = ['UART']


# Set PandasDate helper which supports nanoseconds.
date_utils.date_helper = PandasDateTimeHelper()

# Force garbage collections
gc.enable()


class UART(object):
    _buffer = b''
    _points = []
    _uart = None
    _time = None

    def __init__(self, config_file='config.ini', journald=False,
                 debug=False, dry_run=False, local_clock=False) -> None:
        """Sensorboard serial readout with data storage in a local influx
        database.

        Configure all parameters via configuration file. The configuration file
        has to contain the sections 'influx2' and 'serial'.

        config.ini example::
            [influx2]
              url = http://localhost:8086
              org = -
              token = my-token
              bucket = multi_ear
              measurement = multi_ear
              batch_size = 250
            [serial]
              port = /dev/ttyAMA0
              baudrate = 115200
              timeout = 2000
            [tags]
               uuid = %(MULTI_EAR_UUID)s
        """

        # set options
        self.dry_run = dry_run or False
        self.local_clock = local_clock or False

        # set logger
        self._logger = logging.getLogger(__name__)

        # log to systemd or stdout
        if journald:
            journaldHandler = JournaldLogHandler()
            journaldHandler.setFormatter(logging.Formatter(
                '[%(levelname)s] %(message)s'
            ))
            self._logger.addHandler(journaldHandler)
        else:
            streamHandler = logging.StreamHandler(sys.stdout)
            streamHandler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self._logger.addHandler(streamHandler)

        # set log level
        self._logger.setLevel(logging.DEBUG if debug else logging.INFO)

        # configuration defaults
        self._serial_port = '/dev/ttyAMA0'
        self._serial_baudrate = 115_200
        self._serial_timeout = 2_000
        self._influx2_url = 'http://127.0.0.1:8086'
        self._influx2_org = '-'
        self._influx2_token = ':'
        self._influx2_timeout = 10_000
        self._influx2_auth_basic = False
        self._influx2_bucket = 'multi_ear/'
        self._batch_size = 250
        self._measurement = 'multi_ear'
        self._host = socket.gethostname()
        self._uuid = 'null'
        self._version = version.replace('VERSION-NOT-FOUND', 'null')
        self._packet_start = b'\x11\x99\x22\x88\x33\x73'
        self._packet_start_len = len(self._packet_start)
        self._packet_header_len = 11
        self._buffer_min_len = self._packet_start_len + 1
        self._sampling_rate = 16  # [Hz]
        self._delta = pd.Timedelta(1/self._sampling_rate, 's')

        # parse configuration file
        if not os.path.exists(config_file):
            raise FileNotFoundError(config_file)

        config = ConfigParser(os.environ)
        config.read(config_file)

        def config_getstr(*args, **kwargs):
            value = config.get(*args, **kwargs)
            return value.strip('"') if value is not None else None
        config.getstr = config_getstr

        self._serial_port = config.getstr(
            'serial', 'port', fallback=self._serial_port
        )
        self._serial_baudrate = config.getint(
            'serial', 'baudrate', fallback=self._serial_baudrate
        )
        self._serial_timeout = config.getint(
            'serial', 'timeout', fallback=self._serial_timeout
        )
        self._influx2_url = config.getstr(
            'influx2', 'url', fallback=self._influx2_url
        )
        self._influx2_org = config.getstr(
            'influx2', 'org', fallback=self._influx2_org
        )
        self._influx2_token = config.getstr(
            'influx2', 'token', fallback=self._influx2_token
        )
        self._influx2_timeout = config.getint(
            'influx2', 'timeout', fallback=self._influx2_timeout
        )
        self._influx2_auth_basic = config.getboolean(
            'influx2', 'auth_basic', fallback=self._influx2_auth_basic
        )
        self._influx2_bucket = config.getstr(
            'influx2', 'bucket', fallback=self._influx2_bucket
        )
        self._batch_size = config.getint(
            'influx2', 'batch_size', fallback=self._batch_size
        )
        self._measurement = config.getstr(
            'influx2', 'measurement', fallback=self._measurement
        )
        self._host = config.getstr(
            'tags', 'host', fallback=self._host
        )
        self._uuid = config.getstr(
            'tags', 'uuid', fallback=self._uuid
        )

        # connect to serial port
        self._uart = Serial(
            port=self._serial_port,
            baudrate=self._serial_baudrate,
            timeout=self._serial_timeout / 1000,  # [s]
        )
        self._logger.info(f"Serial connection = {self._uart}")

        # connect to influxdb
        self._db = InfluxDBClient(
           url=self._influx2_url,
           org=self._influx2_org,
           token=self._influx2_url,
           timeout=self._influx2_timeout,
           auth_basic=self._influx2_auth_basic,
        )
        self._logger.info(f"Influxdb connection = {self._db.ping()}")

        self._write_options = WriteOptions(
            batch_size=self._batch_size*2,
            flush_interval=1_000,
            jitter_interval=2_000,
            retry_interval=5_000,
            max_retries=5,
            max_retry_delay=30_000,
            exponential_base=2
        )

        # terminate at exit
        atexit.register(self.close)

    def close(self):
        self._logger.info("Close serial port and influxdb client")
        self.__del__()

    def __del__(self):
        if self._uart is not None:
            self._uart.close()
        if self._db is not None:
            self._db.close()
        pass

    @property
    def _buffer_len(self):
        return len(self._buffer)

    def _frombuffer(self, offset=0, count=1, dtype=np.int8, like=None):
        """Return a dtype sequence from the buffer
        """
        return np.frombuffer(self._buffer, dtype, count, offset, like=like)

    def _packet_starts(self, i):
        """Returns True if the read buffer at the given start index matches the
        packet start sequence.
        """
        return self._buffer[i:i+self._packet_start_len] == self._packet_start

    def _parse_buffer(self):
        """Parse the read buffer for data points.
        """

        # init packet parsing
        buffer_len = self._buffer_len
        header_len = self._packet_header_len
        i = 0

        # scan for packet start sequence
        while i < buffer_len - self._buffer_min_len:

            # packet header match?
            if self._packet_starts(i):

                # get packet length
                packet_len = (self._packet_start_len +
                              int(self._buffer[i+self._packet_start_len]))

                # check buffer length
                if i + packet_len > buffer_len:
                    i += 1
                    break

                # hard debug
                # self._logger.info(
                #     np.frombuffer(self._buffer, np.uint8, packet_len, i)
                # )

                # increase local time
                self._time += self._delta

                # get payload length
                payload_len = int(self._buffer[i+header_len-1])

                # convert payload to point
                point = self._parse_payload(
                    i + header_len, payload_len, self._time
                )

                # append point to data points
                self._points.append(point)

                # shift buffer to next packet
                i += packet_len + 1

            else:
                i += 1

        self._buffer = self._buffer[i:]

    def _parse_payload(self, offset, length, local_time=None) -> Point:
        """Convert payload from Level-1 data to counts.
        Returns
        -------
        point : :class:`Point`
            Influx Point object with all tags, fields for the given time step.
        """
        # Get payload from buffer
        payload = self._buffer[offset:offset+length]
        # self._logger.info(np.frombuffer(payload, np.uint8))

        # Get date, time, and cycle step from payload
        y, m, d, H, M, S, step = np.frombuffer(payload, np.uint8, 7, 0)
        # self._logger.info(f'payload time: {y} {m} {d} {H} {M} {S} {step}')

        # GNSS clock?
        gnss = False if self.local_clock else y != 0
        if gnss:
            time = pd.Timestamp(2000 + y, m, d, H, M, S) + step * self._delta
            clock = 'GNSS'
        else:
            time = local_time or pd.to_datetime('now')
            clock = 'local'
        # self._logger.info(f'{clock} time: {time}')

        # Create point
        point = (Point(self._measurement)
                 .time(time)
                 .tag('clock', clock)
                 .tag('host', self._host)
                 .tag('uuid', self._uuid)
                 .tag('version', self._version))

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

        self._logger.debug(f"Read point: {point.to_line_protocol()}")

        return point

    def _read_lines(self):
        """Read all available lines from the serial port
        and append to the read buffer.
        """
        read = self._uart.readline()
        sleep(.2)
        in_waiting = self._uart.in_waiting
        read += self._uart.readline(in_waiting)

        self._buffer += read

    def _clear_points(self):
        self._points = []
        gc.collect()

    def _write_points(self):
        """Write points to Influx database
        """

        if len(self._points) < self._batch_size:
            return

        if not self.dry_run and len(self._points) > 0:

            with self._db.write_api(
                write_options=self._write_options,
                success_callback=self._write_success,
                error_callback=self._write_error,
                retry_callback=self._write_retry,
            ) as writer:
                writer.write(
                    bucket=self._influx2_bucket,
                    record=self._points
                )

        self._clear_points()

    def _write_success(self, conf: (str, str, str), data: str):
        """Successfully writen batch."""
        self._logger.info(
            f"Written batch: {conf}, "
            f"last time record {pd.Timestamp(int(data[-19:]))}"
        )
        self._logger.debug(
            f"Written batch: {conf}, data: {data}"
        )

    def _write_error(self, conf: (str, str, str), data: str,
                     exception: InfluxDBError):
        """Unsuccessfully writen batch."""
        self._logger.error(
            "Cannot write batch: "
            f"{conf}, data: {data} due: {exception}"
        )

    def _write_retry(self, conf: (str, str, str), data: str,
                     exception: InfluxDBError):
        """Retryable error."""
        self._logger.error(
            "Retryable error occurs for batch: "
            f"{conf}, data: {data} retry: {exception}"
        )

    def readout(self):
        """Contiously read UART serial data into a binary buffer, parse the
        payload and write measurements to the Influx time series database.
        """

        self._logger.info("Start serial readout to influx database")

        # init
        self._buffer = b''
        self._points = []

        # set local time as backup if GNSS fails
        self._time = pd.to_datetime("now")

        while self._uart.isOpen():
            self._read_lines()
            self._parse_buffer()
            self._write_points()

        self._logger.info("Serial port closed")


def main():
    """Main script function.
    """
    # arguments
    parser = ArgumentParser(
        prog='multi-ear-uart',
        description=('Sensorboard serial readout with data storage'
                     'in a local influx database.'),
    )

    parser.add_argument(
        '-i', '--ini', metavar='..', type=str, default='config.ini',
        help='Path to configuration file'
    )
    parser.add_argument(
        '-j', '--journald', action='store_true', default=False,
        help='Log to systemd journal'
    )
    parser.add_argument(
        '--dry-run', action='store_true', default=False,
        help='Serial read without storage in the influx database'
    )
    parser.add_argument(
        '--local-clock', action='store_true', default=False,
        help='Disable GNSS time (if available) and use the local time only.'
    )
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help='Make the operation a lot more talkative'
    )

    parser.add_argument(
        '--version', action='version', version=version,
        help='Print the version and exit'
    )

    args = parser.parse_args()

    uart = UART(
        config_file=args.ini,
        journald=args.journald,
        debug=args.debug,
        dry_run=args.dry_run,
        local_clock=args.local_clock
    )
    uart.readout()


if __name__ == "__main__":
    main()
