from python_jbdtool_bms import BMS

bms = BMS("/dev/ttyUSB0")

pbat_avg_values = []


def add_pbat_reading_to_queue(reading):
    pbat_avg_values.append(reading)
    if len(pbat_avg_values) > 180:
        pbat_avg_values.pop(0)


def calculate_pbat_avgs():
    return f"5min: {get_remaining_string(sum(pbat_avg_values[-30:])/30)}, " \
           f"15min: {get_remaining_string(sum(pbat_avg_values[-90:])/90)}, " \
           f"30min: {get_remaining_string(sum(pbat_avg_values)/180)}"


def get_remaining_string(avg_current):
    remaining = 0 if avg_current == 0 else (bms.residual_capacity if avg_current < 0 else 110 - bms.residual_capacity) / avg_current
    return f"{int((remaining // 1))}:{round(remaining % 1 * 60)}h"


def read_from_bms(new_values):
    bms.query_all()
    new_values['ULiFe'] = bms.total_voltage
    new_values['ILiFe'] = bms.current
    add_pbat_reading_to_queue(bms.current)
    new_values['RSOCLiFe'] = bms.rsoc
    new_values['TimeLiFe'] = calculate_pbat_avgs()