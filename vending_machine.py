import time
import math
from I2C_LCD_driver import lcd
from roboclaw_zwv import Roboclaw_zwv
from keypad import keypad
from ePort import ePort

roboclaw_serial_port = "/dev/ttyACM0"
roboclaw_baud_rate = 38400
roboclaw_address = 0x80

ePort_serial_port = "/dev/ttyUSB0"
ePort_baud_rate = 9600

products = {
                '1': 'Lucky Charms',
                '2': 'Fruit Loops'
             }
prices = {
                '1': 2.00,
                '2': 1.75
    
            }
amounts = {
                '1': .5,
                '2': 1.0,
                '3': 1.5,
                '4': 2.0
          }
amount_descriptions = {
                '1': '1/2 cup',
                '2': '1 cup',
                '3': '1 1/2 cup',
                '4': '2 cups'
          }
confirmations = {
                '1': 'Confirm',
                '2': 'Cancel'
              }

class Vending_Machine:
    def __init__(self):
        self.lcd = lcd()
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string("Booting...", 2, 5)
        
        self.roboclaw = Roboclaw_zwv(roboclaw_serial_port, roboclaw_baud_rate)
        if not self.roboclaw.Open():
            raise Exception(f"Unable to open port {roboclaw_serial_port}")
        
        self.ePort = ePort(ePort_serial_port, ePort_baud_rate)
        if not self.ePort.Open():
            raise Exception(f"Unable to open port {ePort_serial_port}")
        self.ePort.send_command(ePort.DISABLE)
        
        self.keypad = keypad()
        self.pressed_keys = []
        
    def _get_product_selection(self, wait_time = 30):
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string("Please select", 2, 5)
        self.lcd.lcd_display_string("product", 3, 6)
        
        begin_time = time.time()
        while True:
            time.sleep(.1)
            if (wait_time > 0) and (time.time() - begin_time) > wait_time:
                return None
            pressed_keys = self.keypad.pressed_keys()
            if len(pressed_keys) != 1:
                continue
            if pressed_keys[0] not in products:
                continue
            return pressed_keys[0]
    
    def _get_amount_selection(self, wait_time = 30):
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string("1: 1/2 cup", 1, 4)
        self.lcd.lcd_display_string("2: 1 cup", 2, 4)
        self.lcd.lcd_display_string("3: 1 1/2 cup", 3, 4)
        self.lcd.lcd_display_string("4: 2 cups", 4, 4)
        
        begin_time = time.time()
        while True:
            time.sleep(.1)
            if (wait_time > 0) and (time.time() - begin_time) > wait_time:
                return None
            pressed_keys = self.keypad.pressed_keys()
            if len(pressed_keys) != 1:
                continue
            if pressed_keys[0] not in amounts:
                continue
            return pressed_keys[0]
    
    def _get_selection_confirmation(self, wait_time = 30):
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string(amount_descriptions[self.amount_selection] + ' of ', 1)
        self.lcd.lcd_display_string(products[self.product_selection], 2)
        self.lcd.lcd_display_string(f'${self.selection_price/100:0.2f}', 3)
        self.lcd.lcd_display_string("1-confirm 2-cancel", 4)
        
        begin_time = time.time()
        while True:
            time.sleep(.1)
            if (wait_time > 0) and (time.time() - begin_time) > wait_time:
                return None
            pressed_keys = self.keypad.pressed_keys()
            if len(pressed_keys) != 1:
                continue
            if pressed_keys[0] not in confirmations:
                continue
            return pressed_keys[0]
        
    def _authorize_payment(self, wait_time = 30):
        auth_req_response = self.ePort.send_command(ePort.AUTH_REQ, [str(self.selection_price)])
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string('Please swipe card...', 1)

        begin_time = time.time()
        while True:
            status = self.ePort.send_command(ePort.STATUS)
            if status[0] == "2":
                return True
            if status[0] == "3":
                return False
            if (wait_time > 0) and (time.time() - begin_time) > wait_time:
                return None
            time.sleep(.5)
            
    def _dispense_product(self):
        self.lcd.lcd_clear()
        self.lcd.lcd_display_string('Dispensing...', 1)
        self.roboclaw.execute_buffered_commands_with_logging(roboclaw_address,
                                                    [
                                                        lambda : self.roboclaw.SpeedDistanceM1(roboclaw_address, 200, 1400, 0),
                                                        lambda : self.roboclaw.SpeedDistanceM1(roboclaw_address, 100, 50, 0)
                                                    ]
                                                    )
        return True
    
    def _send_transaction_result(self):
        self.ePort.send_command(ePort.TRANSACTION_RESULT, ['1', '1', str(self.selection_price), '999', 'print'])
        self.ePort.send_command(ePort.ACQUIRE_TRANSACTION_ID)
        status = self.ePort.send_command(ePort.STATUS)
        while status[0] != "17":
            status = self.ePort.send_command(ePort.STATUS)
            time.sleep(.1)
        return status[3][0]
            
        
    def vend_loop(self):
        while True:
            ePort_status = self.ePort.send_command(ePort.STATUS)
            if ePort_status == '9':
                self.ePort.send_command(ePort.RESET)
                time.sleep(3)
            elif ePort_status != '6':
                self.ePort.send_command(ePort.DISABLE)
                time.sleep(3)
            
            self.product_selection = self._get_product_selection(0)
            if not self.product_selection:
                continue
            
            self.amount_selection = self._get_amount_selection()
            if not self.product_selection:
                continue
            
            self.selection_price = math.ceil(100 * prices[self.product_selection] * amounts[self.amount_selection])
            
            self.selection_confirmation = self._get_selection_confirmation()
            if self.selection_confirmation != '1':
                continue
            
            if not self._authorize_payment():
                continue
            
            if self._dispense_product():
                transaction_ID = self._send_transaction_result()
                self.ePort.send_command(ePort.DISABLE)
                self.lcd.lcd_clear()
                self.lcd.lcd_display_string('Thank you for ', 2, 3)
                self.lcd.lcd_display_string('your purchase!', 3, 3)
                time.sleep(5)
            else:
                self.lcd.lcd_clear()
                self.lcd.lcd_display_string('Something went wrong', 2)
                self.lcd.lcd_display_string('Purchase cancelled', 3)
                self.ePort.send_command(ePort.RESET)
                time.sleep(5)

            self.lcd.lcd_clear()
            self.lcd.lcd_display_string('More to come...', 1)
            time.sleep(5)


if __name__ == '__main__':
    _vending_machine = Vending_Machine()
    _vending_machine.vend_loop()