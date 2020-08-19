from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient

from datetime import datetime
import json
from time import sleep


uid = 'tgsn-iot-sensor'


def customMssgCallback(client, userdata, message):
    print("Received a new message:")
    print(json.dumps(json.loads(message.payload)))
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


def customShadowCallback(payload, responseStatus, token):
    print("Getting Shadow")
    print(f'Payload: {payload}')
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
        print("property: " + str(payloadDict["state"]["reported"]["property"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")


def customShadowCallback_Delta(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    print(responseStatus)
    payloadDict = json.loads(payload)
    print("++++++++DELTA++++++++++")
    print("property: " + str(payloadDict["state"]["property"]))
    print("version: " + str(payloadDict["version"]))
    print("+++++++++++++++++++++++\n\n")


def customShadowCallback_Delete(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")
    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")


def iot_setup(pwd):
    # For certificate based connection
    myShadowClient = AWSIoTMQTTShadowClient(uid)
    print(f'Shadow Client: {myShadowClient}')
    print(f'Shadow Client ID: {uid}')

    # Configurations
    # For TLS mutual authentication
    myShadowClient.configureEndpoint(
        "aavho6lvgzt85-ats.iot.us-east-2.amazonaws.com", 8883)
    myShadowClient.configureCredentials(
        f'{pwd}AmazonRootCA1.pem',
        f'{pwd}tgsn_iot-private.pem.key',
        f'{pwd}tgsn_iot-certificate.pem.crt.txt')

    myShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
    myShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
    myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

    print('shadow client configured')

    myShadowClient.connect()

    print('shadow client connected')

    # Create a device shadow instance using persistent subscription
    myDeviceShadow = myShadowClient.createShadowHandlerWithName(uid, True)

    myJSONPayload = {
        "state": {
            "reported":{
                "property": 0,
                "state": 'initialized'
            }
        }
    }

    # Shadow operations
    #myDeviceShadow.shadowGet(customShadowCallback, 5)

    myJSONPayload['state']['reported']['time'] = f'{datetime.now()}'
    myDeviceShadow.shadowUpdate(json.dumps(myJSONPayload), customShadowCallback_Update, 5)

    #myDeviceShadow.shadowGet(customShadowCallback, 5)
    #myDeviceShadow.shadowDelete(customShadowCallback_Delete, 5)
    #myDeviceShadow.shadowRegisterDeltaCallback(customShadowCallback_Delta)
    #myDeviceShadow.shadowUnregisterDeltaCallback()

    print('shadow handler configured')

    # MQTT Client operations
    myMQTTClient = myShadowClient.getMQTTConnection()


    payload = {
        'uid': uid,
        'mssg': 'MQTT live',
        'time': f'{datetime.now()}',
    }

    myMQTTClient.subscribe('myTopic', 1, customMssgCallback)
    sleep(0.2)

    print('publishing')

    myMQTTClient.publish("myTopic", json.dumps(payload), 0)

    device = (myDeviceShadow, myMQTTClient, payload)

    return device


def publish_data(client, payload, topic):
    client.publish(topic, json.dumps(payload), 0)


def shadow_update(shadow, report, action):
    document = {'state': {'reported': report}}

    if action == 'get':
        print('getting shadow')
    
    if action == 'update':
        shadow.shadowUpdate(json.dumps(document), customShadowCallback_Update, 5)

    if action == 'delete':
        print('deleting shadow')
