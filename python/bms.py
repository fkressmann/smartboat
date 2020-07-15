import serial
import struct

ser = serial.Serial(port='/dev/tty.usbserial-AQ00XKFX', baudrate=9600, parity=serial.PARITY_EVEN,
                    stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)


def query_bms(query, format):
    print("")
    print(f"Querying BMS: {query}")
    ser.write(query)
    # destroy senseless data
    ser.read(3)
    # get packet length
    length = int.from_bytes(ser.read(1), byteorder='big')
    print(f"Response length: {length} bytes")
    response = ser.read(length)
    ser.read_all()
    data = struct.unpack(format, response)
    print(f"Parsing response {response}\ninto data {data}")
    return data


def data_to_voltages(data):
    for i, e in enumerate(data):
        print(f'Voltage of cell {i} is {e/1000}V')


def data_to_info(data):
    print(f'Remaining capacity: {data[10]}%')
    print(f'Pack voltage is {data[0]/100}V')
    print(f'Pack current draw is {data[1]/100}A')
    print(f'Pack temperature is {(data[15]-2731)/10}°C')


if __name__ == '__main__':
    data1 = query_bms(b'\xdd\xa5\x03\x00\xff\xfd\x77', ">HHHHHHHHHBBBBBHH")
    data_to_info(data1)
    data2 = query_bms(b'\xdd\xa5\x04\x00\xff\xfc\x77', ">HHHH")
    data_to_voltages(data2)
