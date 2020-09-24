from flask import request, jsonify
from python.__main__ import app, settings, new_values, old_values
from python.helper import serial_send


@app.route('/')
def use_serial():
    return 'No command specified. Use specific endpoint instead.'


@app.route('/settings')
def edit_settings():
    setting = request.args.get('s', type=str)
    value = request.args.get('v', type=int)
    try:
        serial_send(settings[setting], value)
    except KeyError:
        return f"Setting {setting} could not be found"
    except Exception as ex:
        return f"Unknown error: {type(ex)}, {ex}"
    return f"Successfully set {setting} to {value}"


@app.route('/led-salon')
def led1_route():
    serial_send(settings["led-salon"], request.args.get('val', type=int))
    return "ok"


@app.route('/led-vorschiff')
def led2_route():
    serial_send(settings["led-vorschiff"], request.args.get('val', type=int))
    return "ok"


@app.route('/tanksensor')
def tanksensor_route():
    value = request.args.get('val', type=int)
    serial_send(settings['tanksensor'], value)
    return 'ok'


# ToDo: State management
@app.route('/heating')
def heating_route():
    channel = request.args.get('ch', type=str)
    value = request.args.get('val', type=int)
    serial_send(settings[channel], value)
    return 'ok'


@app.route('/debug')
def debug_data():
    return jsonify({'new_values': new_values,
                    'old_values': old_values,
                    'settings': settings}, )