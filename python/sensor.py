import python.transformations as tr
from openhab.items import Item


class Sensor:
    def __init__(self, openhab_item: Item):
        self.openhab_item = openhab_item
        self.name = self.openhab_item.name
        mapping = sensor_mappings.get(self.name)
        if mapping:
            self.arduino_channel = mapping[0]
            self.transformation_function = mapping[1]
        self.value = 0
        self.last_value = 0
        self.last_update = None


# Provides information, to which Arduino Pin the Sensor is connected and which transformation function to apply on received values
sensor_mappings = {
    'U12V': (14, tr.internal_voltage_12),  # A0
    'U5V': (15, tr.internal_voltage_5),  # A1
    'Iinverter': (16, tr.shunt75mv),  # A2
    'Iverb': (17, tr.acs711),  # A3
    'Ibat': (18, tr.acs711),  # A4
    'reserve': (19, tr.just_return),  # A5
    'Awasser1': (20, tr.just_return),  # A6
    'Awasser2': (21, tr.just_return),  # A7
    'Atank': (21, tr.tank)  # D2
}


# Builds a name to item mapping dict
def build_sensor_name_dict(openhab_items):
    return {key: Sensor(value) for key, value in openhab_items}
