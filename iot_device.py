from gpiozero import LED, Button, LightSensor

from datetime import datetime
import json
from signal import pause
from time import sleep, time

from iot_setup import iot_setup, publish_data, shadow_update

def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
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

def run_tgsn():

    pwd = '/mnt/c/Users/Ryan/Desktop/cli-git-folder/tgsn/iot-demo/keys/'

    myDevice = iot_setup(pwd)

    devShadow = myDevice[0]
    devClient = myDevice[1]
    devPayload = myDevice[2]
    
    counter = 0

    devPayload = {'mssg': 'ping'}
    shadow_report = {'property': counter, 'state': 'pinging'}

    while True:

        devPayload['time'] = f'{datetime.now()}'
        devPayload['ping'] = counter
        publish_data(devClient, devPayload, 'myTopic')

        shadow_report['time'] = f'{datetime.now()}'
        shadow_report['property'] = counter
        shadow_update(devShadow, shadow_report, 'update')
        
        counter += 1
        sleep(10)

if __name__ == "__main__":
    
    run_tgsn()