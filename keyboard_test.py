import keyboard
import time# using module keyboard
time.sleep(1)
while True:  # making a loop
    try:  # used try so that if user pressed other than the given key error will not be shown
        if keyboard.is_pressed('q'):  # if key 'q' is pressed
            print('You Pressed A Key!')
            time.sleep(0.25)
        else:
            pass
    except:
        break  # if user pressed a key other than the given key the loop will break
