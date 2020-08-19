from gpiozero import LED, Button, LightSensor
from time import sleep, time


def setup():
    board_led = LED(17)
    push_btn = Button(2)
    sensor = LightSensor(18)

    board_led.on()

    parts = (board_led, push_btn, sensor)

    return parts

if __name__ == '__main__':
    setup()
