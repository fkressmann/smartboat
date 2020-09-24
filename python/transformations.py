ROUND_TO_DECIMALS = 1


# Transformation functions, offset used to calibrate
def internal_voltage_5(value):
    # Voltage divider with 6.25V Utotal @ 1.1V Uout. ADC Uref = 1.1V
    return round((6.25 / 1024) * value, ROUND_TO_DECIMALS)


def internal_voltage_12(value):
    # Voltage divider with 17.05V Utotal @ 1.1V Uout. ADC Uref = 1.1V
    return round((17.05 / 1024) * value, ROUND_TO_DECIMALS)


def acs711(value, offset=0):
    # ADC Uref = Vin (5V). Same as Vcc of acs711, so proportions apply
    # 0A = Vin/2. 36.65A = Vin. 0.0716520039 = 73.3 / 1023 (no idea anymore why 1023 instead of 1024 but it works)
    return round(0.0716520039 * (value + offset) - 36.65, ROUND_TO_DECIMALS)


def shunt75mv(value, offset=5.58):
    # 75mV at 100A Shunt, 20 times amplified by AD8217 so 1.5V. 1.1V Uout 73.3A. ADC Uref = 1.1V
    # 0,071614583 = 73.3 / 1024
    offset = offset if value else 0  # Only apply offset if reading is not 0
    return round(0.071614583 * (value + offset), ROUND_TO_DECIMALS)


def tank(value):
    # PWM pulse high time in µS. 1100µS = 0%, 1900µS = 100%. Time divided by 8 is percentage
    print(f"Tank ist {value}")
    return round((value - 1100) / 8, 0)


def just_return(value):
    return value