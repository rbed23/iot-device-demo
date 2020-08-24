from datetime import datetime
import json
import threading
from time import sleep, time

import schedule

from iot_controller import *
from board_setup import *


counter = 0

'''
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("property: " + str(payloadDict["state"]["reported"]["property"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")
'''

def ping_status(client, payload, shadow, report, sensor):
    global counter

    counter += 1

    time = f'{datetime.now()}'
    payload['mssg'] = 'ping'
    payload['time'] = time
    payload['ping'] = counter
    payload['LED_switch'] = 'on' if round(sensor.value) == 1 else 'off'
    publish_data(client, payload, 'myTopic')

    report['time'] = time
    report['property'] = counter
    report['LED_switch'] = 'on' if round(sensor.value) == 1 else 'off'
    shadow.shadowUpdate(json.dumps(report), customShadowCallback_Update, 5)


def event_status(client, payload, shadow, report, sensor):
    global counter

    time = f'{datetime.now()}'
    payload['time'] = time
    payload['ping'] = counter
    payload['LED_switch'] = 'on' if round(sensor.value) == 1 else 'off'
    client.publish('myTopic', payload, 0)

    report['time'] = time
    report['property'] = counter
    report['LED_switch'] = 'on' if round(sensor.value) == 1 else 'off'
    shadow.shadowUpdate(json.dumps(report), customShadowCallback_Update, 5)


def format_shadow_report(report):
    tmp = {
        'state': {
            'reported': report
        }
    }
    return json.dumps(tmp)


def run_tgsn():

    myDevice = iot_setup()

    devShadow = myDevice[0]
    devClient = myDevice[1]
    devPayload = myDevice[2]

    shadow_report = {'property': counter, 'state': 'pinging'}

    # Schedule Reporting Service(s)
    schedule.every(10).seconds.do(ping_status, devClient, devPayload, devShadow, shadow_report, sensor)

    # Initialize Sensor State
    led_switch_state = round(sensor.value)

    shadow_report['LED_switch'] = 'on' if led_switch_state == 1 else 'off'
    shadow_report['LED_main'] = 'on'
    devShadow.shadowUpdate(json.dumps(shadow_report), customShadowCallback_Update, 5)

    while True:

        # Run Scheduler(s)
        schedule.run_pending()

        # Button Press Event
        if button.is_pressed:
            board.off()

            devPayload['LED_switch'] = 'on' if round(sensor.value) == 1 else 'off'
            devPayload['time'] = f'{datetime.now()}'
            devPayload['mssg'] = 'button pressed'

            devClient.publish('myTopic', devPayload, 0)

            sleep(0.1)
            board.on()

        # Toggle LED Event
        if round(sensor.value) != led_switch_state:
            print('toggled!')

            devPayload['mssg'] = 'LED toggled'
            shadow_report['last_event'] = 'LED toggled'
            event_status(devClient, devPayload, devShadow, shadow_report, sensor)
            led_switch_state = round(sensor.value)

        # Switch LED main
        if led_switch_state:
            led_main.on()
            shadow_report['LED_main'] = 'on'
            devShadow.shadowUpdate(
                format_shadow_report(shadow_report),
                customShadowCallback_Update, 5)
        else:
            led_main.off()
            shadow_report['LED_main'] = 'off'
            devShadow.shadowUpdate(
                format_shadow_report(shadow_report),
                customShadowCallback_Update, 5)

        # Sleep
        sleep(0.1)


if __name__ == "__main__":

    run_tgsn()
