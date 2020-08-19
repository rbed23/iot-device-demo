from datetime import datetime
import json
import threading
from time import sleep, time

import schedule

from iot_setup import iot_setup, publish_data, shadow_update
from board_setup import setup as board_setup


counter = 0


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


def ping_status(client, payload, shadow, report, sensor):
    global counter

    counter += 1

    time = f'{datetime.now()}'
    payload['mssg'] = 'ping'
    payload['time'] = time
    payload['ping'] = counter
    payload['LED'] = 'on' if round(sensor.value) == 1 else 'off'
    publish_data(client, payload, 'myTopic')

    report['time'] = time
    report['property'] = counter
    report['LED'] = 'on' if round(sensor.value) == 1 else 'off'
    shadow_update(shadow, report, 'update')


def event_status(client, payload, shadow, report, sensor):
    global counter

    time = f'{datetime.now()}'
    payload['time'] = time
    payload['ping'] = counter
    payload['LED'] = 'on' if round(sensor.value) == 1 else 'off'
    publish_data(client, payload, 'myTopic')

    report['time'] = time
    report['property'] = counter
    report['LED'] = 'on' if round(sensor.value) == 1 else 'off'
    shadow_update(shadow, report, 'update')


def run_tgsn():

    pwd = '/opt/tgsn/iot-demo/keys/'

    myDevice = iot_setup(pwd)

    devShadow = myDevice[0]
    devClient = myDevice[1]
    devPayload = myDevice[2]

    devPayload = {}
    shadow_report = {'property': counter, 'state': 'pinging'}

    board_parts = board_setup()

    board = board_parts[0]
    button = board_parts[1]
    sensor = board_parts[2]


    # Schedule Reporting Service(s)
    schedule.every(10).seconds.do(ping_status, devClient, devPayload, devShadow, shadow_report, sensor)

    # Initialize Sensor State
    led_state = round(sensor.value)

    while True:

        # Run Scheduler(s)
        schedule.run_pending()

        # Button Press Event
        if button.is_pressed:
            board.off()

            devPayload['LED'] = 'on' if round(sensor.value) == 1 else 'off'
            devPayload['time'] = f'{datetime.now()}'
            devPayload['mssg'] = 'button pressed'

            publish_data(devClient, devPayload, 'myTopic')

            sleep(0.1)
            board.on()

        # Toggle LED Event
        if round(sensor.value) != led_state:
            print('toggled!')

            devPayload['mssg'] = 'LED toggled'
            shadow_report['last_event'] = 'LED toggled'
            event_status(devClient, devPayload, devShadow, shadow_report, sensor)
            led_state = round(sensor.value)

        # Sleep
        sleep(0.1)


if __name__ == "__main__":

    run_tgsn()
