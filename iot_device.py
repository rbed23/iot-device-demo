from datetime import datetime
import json
import threading
from time import sleep, time

import schedule

from iot_controller import *
from board_setup import *


counter = 0


def ping_status():
    global counter
    counter += 1


def event_status(client, payload, shadow, report, sensor, event_type=""):
    if event_type == 'ping':
        ping_status()
        payload['mssg'] = 'pinging'

    global counter

    led_switch_state = 'on' if get_switch_state(sensor) == 1 else 'off'
    time = f'{datetime.now()}'

    payload['time'] = time
    payload['ping'] = counter
    payload['LED_switch'] = led_switch_state
    client.publish('myTopic', json.dumps(payload), 0)

    report['time'] = time
    report['property'] = counter
    report['LED_switch'] = led_switch_state
    shadow.shadowUpdate(format_shadow_report(report), customShadowCallback_Update, 5)


def format_shadow_report(report):
    tmp = {
        'state': {
            'reported': report
        }
    }
    return json.dumps(tmp)


def get_switch_state(sensor):
    # Button == 0 if pressed
    # Switch == 0 if 'off'

    # Return True if powered
    # else return False
    #return not sensor.value
    return round(sensor.value)


def button_press_event(payload, shadow):
    print('button pressed!')
    led_main.off()

    payload['mssg'] = 'button pressed'
    shadow['last_event'] = 'button pressed'
    shadow['LED_main'] = 'off'
    event_status(devClient, payload, devShadow, shadow, sensor)

    sleep(0.5)

    led_main.on()
    shadow['LED_main'] = 'on'
    event_status(devClient, payload, devShadow, shadow, sensor)


def toggle_event(payload, shadow):
    print('toggled!')

    payload['mssg'] = 'LED toggled'
    shadow['last_event'] = 'LED toggled'
    led_switch_state = get_switch_state(sensor)

    # Switch LED main
    if led_switch_state == 1:
        led_main.on()
        shadow['LED_main'] = 'on'

    else:
        led_main.off()
        shadow['LED_main'] = 'off'

    event_status(devClient, payload, devShadow, shadow, sensor)


def run_tgsn():

    myDevice = iot_setup()

    devShadow = myDevice[0]
    devClient = myDevice[1]
    devPayload = myDevice[2]

    shadow_report = {'property': counter, 'state': 'pinging'}

    # Schedule Reporting Service(s)
    schedule.every(10).seconds.do(event_status, devClient, devPayload, devShadow, shadow_report, sensor, 'ping')

    # Initialize Sensor State
    led_switch_state = get_switch_state(sensor)

    shadow_report['LED_switch'] = 'on' if led_switch_state == 1 else 'off'
    shadow_report['LED_main'] = 'on'
    shadow_report['last_event'] = 'initialized'
    event_status(devClient, devPayload, devShadow, shadow_report, sensor)

    while True:

        # Run Scheduler(s)
        schedule.run_pending()

        # Button Press Event
        if button.is_pressed:
            btn_thread = threading.Thread(
                target=button_press_event,
                args=(devPayload, shadow_report))
            btn_thread.start()
            
        # Toggle LED Event
        if get_switch_state(sensor) != led_switch_state:
            tgl_thread = threading.Thread(
                target=toggle_event,
                args=(devPayload, shadow_report))
            tgl_thread.start()
        
        # Sleep
        sleep(0.1)


if __name__ == "__main__":

    run_tgsn()
