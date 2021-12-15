# Mandatory imports
import atexit
import logging
import numpy as np
import os
import pandas as pd
import sys
import threading
from queue import Queue
from argparse import ArgumentParser
from configparser import ConfigParser
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.exceptions import InfluxDBError
import influxdb_client.client.util.date_utils as date_utils
from influxdb_client.client.util.date_utils_pandas import PandasDateTimeHelper
from serial import Serial
from socket import gethostname
from systemd.journal import JournaldLogHandler

# Relative imports
try:
    from ..version import version
except (ValueError, ModuleNotFoundError):
    version = 'VERSION-NOT-FOUND'


__all__ = ['UART']


# Set PandasDate helper which supports nanoseconds.
date_utils.date_helper = PandasDateTimeHelper()


class UART(object):
    _buffer = b''  # buffer[:size] = memoryview(buffer)[-size:]
    _payloads = []
    _uart = None
    _db_client = None
    _write_api = None
    _time = None
    _step = None

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
              batch_size = 32
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
        self._logger = logging.getLogger('multi-ear-uart')

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
        self._packet_start = b'\x11\x99\x22\x88\x33\x73'
        self._packet_start_len = len(self._packet_start)
        self._packet_header_len = 11
        self._buffer_min_len = 34
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

        # connect to serial port
        self._uart = Serial(
            port=config.getstr(
                'serial', 'port', fallback='/dev/ttyAMA0'
            ),
            baudrate=config.getint(
                'serial', 'baudrate', fallback=115_200
            ),
            timeout=config.getint(
                'serial', 'timeout', fallback=2_000
            )/1000,
            rtscts=True,
            exclusive=True,
        )
        self._logger.info(f"Serial connection = {self._uart}")

        # connect to influxdb
        self._db_client = InfluxDBClient(
           url=config.getstr(
               'influx2', 'url', fallback='http://127.0.0.1:8086'
           ),
           org=config.getstr(
               'influx2', 'org', fallback='-'
           ),
           token=config.getstr(
               'influx2', 'token', fallback=':'
           ),
           timeout=config.getint(
               'influx2', 'timeout', fallback=10_000
           ),
           auth_basic=config.getboolean(
               'influx2', 'auth_basic', fallback=False
           ),
           default_tags=dict(
               host=config.getstr('tags', 'host', fallback=gethostname()),
               uuid=config.getstr('tags', 'uuid', fallback='null'),
               version=version.replace('VERSION-NOT-FOUND', 'null'),
           ),
        )
        self._logger.info(f"Influxdb connection = {self._db_client.ping()}")

        self._write_api = self._db_client.write_api(
            success_callback=self._write_success if debug else None,
            error_callback=self._write_error,
            retry_callback=self._write_retry,
        )

        self._bucket = config.getstr(
            'influx2', 'bucket', fallback='multi_ear/'
        )
        self._batch_size = config.getint(
            'influx2', 'batch_size', fallback=self._sampling_rate
        )
        self._measurement = config.getstr(
            'influx2', 'measurement', fallback='multi_ear'
        )

        # init threads pool and lock
        self._pool = Queue()
        self._lock = threading.Lock()
        for i in range(2):
            threading.Thread(target=self._threader, daemon=True).start()

        # terminate at exit
        atexit.register(self.close)

    def close(self):
        self._logger.info("Close serial port and influxdb client")
        self.__del__()

    def __del__(self):
        if self._uart is not None:
            self._uart.close()
        if self._db_client is not None:
            self._db_client.close()
        if self._write_api is not None:
            self._write_api.close()
        pass

    def _frombuffer(self, offset=0, count=1, dtype=np.int8, like=None):
        """Return a dtype sequence from the buffer
        """
        return np.frombuffer(self._buffer, dtype, count, offset, like=like)

    def _packet_len(self, i):
        """Return the packet len
        """
        j = i + self._packet_start_len
        return self._packet_start_len + int(self._buffer[j])

    def _packet_starts(self, i):
        """Returns True if the read buffer at the given start index matches the
        packet start sequence.
        """
        start = memoryview(self._buffer)[i:i+self._packet_start_len]
        return start == self._packet_start

    def _extract(self):
        """Extract payloads from the read buffer.
        """
        buffer_len = len(self._buffer)
        i = 0
        payloads = []
        while i < buffer_len - self._buffer_min_len:

            # packet header match?
            if self._packet_starts(i):

                # get packet length
                packet_len = self._packet_len(i)

                # check buffer length
                if i + packet_len > buffer_len:
                    break

                # hard debug
                # self._logger.info(
                #     np.frombuffer(self._buffer, np.uint8, packet_len, i)
                # )

                # get payload
                length = int(self._buffer[i+self._packet_header_len-1])
                offset = i + self._packet_header_len

                # append payload to list
                payloads.append(self._buffer[offset:offset+length])

                # shift buffer to next packet
                i += packet_len

            # skip byte
            i += 1

        with self._lock:
            self._buffer = self._buffer[i:]
            self._payloads += payloads

    def _decode_and_write(self):
        """Decode points from payloads and write to the database.
        """
        if len(self._payloads) < self._batch_size:
            return
        self._pool.put(self._payloads)
        with self._lock:
            self._payloads = []

    def _threader(self):
        """Thread to decode points from payloads and write to the database.
        """
        while True:
            payloads = self._pool.get()
            points = self._decode(payloads)
            self._write(points)
            self._pool.task_done()

    def _decode(self, payloads) -> list:
        """Decode points from payloads.
        """
        return [self._decode_point_from_payload(p) for p in payloads]

    def _decode_point_from_payload(self, payload) -> Point:
        """Convert payload from Level-1 data to counts.
        Returns
        -------
        point : :class:`Point`
            Influx Point object with all tags, fields for the given time step.
        """

        length = len(payload)
        # self._logger.info(f"payload #{length}: "
        #                   f"{np.frombuffer(payload, np.uint8)}")

        # Get date, time, and cycle step from payload
        y, m, d, H, M, S, step = np.frombuffer(payload, np.uint8, 7, 0)
        # self._logger.info(f'payload time: {y} {m} {d} {H} {M} {S} {step}')

        # Verify step increment
        if self._step is not None:
            dstep = (int(step) - self._step) % self._sampling_rate
            if dstep != 1:
                self._logger.warning(f"Step increment yields {dstep}")
        else:
            dstep = 1

        # store current step and set local time
        with self._lock:
            self._step = int(step)
            self._time += self._delta * dstep

        # GNSS clock?
        gnss = False if self.local_clock else y != 0
        if gnss:
            timestamp = pd.Timestamp(2000+y, m, d, H, M, S) + step*self._delta
            clock = 'GNSS'
        else:
            timestamp = self._time
            clock = 'local'
        # self._logger.info(f'{clock} time: {time}')

        # Create point
        point = Point(self._measurement).time(timestamp).tag('clock', clock)

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
        # DLVR       [Pa] : counts * 0.01*250/6553
        # SP210      [Pa] : counts * 250/(0.9*32768)
        # LPS33HW   [hPa] : count / 4096
        # LIS3DH     [mg] : counts * 0.076
        # LIS3DH   [ms-2] : counts * 0.076*9.80665/1000
        # SHT8x_T    [°C] : counts * 175/(2**16-1) - 45
        # SHT8x_H     [%] : counts * 100/(2**16-1)
        # ICS       [dBV] : counts * 100/4096

        # GNSS
        if gnss and length >= 46:
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

        # self._logger.debug(f"Read point: {point.to_line_protocol()}")

        return point

    def _receive(self):
        """Read all available bytes from the serial port
        and append to the read buffer.
        """
        # https://github.com/pyserial/pyserial/issues/216#issuecomment-369414522
        while True:
            size = max(1, min(2048, self._uart.in_waiting))
            received = self._uart.read(size)
            self._buffer += received
            if b'\n' in received:
                return

    def _write(self, points):
        """Write points to Influx database in batch mode
        """
        # self._logger.info(f"Write {len(points)} lines")
        self._write_api.write(bucket=self._bucket, record=points)

    def _write_success(self, conf: (str, str, str), data: str):
        """Successfully writen batch."""
        self._logger.debug("Written batch")

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
        self._payloads = []

        # set local time as backup if GNSS fails
        self._time = pd.to_datetime("now", utc=True).round(self._delta)
        self._logger.info(f"Local reference time if GNSS fails: {self._time}")

        # clear serial output buffer
        self._uart.reset_output_buffer()

        while True:
            self._receive()
            self._extract()
            self._decode_and_write()

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
