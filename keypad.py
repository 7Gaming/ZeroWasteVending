import RPi.GPIO as GPIO

class keypad:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        
        self.pins = [29, 31, 33, 35, 37, 38, 40]
        self.columns = self.pins[0:3]
        self.rows = self.pins[3:7]
        self.keys = [
                        ['1','2','3'],
                        ['4','5','6'],
                        ['7','8','9'],
                        ['*','0','#']
                    ]
        
        self.__set_all_pins_to_input__()
        
    def __set_all_pins_to_input__(self):
        for pin in self.pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    def pressed_keys(self):
        pressed = []
        self.__set_all_pins_to_input__()
        for row, row_pin in enumerate(self.rows):
            GPIO.setup(row_pin, GPIO.OUT)
            GPIO.output(row_pin, GPIO.LOW)
            for col, col_pin in enumerate(self.columns):
                if not GPIO.input(col_pin):
                    pressed.append(self.keys[row][col])
            GPIO.setup(row_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        return pressed
