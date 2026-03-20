import Jetson.GPIO as GPIO

class GPIOController:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        self.pins = {}

    def setup_out(self, pin):
        GPIO.setup(pin, GPIO.OUT)   #pin是该排针的编号（从1开始）
        self.pins[pin] = "OUT"

    def setup_in(self, pin):
        GPIO.setup(pin, GPIO.IN)
        self.pins[pin] = "IN"

    def write(self, pin, value):
        GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)

    def read(self, pin):
        return GPIO.input(pin)

    def cleanup(self):
        GPIO.cleanup()