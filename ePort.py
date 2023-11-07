import serial


class ePort:
    def __init__(self, comport, rate, timeout=0.01, retries=3):
        self.comport = comport
        self.rate = rate
        self.timeout = timeout;
        self._trystimeout = retries
        self._crc = 0;

    def send_command(self, command, data=[]):
        command_identifier = command[0]
        if len(data) > 0:
            data = '\x1e' + '\x1e'.join(data)
        else:
            data = ""
        message = str.encode(command_identifier) + str.encode(data)
        crc_required = command[2]
        if crc_required:
            message = message + self.calculate_crc16(message)
        message = message + b'\r'
        self._port.write(message)
        response = b''
        while 1:
            response = response + self._port.read()
            if len(response) == 0:
                continue
            if (response[0] == 0x6) or (response[0] == 0x15) or (response[-1] == 0xd):
                return self.parse_response(response)
            
    def parse_response(self, response):
        #response = response.decode('ASCII')
        if response[0] == 0x6 or response[0] == 0x15:
            return ePort.RESPONSES[response.decode('ASCII')]
        if response[-1] != 0xd:
            raise Exception('Response not terminated with carriage return')
        response = response[:-1]
        response_code = response.split(b'\x1e')[0].decode('ASCII')
        response_descriptor = ePort.RESPONSES[response_code]
        crc_present = response_descriptor[2]
        #Extract crc if needed
        if crc_present:
            response, crc = response[0:-2], response[-2:]
        response = response.decode("ASCII")
        fields = response_descriptor[2]
        values = response.split('\x1e')[1:]
        short_description = response_descriptor[0]
        long_description = response_descriptor[1]
        response = (response_code, short_description, long_description, list(zip(fields, values)), crc if crc_present else None)
        return response
            
    def calculate_crc16(self, data):
        if (type(data) == str):
            data = str.encode(data)
        if (type(data) != bytes) and (type(data) != bytearray):
            raise Exception("Unsupported data type.")
        new_crc = 0xFFFF
        for char in data:
                new_crc = ((new_crc << 8) & 0xFFFF) ^ self.crc_table[(new_crc >> 8) ^ (char)]
        return new_crc.to_bytes(2, 'big')

    def Open(self):
        try:
            self._port = serial.Serial(port=self.comport, baudrate=self.rate, timeout=1, interCharTimeout=self.timeout)
        except:
            return 0
        return 1

    #Commands (command_identifier, description, crc_required)
    STATUS = ("1", "Get ePort status and responses", False)
    REBOOT = ("2", "Instructs ePort to reboot", False)
    RESET = ("3", "Instructs ePort to reset", False)
    PROCESS_UPDATE = ("4", "Instructs ePort to contact server for updates", False)
    ENABLE = ("5", "Enables ePort to accept credit cards", False)
    DISABLE = ("6", "Disables ePort from accepting credit cards", False)
    BEGIN_FILE_DOWNLOAD = ("7", "Instructs ePort to download file from server", False)
    TERMINATE_FILE_TRANSFER = ("8", "Instructs ePort to terminate file transfers", False)
    ACQUIRE_SIGNAL_QUALITY = ("9", "Returns the signal quality of ePort’s modem on the next STATUS request", False)
    ACQUIRE_TIME_AND_DATE = ("10", "Returns time and date ePort ePort is set to on the next STATUS request", False)
    EVENT_LOG = ("11", "Internal USAT use", False)
    ACQUIRE_EPORT_CONFIG_DATA = ("12", "Returns ePort’s configuration information on the next STATUS request", False)
    ACQUIRE_TRANSACTION_ID = ("13", "Returns the current credit transaction ID on the next STATUS request", False)
    CONFIG = ("20", "Sends Kiosk config information to ePort", True)
    AUTH_REQ = ("21", "Send authorization request for set amount", True)
    TRANSACTION_RESULT = ("22", "Sends sales result information to ePort", True)
    CASHREPORT = ("23", "Send cash sales result to information to ePort", True)
    FILE_READY_FOR_UPLOAD = ("24", "Notify ePort that Kiosk ready to send file", True)
    FILE_RECORD = ("25", "Sends file information to ePort", True)
    DISP_MESSAGE = ("26", "Sends information to display on card reader", True)

    #Responses (response_code, response_identifier, description, [return_value], crc_present)
    RESPONSES = {
                    "\x06": ("ACK", "ePort has acknowledged a command", [], False),
                    "\x15": ("NAK", "command not acknowleged", [], False),
                    "0": ("OK", "ePort has nothing to report. Idle, initialized with a cell connection", [], False),
                    "1": ("BUSY", "ePort processing previous command", [], False),
                    "2": ("AUTH_OK", "Card authorization successful", ["auth_amt", "masked_card_data"], True),
                    "3": ("AUTH_DECL", "Bank declined authorization; bank reason provided", ["auth_code", "Msg"], True),
                    "4": ("SESSION_TO", "Session timeout, brief description where it occurred", ["msg"], False),
                    "5": ("INITIALIZING", "ePort is initializing, establishing a cell connection", [], False),
                    "6": ("DISABLED", "ePort is in disabled state", [], False),
                    "7": ("XPCTNG_SWIPE", "ePort waiting for card swipe", [], False),
                    "8": ("AUTHORIZING", "ePort is authorizing the credit card", [], False),
                    "9": ("XPCTNG_TRANS_RESULT", "ePort waiting on Kiosk transaction result", [], False),
                    "10": ("INVALID_CMD", "ePort received bad or out of sequence command from Kiosk", ["cmnd", "msg"], False),
                    "11": ("FILE_AVAILABLE", "attributes of a file that is available on the server to be downloaded to the Kiosk", ["file_name", "file_type", "file_size", "records_total", "record_size"], True),
                    "12": ("XPCTNG_RECORD_UPLOAD", "ePort ready to receive file from Kiosk", [], False),
                    "13": ("CANCEL_FILE_XFER", "ePort response to cancel file upload or download", [], False),
                    "14": ("SIGNAL_QUALITY", "Response to Command 9", ["RSSI", "BER"], False),
                    "15": ("TIME&DATE = Response to Command 10 current GMT & local time (set in USALive)", ["GMT_time", "GMT_date", "GMT_offset", "local_time", "local_date"], False),
                    "16": ("EPORT_CONFIG", "Response to Command 12", ["serial_number", "software_revision"], False),
                    "17": ("TRANSACTION_ID", "Response to Command 13, 10-digit value", ["transaction_id"], False),
                    "18": ("END_BUTTON_PRESSED", "Indicates cardholder pressing card reader button", [], False),
                    "30": ("FAIL_NETWORK", "Provider network (cell phone) error", [], False),
                    "31": ("FAIL_MODEM", "ePort modem failure", [], False),
                    "32": ("FAIL_SERVER", "USAT server failure", [], False),
                    "33": ("FAIL_TIME_REQUEST", "Command 10, ePort not synchronized with server", [], False)
                }

    crc_table =     [
                        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
                        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
                        0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
                        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
                        0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
                        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
                        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
                        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
                        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
                        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
                        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
                        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
                        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
                        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
                        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
                        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
                        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
                        0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
                        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
                        0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
                        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
                        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
                        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
                        0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
                        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
                        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
                        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
                        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
                        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
                        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
                        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
                        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
                    ]


if __name__ == '__main__':
    _ePort = ePort("/dev/ttyUSB0", 9600)
    if _ePort.Open():
        print("Use _ePort to communicate")
    else:
        print("Unable to connect to ePort")
