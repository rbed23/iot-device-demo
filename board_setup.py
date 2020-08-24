from gpiozero import LED, Button, LightSensor
from time import sleep, time


board = LED(17)
led_main = LED(18)
button = Button(2)
sensor = LightSensor(27)


board.on()
led_main.on()