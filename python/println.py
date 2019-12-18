import serial

ser = serial.Serial(

    port='/dev/ttyAMA0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)
counter = 0


while 1:
    x = ser.readline().decode('utf-8')
    msg = x.split(":")
    if msg[0] == "A7":
        print((5.05 / 1024) * (float(msg[1])))
        print(0.0716520039 * (float(msg[1])+1) - 36.65)
        print(x)
