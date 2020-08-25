from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

from datetime import datetime
import json
import os
from time import sleep

from delta_manager import *


def customMssgCallback(client, userdata, message):
    print("Received a new message:")
    print(str(message.payload))
    print("from topic: ")
    print(str(message.topic))
    print("--------------\n\n")


def customShadowCallback(payload, responseStatus, token):
    print(f'Payload: {str(payload)}')
    print(f'Status: {responseStatus}')
    print(f'Token: {token}')
    print("--------------\n\n")


def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        if [x for x in payloadDict['state'].keys()][0] == 'reported':
            print("Reported state: " + str(payloadDict["state"]["reported"]))
        else:
            print("Desired state: " + str(payloadDict["state"]["desired"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")
        print(json.dumps(payload, indent=2))


def customShadowCallback_Delta(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    payloadDict = json.loads(payload)
    print("++++++++DELTA++++++++++")
    print(json.dumps(payloadDict, indent=2))
    print("Desired state: " + str(payloadDict["state"]))
    print("version: " + str(payloadDict["version"]))
    print("+++++++++++++++++++++++\n\n")

    delta_handler(payloadDict['state'])


def customShadowCallback_Delete(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")
    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")


def delta_handler(delta_state):

    print('in delta handler')
    aar = {}
    for k, v in delta_state.items():
        if k == 'LED_main':
            if v == 'on' or v == 'off':
                led_main_handler(v)
                aar['LED_main'] = v
            else:
                print('Invalid input value for LED_main; try "on" or "off"')

    
    final_report = {'state': {'reported': aar}}
    print(json.dumps(final_report, indent=2))

    myDeviceShadow.shadowUpdate(
        json.dumps(final_report),
        customShadowCallback_Update, 5)



def iot_setup():

    # Get device configuration details
    with open('config.json', 'r') as cfg:
        device = json.load(cfg)
    thing_uid = device['thing_uid']

    # Get keyfile paths
    key_dir = f'{os.getcwd()}/keys/'

    if os.path.exists(key_dir):
        try:
            with open(f'{key_dir}{thing_uid}.pem.crt', 'r') as r:        
                root_file = f'{key_dir}RootCA.pem'
                key_file = f'{key_dir}{thing_uid}.private.key'
                crt_file = f'{key_dir}{thing_uid}.pem.crt'
        except FileNotFoundError as err:
            print(f'Issue with filenames in <{key_dir}>')
            print(str(err))
    else:
        print(f'Path <{key_dir} does not exist; verify working directory')


    # Certificate based connection
    myShadowClient = AWSIoTMQTTShadowClient(thing_uid)
    print(f'Shadow Client: {myShadowClient}')
    print(f'Shadow Client ID: {thing_uid}')

    # Configuration for TLS mutual authentication
    myShadowClient.configureEndpoint(
        device['endpt'], int(device['prt']))
    myShadowClient.configureCredentials(
        root_file,
        key_file,
        crt_file)

    myShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
    myShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

    print('shadow client configured')

    myShadowClient.connect()

    print('shadow client connected')

    # Create a device shadow instance using persistent subscriptions
    myDeviceShadow = myShadowClient.createShadowHandlerWithName(thing_uid, True)

    with open('default_payloads.json', 'r') as defaults:
        tmp = json.load(defaults)

    shadow_doc = tmp['default_shadow']
    payload = tmp['default_payload']


    # Shadow operations
    #init_shadow = myDeviceShadow.shadowGet(customShadowCallback, 5)

    shadow_doc['state']['reported']['property'] = 0
    shadow_doc['state']['reported']['state'] = 'initialized'
    shadow_doc['state']['reported']['time'] = f'{datetime.now()}'
    myDeviceShadow.shadowUpdate(
        json.dumps(shadow_doc),
        customShadowCallback_Update, 5)
    #myDeviceShadow.shadowDelete(customShadowCallback_Delete, 5)
    myDeviceShadow.shadowRegisterDeltaCallback(customShadowCallback_Delta)
    #myDeviceShadow.shadowUnregisterDeltaCallback()

    print('shadow handler configured')


    # MQTT Client operations
    myMQTTClient = myShadowClient.getMQTTConnection()

    payload['mssg'] = 'MQTT live'
    payload['time'] = f'{datetime.now()}'
    payload['uid'] = thing_uid

    myMQTTClient.subscribe('myTopic', 1, customMssgCallback)
    sleep(0.1)
    myMQTTClient.publish("myTopic", json.dumps(payload), 0)

    print('mqtt client connection active') 

    return (myDeviceShadow, myMQTTClient, payload)
