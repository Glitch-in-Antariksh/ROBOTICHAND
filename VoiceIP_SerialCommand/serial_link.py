
import serial
import time


class SerialLink:

    def __init__(self, port="COM3", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.connection = None

    def connect(self):
        try:
            self.connection = serial.Serial(
                self.port,
                self.baudrate,
                timeout=1,
                write_timeout=1
            )

            # Arduino may reset when the serial port opens
            time.sleep(2)

            print(f"Arduino connected on {self.port}")
            return True

        except serial.SerialException as error:
            print(f"Serial connection failed: {error}")
            return False

    def send_command(self, command_id):
        if self.connection is None or not self.connection.is_open:
            print("Arduino is not connected.")
            return

        if command_id not in (1, 2, 3):
            print(f"Invalid command ID: {command_id}")
            return

        try:
            self.connection.write(str(command_id).encode("utf-8"))
            print(f"Sent command ID: {command_id}")

        except serial.SerialException as error:
            print(f"Serial transmission failed: {error}")

    def close(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Arduino connection closed.")

