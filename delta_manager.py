from board_setup import *

def led_main_handler(action):
    if action == 'on':
        led_main.on()
    elif action == 'off':
        led_main.off()
    else:
        pass

