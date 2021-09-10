 #!/opt/py37/bin/python3

import serial
import time
from datetime import datetime, timedelta

# carrier definition
carrier_start = b'\x11\x99\x22\x88\x33\x73'
carrier_start_bytes = len(carrier_start)
carrier_min_bytes = 40  # minimum bytes to process a carrier

# sampling definition
sampling_rate = 16  # Hz
t_delta = 1/sampling_rate  # s


def payload_to_counts(payload, n_payload, t_start):
    """Move to data
    """
    # date time
    h, m, s, step = int(payload[0]), int(payload[1]), int(payload[2]), int(payload[3])
    t = t_start + timedelta(0, n_payload*t_delta)
    # print(h, m, s, step)
    print(t)

    # DLVR
    DLVR = int(payload[4] | payload[5])
    
    # SP210
    SP210 = int(payload[6] << 8 | payload[7])
    
    # LPS
    LPS = int.from_bytes(payload[8:11], "little")

    # LIS3
    LIS3_X = int(payload[11] << 8 | payload[12])
    LIS3_Y = int(payload[13] << 8 | payload[14])
    LIS3_Z = int(payload[15] << 8 | payload[16])

    # LSM
    LSM_X, LSM_Y, LSM_Z = int(payload[17]), int(payload[18]), int(payload[19])

    # SHT
    SHT_T = int(payload[20] << 8 | payload[21])
    SHT_H = int(payload[22] << 8 | payload[23])


    print(
        DLVR,
        SP210,
        LPS,
        (LIS3_X, LIS3_X, LIS3_Z),
        (LSM_X, LSM_Y, LSM_Z),
        (SHT_T, SHT_H),
    )

    return # counts


def uart_readout():
    """Todo: Buffer serial stream as fixed byte length and write to files.
    """
    # connect to serial port
    ser = serial.Serial(
        port="/dev/ttyAMA0",
        baudrate=115200,
        timeout=1
    )

    # init
    rx_data = b''
    n_payload = 0
    t_start = datetime.utcnow()

    # continuous serial readout while open
    while ser.isOpen():

        # get serial output
        rx_data += ser.readline()
        time.sleep(.2)
        rx_data += ser.readline(ser.inWaiting())

        # get bytes received
        rx_bytes = len(rx_data)

        # reset carrier scanning
        i = 0

        # scan for carrier start sequence
        while i < rx_bytes - carrier_min_bytes:

            if rx_data[i:i+carrier_start_bytes] == carrier_start:

                payload_bytes = int(rx_data[i+10])
                carrier_bytes = payload_bytes + 11

                # carrier = rx_data[i:i+carrier_bytes]
                # print("carrier = ", carrier.hex())

                payload = rx_data[i+11:i+carrier_bytes]
                n_payload += 1
                print(f"payload_{n_payload:05} = ", payload.hex())

                # convert payload to counts
                payload_to_counts(payload, n_payload, t_start) 

                # skip carrier start sequence scanning
                i += carrier_bytes

            else:
                i += 1 

        rx_data = rx_data[i:]


if __name__ == "__main__":
    uart_readout()
