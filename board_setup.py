from gpiozero import LED, Button, LightSensor
from gpiozero import DigitalInputDevice
from time import sleep, time


board = LED(4)
led_main = LED(18)
button = Button(2)
sensor = Button(27)


board.on()
led_main.on()