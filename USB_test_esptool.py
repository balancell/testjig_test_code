import esptool
import serial
import subprocess
import time
import re

class LogMessage:
    def __init__(self, header, timestamp, tag, information):
        self.header = header
        self.timestamp = timestamp
        self.tag = tag
        self.information = information

def strip_extra_colour_characters(text):
    # Regex pattern to match ANSI escape codes for color formatting
    ansi_escape_pattern = r'\033\[[0-9;]*m'
    # Strip ANSI escape codes from the text
    text = re.sub(ansi_escape_pattern, '', text)
    # Remove any leading or trailing whitespace
    text = text.strip()
    return text

def parse_log_line(line):
    pattern = r'^[^\w]*([IED]) \((\d+)\) (\w+): (.+)'
    match = re.match(pattern, line)
    
    
    if match:
        header = match.group(1)
        timestamp = match.group(2)
        tag = match.group(3)
        information = match.group(4)
        return LogMessage(header, timestamp, tag, information)
    else:
        return None


# Serial port of the ESP32 device
esp32_port = '/dev/ttyACM0'  # Replace with the actual serial port of your ESP32 device

# Baud rate for serial communication
baud_rate = 115200  # Replace with the baud rate of your ESP32 device if different, TODO: Add to config file

# Vendor ID (VID) and Product ID (PID) of the USB device - This is the same for all the SCO1 (the ESP screen unit) devices
usb_vid = "303a"
usb_pid = "1001"

# Check for the presence of the USB device on the bus
def check_device_state():
    # Run the lsusb command to list USB devices
    result = subprocess.run(["lsusb"], capture_output=True, text=True)
    lsusb_output = result.stdout

    # Check if the USB device is present on the bus
    if f"{usb_vid}:{usb_pid}" in lsusb_output:
        return "CONNECTED"
    else:
        return "DISCONNECTED"

# Path to the firmware binary file
firmware_path = 'path/to/firmware.bin'  # Placeholder. We will update the firmware with a remote binary

# Flash firmware to ESP32 device
def flash_firmware():
    subprocess.run(['esptool.py', '--port', esp32_port, 'write_flash', '0', firmware_path])

# Reset the ESP32 device
def reset_device():
    subprocess.run(['esptool.py', '--port', esp32_port, 'chip_id'])

LINES_TO_MONITOR = 41 #Monitor 20 lines and exit serial
# Monitor the output of the ESP32 device
def monitor_output(lines_to_read : int = 20):
    #monitor and classify what is on the device e.g. demo image, balancell bdi image, bdi image + internal storage initialized
    lines_read = 0
    prov_state = " "
    state = "CONNECTED"
    with serial.Serial(esp32_port, baud_rate, timeout=1) as ser:
        while lines_read < LINES_TO_MONITOR:
            line = ser.readline().decode('utf-8').strip()
            print(line)
            line = strip_extra_colour_characters(line)
            if line:
                log_message = parse_log_line(line)
                if log_message:
                    print("Header:", log_message.header)
                    print("Timestamp:", log_message.timestamp)
                    print("Tag:", log_message.tag)
                    print("Information:", log_message.information)
                    print()
                else:
                    print("Failed to parse line:", line)
                lines_read += 1
    
    print("Finished monitoring")
    if log_message.tag == 'QMSD':
        state = "FLASHED_WITH_DEMO"
        print(state)
    
    if log_message.tag == 'IPC_MSG' or 'UTILS':
        state = "FLASHED"
        if log_message.information == "LOADING DEVICE KEY FAILED >> PROVISION DEVICE BEFORE USE WITH AWS IOT":
            prov_state = "NOT PROVISIONED"
            print(prov_state)
       # print(state)
    return state


# Main function
def main():
   # while True:
        # Check the state of the ESP32 device
        state = check_device_state()
        print("Device state:", state)

        if state == "DISCONNECTED":
            time.sleep(1)  # Wait for 1 second before checking again
        if state == "CONNECTED":
            # Flash firmware onto the device
            flash_firmware()
            #print(state)
            reset_device()  # Reset the device after flashing
            state = monitor_output(50)  # Monitor the output after resetting
            #print(state)
           # time.sleep(30)
            
  
         
        if state == "FLASHED_WITH_DEMO":
            print(state)
            # Perform actions specific to this state, to move to flashed
            pass
        
        if state == "FLASHED":
            print(state)
            # Perform actions specific to this state, to move to provisioned
#            pass
#           if prov_state == "NOT PROVISIONED":
#                print(prov_state)
#                pass
        elif state == "BDI_PROGRAMMED_AND_PASSED":
            #Close connection and feedback to user that the test is successful with any info they need
            pass


if __name__ == "__main__":
    main()

    
