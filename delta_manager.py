from board_setup import *

def led_main_handler(action):
    '''
    Handles LED Main status

    :desc action: either 'on' or 'off'
    :type action: str
    '''
    if action == 'on':
        led_main.on()
    elif action == 'off':
        led_main.off()
    else:
        pass
