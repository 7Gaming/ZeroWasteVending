import os
import time
from datetime import datetime
from roboclaw_zwv import Roboclaw_zwv

serial_port = "/dev/ttyACM0"
baud_rate = 38400
address = 0x80
log_file_dir = "../../Logs"
    
try:
    roboclaw = Roboclaw_zwv(serial_port, baud_rate)
    if not roboclaw.Open():
        raise Exception(f"Unable to open port {serial_port}")
    
    roboclaw.execute_buffered_commands_with_logging(address,
                                                    [
                                                        lambda : roboclaw.SpeedDistanceM1(address, 200, 1400, 0),
                                                        lambda : roboclaw.SpeedDistanceM1(address, 100, 50, 0)
                                                    ],
                                                    2,
                                                    2
                                                    )
    roboclaw.graph_metrics(roboclaw.log_file.name)
    
finally:
    if roboclaw._port.is_open:
        roboclaw._port.close()


