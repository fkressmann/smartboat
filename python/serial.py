import time

from python.__main__ import ser, new_values, time_of_last_reading, address_to_sensor_mapping


@ser.on_message()
def handle_incoming_message(msg):
    message = msg.decode("utf-8")
    print(message)
    for s in message.split('_'):
        if s[0] == '+':
            # Cut out '+'
            process_incoming_message(s[1:])
        elif s != '':
            print("Cant handle message: ", s)


# @ser.on_log()
def handle_logging(level, info):
    print(level, info)
    pass


def process_incoming_message(message):
    global time_of_last_reading
    try:
        address, command = message.split(':')
        # Get respective sensor and function from mapping dict
        sensor, function = address_to_sensor_mapping[int(address)]
        # Apply command to function and save result in list
        new_values[sensor] = function(float(command))
        time_of_last_reading = time.time()
    except Exception as e:
        print(f"Error reading message: {type(e)}, {e}")
        print(f"message was '{message}'")
        raise