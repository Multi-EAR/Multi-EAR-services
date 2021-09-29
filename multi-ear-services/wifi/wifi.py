import RPi.GPIO as GPIO
import time
import os


def gpio_trigger(pin: int = 7):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    while True:
        input_state = GPIO.input(pin)
        if input_state == False:
            print('Button Pressed')
            # os.system('/home/pi/Downloads/PuttingItAllTogether.py')
            time.sleep(10)


def main():
    gpio_trigger()

if __name__ == "__main__":
    main()
