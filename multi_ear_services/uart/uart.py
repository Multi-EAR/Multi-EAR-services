import time
import numpy as np
import serial
import socket
from influxdb_client import InfluxDBClient
# from influxdb_client .client.write_api import SYNCHRONOUS

# data packet definition
_packet_header = b'\x11\x99\x22\x88\x33\x73'
_packet_header_bytes = len(_packet_header)
_packet_bytes_min = 40  # minimum bytes to process a packet

# sampling definition
_sampling_rate = 16  # Hz
_sampling_delta = np.timedelta64(np.int64(1e9/_sampling_rate))  # ns

# device hostname
_hostname = socket.gethostname()


def uart_readout(port='/dev/ttyAMA0', baudrate=115200, timeout=2,
                 client: InfluxDBClient = None):
    """
    Continuoisly read uart serial stream.

    Parameters
    ----------
    port : `str`, optional
        Serial port (default: "/dev/ttyAMA0").

    baudrate : `int`, optional
        Serial port baudrate (default: 115200).

    timeout : `int`, optional
        Serial port timeout, in seconds (default: 1).

    client : `InfluxDBClient`, optional
        InfluxDB client for data storage.
    """

    # connect to influxDB data client
    client = client or InfluxDBClient.from_config_file("influxdb.ini")
    print(client)

    # connect to serial port
    ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
    print(ser)

    # wait while everythings gets set
    time.sleep(2)

    # init
    read_buffer = b""
    read_time = np.datetime64("now")  # backup if GPS fails

    # continuous serial readout while open
    while ser.isOpen():
        read_buffer, data_points = parse_read(
            read_lines(ser, read_buffer), read_time
        )
        client.write_points(data_points)


def read_lines(ser, read_buffer=b"", **args):
    """Read all available lines from the serial port
    and append to the read buffer.

    Parameters
    ----------
    ser : serial.Serial() instance
        The device we are reading from.
    read_buffer : bytes, default b''
        Previous read buffer that is appended to.

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

    return read_buffer + read


def read_all(ser, read_buffer=b"", **args):
    """Read all available bytes from the serial port
    and append to the read buffer.

    Parameters
    ----------
    ser : serial.Serial() instance
        The device we are reading from.
    read_buffer : bytes, default b''
        Previous read buffer that is appended to.

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

    return read_buffer + read


def read_all_newlines(ser, read_buffer=b"", n_reads=4):
    """Read data in until encountering newlines.

    Parameters
    ----------
    ser : serial.Serial() instance
        The device we are reading from.
    n_reads : int
        The number of reads up to newlines
    read_buffer : bytes, default b''
        Previous read buffer that is appended to.

    Returns
    -------
    output : bytes
        Bytes object that contains read_buffer + read.

    Notes
    -----
    .. This is a drop-in replacement for read_all().
    """
    read = read_buffer
    for _ in range(n_reads):
        read += ser.read_until()

    return read


# dtype shorts with byteswap ('_S' suffix)
_u1 = np.dtype(np.uint8)
_u8 = np.dtype(np.uint64)
_i1 = np.dtype(np.int8)
_i2 = np.dtype(np.int16)
_i2_S = _i2.newbyteorder('S')
_i4 = np.dtype(np.int32)
_i4_S = _i4.newbyteorder('S')
_f4 = np.dtype(np.float32)


def parse_read(read_buffer, read_time, data_points=[]):
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
            payload_bytes = np.frombuffer(read_buffer, dtype=_i1, offset=i)

            # payload
            i += 1
            payload = read_buffer[i:i+payload_bytes]

            # convert payload to counts and add to data buffer
            data_point = parse_payload(payload, read_time)
            data_points.append(data_point)

            # skip packet header scanning
            i += payload_bytes

        else:
            i += 1

    # return tail
    return read_buffer[i:], data_points


def parse_payload(payload, imprecise_time):
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
    print(imprecise_time, payload.hex())

    def frompayload(*args, **kwargs):
        return np.frombuffer(payload, *args, **kwargs)

    # date time
    # h, m, s = int(payload[0]), int(payload[1]), int(payload[2])
    step = frompayload(dtype=_u1, offset=3)

    # DLVR-F50D differential pressure (14-bit ADC)
    # DLVR = int(payload[4] | payload[5])
    DLVR = frompayload(dtype=_i2, offset=4)

    # SP210
    # SP210 = int(payload[6] << 8 | payload[7])
    SP210 = frompayload(dtype=_i2_S, offset=6)

    # LPS33HW barometric pressure (returns 32-bit)
    # LPS = int.from_bytes(payload[8:11], "little")
    LPS33HW = frompayload(dtype=_i4, offset=8, count=1)

    # LIS3DH 3-axis accelerometer and gyroscope (16-bit ADC)
    LIS3DH_X, LIS3DH_Y, LIS3DH_Z = frompayload(dtype=_i2_S, offset=11, count=3)
    # LIS3_X = int(payload[11] << 8 | payload[12])
    # LIS3_Y = int(payload[13] << 8 | payload[14])
    # LIS3_Z = int(payload[15] << 8 | payload[16])

    # LSM303 3-axis accelerometer and magnetometer (returns 8-bit)
    LSM303_X, LSM303_Y, LSM303_Z = frompayload(dtype=_i1, offset=17, count=3)
    # int(payload[17]), int(payload[18]), int(payload[19])

    # SHT8x temperature and humidity (16-bit ADC)
    SHT8x_T, SHT8x_H = frompayload(dtype=_i2_S, offset=20, count=2)
    # SHT_T = int(payload[20] << 8 | payload[21])
    # SHT_H = int(payload[22] << 8 | payload[23])

    # Construct dictionary with data point
    data_point = {
        "measurement": 'Multi-EAR',
        "time": imprecise_time,
        "tag": _hostname,
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
    if step == 0:
        GNS_LAT, GNS_LON = frompayload(dtype=_f4, offset=24, count=2)
        data_point['fields']['GNS_LAT'] = GNS_LAT
        data_point['fields']['GNS_LON'] = GNS_LON

    return data_point


def main():
    uart_readout()


if __name__ == "__main__":
    main()
