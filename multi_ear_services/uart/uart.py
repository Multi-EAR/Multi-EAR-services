# Mandatory imports
import atexit
import logging
import multiprocessing as mp
import numpy as np
import os
import sys
from argparse import ArgumentParser
from collections import deque
from configparser import ConfigParser
from dataclasses import dataclass
from dataclasses import field as datafield
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError
from pandas import Timestamp, Timedelta
from serial import Serial
from socket import gethostname
from subprocess import Popen, PIPE
from systemd.journal import JournaldLogHandler
from time import sleep
from typing import Union


# Relative imports
try:
    from ..version import version
except (ValueError, ModuleNotFoundError):
    version = 'VERSION-NOT-FOUND'
try:
    from .ws import MultiEARWebsocket
except (ValueError, ModuleNotFoundError):
    MultiEARWebsocket = False


__all__ = ['UART']


# Set epoch base and delta
_epoch_base = Timestamp('1970-01-01', tz='UTC')
_epoch_delta = Timedelta('1ns')


@dataclass
class Point:
    """influxdb_client-like Point class to improve serialization."""
    time: Timestamp
    clock: str
    fields: dict = datafield(init=False, repr=False, default_factory=dict)

    def field(self, key: str, value: Union[np.integer, np.floating]):
        self.fields[key] = value

    def epoch(self) -> int:
        return (self.time - _epoch_base) // _epoch_delta

    def serialize(self) -> str:
        fields = ",".join([
            f"{k}={v}{'i' if np.issubdtype(v, np.integer) else ''}"
            for k, v in self.fields.items()
        ])
        return "clock={clock} {fields} {time}".format(
            clock=self.clock,
            fields=fields,
            time=self.epoch(),
        )

    def to_line_protocol(self,
                         measurement: str = 'multi_ear',
                         host: str = 'null',
                         uuid: str = 'null',
                         version: str = 'null') -> str:
        """Return the serialized influx line to write with all tags.
        """
        return (f"{measurement},host={host},uuid={uuid},version={version}," +
                self.serialize())


class UART(object):
    _uart = None
    _db = None
    _writer = None
    _buffer = None
    _points = deque()
    _queue = None
    _receiver = None
    _time = None
    _step = None

    def __init__(self, config_file='config.ini', journald=False,
                 debug=False, dry_run=False) -> None:
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
              timeout = 1000
            [tags]
               uuid = %(MULTI_EAR_UUID)s
        """

        # set options
        self.dry_run = dry_run or False

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
        self._packet_start_green = b'\x11\x99\x22\x88\x33\x73'
        self._packet_start_blue = b'\x11\x99\x22\x88\x33\x74'
        self._packet_start_len = 6
        self._packet_header_len = 11
        self._buffer_min_len = 34
        self._sampling_rate = 16  # [Hz]
        self._delta = Timedelta(1/self._sampling_rate, 's')

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
                'serial', 'timeout', fallback=1_000
            )/1000,
            bytesize=8,
            parity='N',
            stopbits=1,
            rtscts=True,
            xonxoff=False,
        )
        self._logger.info(f"Serial connection = {self._uart}")

        # connect to influxdb
        self._db = InfluxDBClient(
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
        )
        self._logger.info(f"Influxdb connection = {self._db.ping()}")

        self._writer = self._db.write_api(
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
        self._host = config.getstr('tags', 'host', fallback=gethostname())
        self._uuid = config.getstr('tags', 'uuid', fallback='null')
        self._version = version.replace('VERSION-NOT-FOUND', 'null')

        # init serial receiver queue and process
        self._queue = mp.Queue()
        self._receiver = mp.Process(
            target=_uart_receiver_thread,
            daemon=True,
            args=(self._uart, self._queue),
        )

        # init websocket
        if MultiEARWebsocket:
            # self._ws = MultiEARWebsocket()
            # self._ws.listen("localhost", 8765)
            # self._ws_fields = ['LPS33HW',
            #                    'DLVR',
            #                    'LIS3DH_X', 'LIS3DH_Y', 'LIS3DH_Z']

        # terminate at exit
        atexit.register(self.close)

    def close(self):
        self._logger.info("Close uart and subprocesses")
        self.__del__()

    def __del__(self):
        if self._uart is not None:
            self._uart.close()
        if self._db is not None:
            self._db.close()
        if self._writer is not None:
            self._writer.close()
        if self._queue is not None:
            self._queue.close()
        if self._receiver is not None:
            self._receiver.terminate()
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
        """Returns 1 or 2 if the read buffer at the given start index matches
        the packet start sequence of the green or blue pcb, otherwise 0.
        """
        start = memoryview(self._buffer)[i:i+self._packet_start_len]
        if start == self._packet_start_green:
            return 0x73
        elif start == self._packet_start_blue:
            return 0x74
        else:
            return 0

    def _extract(self, read=b''):
        """Extract payloads from the read buffer.
        """
        # append to buffer
        self._buffer += read

        # store buffer len
        buffer_len = len(self._buffer)

        # start?
        if buffer_len < self._buffer_min_len:
            return

        # parse buffer
        i = 0
        while i < buffer_len - self._buffer_min_len:

            # packet header match?
            pcb_id = self._packet_starts(i)
            if pcb_id != 0:

                # get packet length
                packet_len = self._packet_len(i)

                # hard debug
                # self._logger.info(
                #     np.frombuffer(self._buffer, np.uint8, packet_len, i)
                # )

                # extract payload
                length = int(self._buffer[i+self._packet_header_len-1])
                offset = i + self._packet_header_len
                payload = self._buffer[offset:offset+length]

                # check if payload is complete
                if len(payload) != length:
                    break

                # decode point
                point = self._decode_payload_to_point(payload, length, pcb_id)

                # append point
                self._points.append(point)

                # broadcast point
                # self._broadcast(point)

                # shift buffer to next packet
                i += packet_len

            # skip byte
            i += 1

        self._buffer = self._buffer[i:]

    def _decode_payload_to_point(self, payload, length, pcb_id) -> Point:
        """Convert payload from Level-1 data to counts.
        Returns
        -------
        point : :dataclass:`Point`
            Influx Point object with all tags, fields for the given time step.
        """

        self._logger.debug(f"payload {pcb_id} #{length}: "
                           f"{np.frombuffer(payload, np.uint8)}")

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

        # store current step
        self._step = int(step)

        # GNSS clock?
        gnss = y != 0 and M != 0
        if gnss:
            timestamp = Timestamp(2000+y, m, d, H, M, S) + step * self._delta
            self._time = timestamp
            clock = 'GNSS'
        else:
            self._time += self._delta * dstep
            timestamp = self._time
            clock = 'local'
        # self._logger.info(f'{clock} time: {timestamp}')

        # Create point object
        point = Point(timestamp, clock)

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

        # LSM303C 3-axis accelerometer (3x 16-bit), green pcb only
        if pcb_id == 0x73 and False:
            point.field(
                'LSM303C_X',
                np.int16(payload[14] | (payload[15] << 8))
            )
            point.field(
                'LSM303C_Y',
                np.int16(payload[16] | (payload[17] << 8))
            )
            point.field(
                'LSM303C_Z',
                np.int16(payload[18] | (payload[19] << 8))
            )

        # LIS3DH 3-axis accelerometer (3x 16-bit)
        point.field(
            'LIS3DH_X',
            np.int16(payload[20] | (payload[21] << 8))
        )
        point.field(
            'LIS3DH_Y',
            np.int16(payload[22] | (payload[23] << 8))
        )
        point.field(
            'LIS3DH_Z',
            np.int16(payload[24] | (payload[25] << 8))
        )

        # SHT85 temperature and humidity, ICS-4300 SPL
        #
        # temporary fix for missing byte of ICS-4300
        # if length == 32 or length == 56:
        #
        if length == 31 or length == 55:
            point.field(
                'SHT85_T',
                np.uint16((payload[26] << 8) | payload[27])
            )
            point.field(
                'SHT85_H',
                np.uint16((payload[28] << 8) | payload[29])
            )
        """
            point.field(
                'ICS',
                np.uint16((payload[30] << 8) | payload[31])
            )
        else:  # length == 28 or length == 52
            point.field(
                'ICS',
                np.uint16((payload[26] << 8) | payload[27])
            )
        """

        # Counts to unit conversions
        # DLVR       [Pa] : counts * 0.01*250/6553
        # SP210      [Pa] : counts * 250/(0.9*32768)
        # LPS33HW   [hPa] : count / 4096
        # LIS3DH     [mg] : counts * 0.076
        # LIS3DH   [ms-2] : counts * 0.076*9.80665/1000
        # SHT85_T    [°C] : counts * 175/(2**16-1) - 45
        # SHT85_H     [%] : counts * 100/(2**16-1)
        # ICS       [dBV] : counts * 100/4096

        # GNSS
        if gnss and length >= 51:  # >= 52
            lat, lon, alt = np.frombuffer(payload, np.int32, 3, length - 24)
            point.field('GNSS_LAT', lat)
            point.field('GNSS_LON', lon)
            point.field('GNSS_ALT', alt)
            self._set_system_time(self._time)

        self._logger.debug(f"Point: {point.serialize()}")

        return point

    def _broadcast(self, point):
        """Broadcast points using WebSockets
        """
        if MultiEARWebsocket is False:
            return
        data = [point.fields[k] for k in self._ws_fields]
        self._ws.broadcast(data)

    def _write(self):
        """Write points to Influx database in batch mode
        """
        if len(self._points) < self._batch_size:
            return
        self._logger.debug(f"Write {len(self._points)} lines")
        lines = "\n".join([
            p.to_line_protocol(
                self._measurement,
                self._host,
                self._uuid,
                self._version
            ) for p in self._points
        ])
        self._writer.write(bucket=self._bucket, record=lines)
        self._points.clear()

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

    def _set_system_time(self, timestamp, force=False):
        """Set system time if no NTP sync is available
        """
        self._logger.info(f"Set system time to {self._time}")
        try:
            p = Popen(['timedatectl',
                       'show',
                       '--property=NTPSynchronized',
                       '--value'],
                      stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            if p.returncode != 0:
                self._logger.error(
                    f"Error retrieving NTPSynchronized: {err.decode('utf-8')}"
                )
            if out.decode('utf-8') != 'yes':
                t = timestamp.strftime('%Y/%m/%d %H:%M:%S')
                p = Popen(['sudo',
                           'timedatectl',
                           'set-time',
                           f'"{t}"'],
                          stdout=PIPE, stderr=PIPE)
                out, err = p.communicate()
                if p.returncode == 0:
                    self._logger.debug(f"System time set to {t}")
                else:
                    self._logger.error(
                        f"timedatectl time-set error: {err.decode('utf-8')}"
                    )
        except OSError as e:
            self._logger.error(f"Could not set the system time: {e}")

    def readout(self):
        """Contiously read UART serial data into a binary buffer, parse the
        payload and write measurements to the Influx time series database.
        """

        self._logger.info("Start serial readout to influx database")

        # init
        self._buffer = b''

        # clear serial output buffer
        self._uart.reset_output_buffer()

        # start serial receiver process
        self._receiver.start()

        # set local time as backup if GNSS fails
        self._time = Timestamp.utcnow().round(self._delta)
        self._logger.info(f"Local reference time if GNSS fails: {self._time}")

        while True:
            read = self._queue.get()
            if not read:
                sleep(.1)
                continue
            self._extract(read)
            self._write()

        self._logger.info("Serial port closed")


def _uart_receiver_thread(s, q, chunk_size=2048):
    """Read all available bytes from the serial port
    and append to the queue.
    """
    # https://github.com/pyserial/pyserial/issues/216#issuecomment-369414522

    while s.is_open:
        # wait until there is data
        while (s.in_waiting == 0):
            pass
        # read data and append to the buffer queue
        read = s.read(size=chunk_size)
        q.put(read)


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
    )
    uart.readout()


if __name__ == "__main__":
    main()
