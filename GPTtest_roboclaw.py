# Import necessary libraries
import os
import time
from datetime import datetime
from roboclaw_zwv import Roboclaw_zwv  # Import the custom Roboclaw class

# Define serial port and communication settings
serial_port = "/dev/ttyACM0"  # Serial port for communication
baud_rate = 38400  # Baud rate for serial communication

# Address of the Roboclaw device
address = 0x80  # Roboclaw address (change to match your setup)

# Directory for storing log files
log_file_dir = "../../Logs"

# Try to execute the following code, and if an exception occurs, handle it in the 'finally' block
try:
    # Initialize an instance of the custom Roboclaw_zwv class with the specified serial port and baud rate
    roboclaw = Roboclaw_zwv(serial_port, baud_rate)

    # Check if the serial port can be opened, and if not, raise an exception
    if not roboclaw.Open():
        raise Exception(f"Unable to open port {serial_port}")

    # Execute a sequence of buffered commands with logging
    roboclaw.execute_buffered_commands_with_logging(address,
                                                    [
                                                        lambda: roboclaw.SpeedDistanceM1(address, 200, 1400, 0),
                                                        lambda: roboclaw.SpeedDistanceM1(address, 100, 50, 0)
                                                    ],
                                                    2, 2)  # Capture metrics before and after executing commands

    # Generate and display graphs from the logged metrics
    roboclaw.graph_metrics(roboclaw.log_file.name)

# Ensure proper cleanup in case of an exception
finally:
    # Check if the serial port is open and close it if necessary
    if roboclaw._port.is_open:
        roboclaw._port.close()
