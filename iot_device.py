import schedule

from datetime import datetime
import json
from threading import Thread
from time import sleep

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
    '''
    Create shadow state report doc, ready for shadow update

    :desc report: device state to be reported
    :type report: dict
    '''

    tmp = {
        'state': {
            'reported': report
        }
    }
    return json.dumps(tmp)


def get_switch_state(sensor):
    # If sensor object is of type 'Button'
    # Button == 0 if pressed, else returns 1

    # If sensor object is of type 'LightSensor'
    # Switch == 0 if 'off', else returns 1

    # If Button:
        # Return True if powered
        # else return False
    #return not sensor.value
    
    # If LightSensor:
        # Return 1 if powered
        # else return 0
    return round(sensor.value)


def event(payload, shadow, client, dev, event_type):
    '''
    Manages event actions for a device

    :desc event_type: expresses the specific event requiring action
    :type event_type: str
    '''

    if event_type == 'button_press':
        print('button pressed!')

        led_main.off()

        payload['mssg'] = 'button pressed'
        payload['LED_main'] = 'off'
        shadow['last_event'] = 'button pressed'
        shadow['LED_main'] = 'off'
        event_status(client, payload, dev, shadow, sensor)

        sleep(0.5)

        led_main.on()
        payload['LED_main'] = 'on'
        shadow['LED_main'] = 'on'

    elif event_type == 'toggle':
        print('toggled!')

        payload['mssg'] = 'LED toggled'
        shadow['last_event'] = 'LED toggled'
        led_switch_state = get_switch_state(sensor)

        if led_switch_state == 1:
            led_main.on()
            shadow['LED_main'] = 'on'
        else:
            led_main.off()
            shadow['LED_main'] = 'off'

    event_status(client, payload, dev, shadow, sensor)


def run_tgsn():

    myDevice = iot_setup()

    devShadow = myDevice[0]
    devClient = myDevice[1]
    devPayload = myDevice[2]

    shadow_report = {'property': counter, 'state': 'pinging'}

    # Schedule Reporting Service(s)
    schedule.every(10).seconds.do(
        event_status,
        devClient,
        devPayload,
        devShadow,
        shadow_report,
        sensor,'ping')

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

            # Create Thread
            btn_thread = Thread(
                target=event,
                args=(devPayload, shadow_report, devClient, devShadow, 'button_press'))
            btn_thread.start()
            
        # Toggle LED Event
        if get_switch_state(sensor) != led_switch_state:
            
            # Set New Switch State
            led_switch_state = get_switch_state(sensor)

            # Create Event Thread
            tgl_thread = Thread(
                target=event,
                args=(devPayload, shadow_report, devClient, devShadow, 'toggle'))
            tgl_thread.start()
        
        # Sleep
        sleep(0.1)


if __name__ == "__main__":

    run_tgsn()
