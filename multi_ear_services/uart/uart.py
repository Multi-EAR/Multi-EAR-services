# Mandatory imports
import atexit
import numpy as np
import pandas as pd
from serial import Serial
from argparse import ArgumentParser
from configparser import ConfigParser
from influxdb_client import InfluxDBClient, WriteApi
from influxdb_client.client.write_api import SYNCHRONOUS

# Relative imports
from ..version import version
from ..util.serial_read import read_lines


__all__ = ['uart_readout']

#
# Todo: make an UART class!
#
# data packet definition
_header = b'\x11\x99\x22\x88\x33\x73'  # 17 153 34 136 51 115
_header_size = len(_header)
_buffer_bytes_min = 40  # minimum bytes to process a packet

# sampling definition
_sampling_rate = 16  # Hz
_delta = pd.Timedelta(1/_sampling_rate, 'ns')
# _time = None


def on_exit(db_client: InfluxDBClient, write_api: WriteApi, uart_conn: Serial):
    """Close clients after terminate a script.

    :param db_client: InfluxDB client
    :param write_api: WriteApi
    :param uart_conn: Serial
    :return: nothing
    """
    write_api.close()
    db_client.close()
    uart_conn.close()


def uart_readout(config_file='config.ini', debug=None, dry_run=False):
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

    config = ConfigParser()
    config.read(config_file)

    def config_value(sec: str, key: str):
        return config[sec][key].strip('"')

    # influx database connection
    _db_client = InfluxDBClient.from_config_file(config_file)
    _write_api = _db_client.write_api(write_options=SYNCHRONOUS)

    bucket = config_value('influx2', 'bucket')

    print("InfluxDB health =", _db_client.health())

    # serial port connection
    _uart_conn = Serial(
        port=config_value('serial', 'port'),
        baudrate=int(config_value('serial', 'baudrate')),
        timeout=int(config_value('serial', 'timeout')) / 1000  # ms to s,
    )
    print("UART connection =", _uart_conn)

    # automatically close clients on exit
    atexit.register(on_exit, _db_client, _write_api, _uart_conn)

    # init
    read_buffer = b""
    read_time = pd.to_datetime("now")  # backup if GPS fails

    # continuous serial readout while open
    print("Start UART readout")
    while _uart_conn.isOpen():
        read_buffer, data_points = parse_read(
            read_lines(_uart_conn, read_buffer), read_time, debug=debug
        )
        if not dry_run:
            _write_api.write(bucket=bucket, record=data_points)


def parse_read(read_buffer, read_time, data_points=[], debug=False):
    """Parse read buffer for data packets with payload.

    Parameters
    ----------

    Returns
    -------
    read_buffer : `bytes`
        Bytes object that contains the remaining read_buffer.

    data : `list`
        Data list with parsed payload in counts.
    """
    # get bytes received
    read_bytes = len(read_buffer)

    # init packet scanning
    i = 0

    # scan for packet header
    while i < read_bytes - _buffer_bytes_min:

        # packet header match
        if read_buffer[i:i+_header_size] == _header:

            # backup time (inaccurate!)
            read_time += _delta

            # packet size
            packet_size = _header_size + int(read_buffer[i+_header_size])

            # payload size
            i += 10
            payload_size = int(read_buffer[i])

            # payload
            i += 1
            payload = read_buffer[i:i+payload_size]

            # convert payload to counts and add to data buffer
            data_points.append(parse_payload(payload, read_time, debug))

            # skip packet header scanning
            i += packet_size

        else:
            i += 1

    # return tail
    return read_buffer[i:], data_points


def parse_payload(payload, backup_time, debug=False):
    """
    Convert payload to Level-1 data in counts.

    Parameters
    ----------
    payload : `bytes`
        Raw payload stream in bytes.

    backup_time : `np.datetime64`
        Payload imprecise time used as backup if the GNSS timestamp fails.

    Returns
    -------
    data_point : `dict`
        Dictionary with all fields for the given time step.

    """
    payload_size = len(payload)
    fields = dict()

    # Get date time cycle from buffer
    y, m, d, H, M, S, step = np.frombuffer(payload, np.uint8, 7, 0)

    # GNSS lock?
    if y != 0:
        time = pd.Timestamp(2000 + y, m, d, H, M, S) + step * _delta
        gnss = True
    else:
        time = backup_time
        gnss = False

    # DLVR-F50D differential pressure (14-bit ADC)
    tmp = payload[7] | (payload[8] << 8)
    fields['DLVR'] = (tmp | 0xF000) if (tmp & 0x1000) else (tmp & 0x1FFF)

    # SP210
    fields['SP210'] = (payload[9] << 8) | payload[10]

    # LPS33HW barometric pressure (24-bit)
    fields['LPS33'] = payload[11] + (payload[12] << 8) + (payload[13] << 16)

    # LIS3DH 3-axis accelerometer and gyroscope (3x 16-bit)
    fields['LIS3_X'] = payload[14] | (payload[15] << 8)
    fields['LIS3_Y'] = payload[16] | (payload[17] << 8)
    fields['LIS3_Z'] = payload[18] | (payload[19] << 8)

    if payload_size == 26 or payload_size == 50:
        fields['SHT_T'] = (payload[20] << 8) | payload[21]
        fields['SHT_H'] = (payload[22] << 8) | payload[23]
        fields['ICS'] = (payload[24] << 8) | payload[25]
    else:
        fields['ICS'] = (payload[20] << 8) | payload[21]

    # Counts to unit conversions
    # DLVR counts_to_Pa = 0.01*250/6553  # 25/65530
    # SP210 counts_to_inH20 = 1/(0.9*32768)  # 10/(9*32768)
    # LPS33HW counts_to_hPa = 1 / 4096
    # LIS3 counts_to_ms2 = 0.076
    # SHT8x ...
    # ICS counts_to_dB = 100/4096

    # GNSS
    if gnss and payload_size > 26:
        i = payload_size - 24
        fields['GNSS_LAT'] = payload[i] + (payload[i+1] << 8) + (payload[i+2] << 16)
        i += 3
        fields['GNSS_LON'] = payload[i] + (payload[i+1] << 8) + (payload[i+2] << 16)
        i += 3
        fields['GNSS_ALT'] = payload[i] + (payload[i+1] << 8) + (payload[i+2] << 16)

    # Construct data point
    data_point = {
        "measurement": 'multi_ear',
        "time": f"{time.asm8}Z",
        "fields": fields,
    }
    if gnss:
        data_point['tag'] = 'GNSS'

    if debug:
        print(data_point)

    return data_point


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
        '-c', '--config_file', metavar='..', type=str, default='config.ini',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='UART readout without storage in the Influx database'
    )
    parser.add_argument(
        '--debug', action='store_true',
        help='Make the operation more talkative'
    )

    parser.add_argument(
        '--version', action='version', version=version,
        help='Print xcorr version and exit'
    )

    args = parser.parse_args()

    uart_readout(args.config_file, args.debug, args.dry_run)


if __name__ == "__main__":
    main()
