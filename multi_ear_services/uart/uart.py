# Mandatory imports
import time
import numpy as np
import serial
import argparse
from configparser import ConfigParser
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

# Relative imports
# try:
#     from ..version import version
# except ModuleNotFoundError:
#     version = '[VERSION-NOT-FOUND]'
version = '[VERSION-NOT-FOUND]'


__all__ = ['uart_readout']


# data packet definition
_packet_header = b'\x11\x99\x22\x88\x33\x73'  # 17 153 34 136 51 115
_packet_header_bytes = len(_packet_header)
_packet_bytes_min = 40  # minimum bytes to process a packet

# sampling definition
_sampling_rate = 16  # Hz
_sampling_delta = np.timedelta64(np.int64(1e9/_sampling_rate), 'ns')  # ns


def uart_readout(config_file='config.ini', debug=None):
    """Sensorboard serial readout via UART with data storage in a local
    Influx v1.8 database.

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

    # influxdb connection
    _client = InfluxDBClient.InfluxDBClient.from_config(config_file)
    _write_api = _client.write_api(write_options=SYNCHRONOUS)

    bucket = config_value('influx2', 'bucket')

    if debug:
        print(_client.health)

    # serial connection
    _serial = serial.Serial(
        port=config_value('serial', 'port'),
        baudrate=config_value('serial', 'baudrate'),
        timeout=config_value('serial', 'timeout') / 1000  # ms to s,
    )

    if debug:
        print(_serial)

    # wait while everythings gets set
    # time.sleep(2)

    # init
    read_buffer = b""
    read_time = np.datetime64("now") - _sampling_delta  # backup if GPS fails

    # continuous serial readout while open
    while _serial.isOpen():

        try:
            # append to read buffer
            read_buffer += read_lines(_serial)
            read_buffer, data_points = parse_read(read_buffer, read_time,
                                                  debug=debug)

            print(data_points)
            raise SystemExit()

            # write to influxdb
            _write_api.write(bucket=bucket, record=data_points)

        except (KeyboardInterrupt, SystemExit):
            _serial.close()
            _client.close()

    else:
        _client.close()


def read_lines(ser, **args):
    """Read all available lines from the serial port
    and append to the read buffer.

    Parameters
    ----------
    ser : serial.Serial() instance
        The device we are reading from.

    Returns
    -------
    output : bytes
        Bytes object that contains read_buffer + read.

    Notes
    -----
    .. `**args` appears, but is never used. This is for
       compatibility with `read_all_newlines()` as a
       drop-in replacement for this function.
    """
    read = ser.readline()
    time.sleep(.2)
    in_waiting = ser.in_waiting
    read += ser.readline(in_waiting)

    return read


def read_all(ser, **args):
    """Read all available bytes from the serial port
    and append to the read buffer.

    Parameters
    ----------
    ser : serial.Serial() instance
        The device we are reading from.

    Returns
    -------
    output : bytes
        Bytes object that contains read_buffer + read.

    Notes
    -----
    .. `**args` appears, but is never used. This is for
       compatibility with `read_all_newlines()` as a
       drop-in replacement for this function.
    """
    # Set timeout to None to make sure we read all bytes
    previous_timeout = ser.timeout
    ser.timeout = None

    in_waiting = ser.in_waiting
    read = ser.read(size=in_waiting)

    # Reset to previous timeout
    ser.timeout = previous_timeout

    return read


def read_all_newlines(ser, n_reads=4):
    """Read data in until encountering newlines.

    Parameters
    ----------
    ser : serial.Serial() instance
        The device we are reading from.
    n_reads : int
        The number of reads up to newlines

    Returns
    -------
    output : bytes
        Bytes object that contains read_buffer + read.

    Notes
    -----
    .. This is a drop-in replacement for read_all().
    """
    read = b""
    for _ in range(n_reads):
        read += ser.read_until()

    return read


# dtype shorts with byteswap ('_S' suffix)
_u1 = np.dtype(np.uint8)
_u8 = np.dtype(np.uint64)
_i1 = np.dtype(np.int8)
_i1_S = _i1.newbyteorder('S')
_i2 = np.dtype(np.int16)
_i2_S = _i2.newbyteorder('S')
_i4 = np.dtype(np.int32)
_i4_S = _i4.newbyteorder('S')
_f4 = np.dtype(np.float32)


def frombuffer(buffer, dtype=None, count=None, offset=None, **kwargs):
    """Wrapper to np.frombuffer returning the item if count == 1

    See np.frombuffer for the usage.
    """
    dtype = dtype or _f4
    count = count or -1
    offset = offset or 0
    data = np.frombuffer(buffer, dtype=dtype, count=count, offset=offset,
                         **kwargs)
    return data.item() if count == 1 else data


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
    while i < read_bytes - _packet_bytes_min:

        # packet header match
        if read_buffer[i:i+_packet_header_bytes] == _packet_header:

            # backup time (inaccurate!)
            read_time += _sampling_delta

            # payload size
            i += 10
            payload_bytes = frombuffer(read_buffer, _i1, 1, i)

            # payload
            i += 1
            payload = read_buffer[i:i+payload_bytes]

            if debug:
                print("payload size =", payload_bytes)
                print("payload bytes =", payload)

            # convert payload to counts and add to data buffer
            data_points.append(parse_payload(payload, read_time, debug))

            # skip packet header scanning
            i += payload_bytes

            raise SystemExit()

        else:
            i += 1

    raise SystemExit()

    # return tail
    return read_buffer[i:], data_points


def parse_payload(payload, imprecise_time, debug=False):
    """
    Convert payload to Level-1 data in counts.

    Parameters
    ----------
    payload : `bytes`
        Raw payload stream in bytes.

    imprecise_time : `np.datetime64`
        Payload imprecise time used as backup if the GPS timestamp fails.

    Returns
    -------
    data_point : `dict`
        Dictionary with all fields for the given time step.

    """
    if debug:
        print("imprecise time =", imprecise_time)
        print("payload hex =", payload.hex())

    # date time
    y, m, d, H, M, S = frombuffer(payload, _u1, 6, 0)
    step = frombuffer(payload, _u1, 1, 6)
    # print(y, m, d, H, M, S, step)

    # DLVR-F50D differential pressure (14-bit ADC)
    # DLVR = int(payload[4] | payload[5])
    DLVR = frombuffer(payload, _i1, 1, 4) | frombuffer(payload, _i1, 1, 5)

    # SP210
    # SP210 = payload[6] << 8 | payload[7]  # wrong -> unsigned int?
    # SP210 = frombuffer(payload, _i1, 1, 6) | frombuffer(payload, _i1, 1, 7)
    SP210 = frombuffer(payload, _i2, 1, 6)

    # LPS33HW barometric pressure (returns 32-bit)
    LPS33HW = int.from_bytes(payload[8:11], "little")
    print(LPS33HW)
    LPS33HW = int.from_bytes(payload[8:11], "big")
    print(LPS33HW)
    LPS33HW = frombuffer(payload, _i4, 1, 8)
    print(LPS33HW)
    raise SystemExit()

    # LIS3DH 3-axis accelerometer and gyroscope (16-bit ADC)
    LIS3DH_X, LIS3DH_Y, LIS3DH_Z = frombuffer(payload, _i2_S, 3, 14)
    # LIS3_X = int(payload[11] << 8 | payload[12])
    # LIS3_Y = int(payload[13] << 8 | payload[14])
    # LIS3_Z = int(payload[15] << 8 | payload[16])

    # LSM303 3-axis accelerometer and magnetometer (returns 8-bit)
    LSM303_X, LSM303_Y, LSM303_Z = frombuffer(payload, _i1, 3, 20)
    # int(payload[17]), int(payload[18]), int(payload[19])

    # SHT8x temperature and humidity (16-bit ADC)
    SHT8x_T, SHT8x_H = frombuffer(payload, _i2_S, 2, 23)
    # SHT_T = int(payload[20] << 8 | payload[21])
    # SHT_H = int(payload[22] << 8 | payload[23])

    # Construct dictionary with data point
    data_point = {
        "measurement": 'Multi-EAR',
        "time": imprecise_time,
        "fields": {
            "step": step,
            "DLVR": DLVR,
            "SP210": SP210,
            "LPS33HW": LPS33HW,
            "LIS3DH_X": LIS3DH_X,
            "LIS3DH_Y": LIS3DH_Y,
            "LIS3DH_Z": LIS3DH_Z,
            "LSM303_X": LSM303_X,
            "LSM303_Y": LSM303_Y,
            "LSM303_Z": LSM303_Z,
            "SHT8x_T": SHT8x_T,
            "SHT8x_H": SHT8x_H,
        }
    }

    # Readout gnss at full cycle
    # add GNSS quality
    # if step == 0:
    #     GNS_LAT, GNS_LON = frombuffer(payload, _f4, 2, 24)
    #     data_point['fields']['GNS_LAT'] = GNS_LAT
    #     data_point['fields']['GNS_LON'] = GNS_LON

    if debug:
        print(data_point)

    return data_point


def main():
    """Main script function.
    """
    # arguments
    parser = argparse.ArgumentParser(
        prog='multi-ear-uart',
        description=('Sensorboard serial readout via UART with '
                     'data storage in a local InfluxDB database.'),
    )

    parser.add_argument(
        '-c', '--config_file', metavar='..', type=str, default='config.ini',
        help='Path to configuration file'
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

    uart_readout(args.config_file, args.debug)


if __name__ == "__main__":
    main()
