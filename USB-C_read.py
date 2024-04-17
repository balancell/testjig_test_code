import serial
import esptool
import time

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200
DSRDTR = 'TRUE'
RTSCTS = 'TRUE'


def main():
    try:
        print(f"Attempting to open {SERIAL_PORT} on with {BAUD_RATE}\n")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)

        time.sleep(0.5)
        ser.rtscts=False
        ser.dsrdtr=False
        time.sleep(0.1)
        ser.rtscts=False
        ser.dsrdtr=True
        time.sleep(0.1)
        ser.dsrdtr=False
        ser.rtscts=True
        time.sleep(0.1)
        ser.rtscts=False
        ser.dsrdtr=False
        
        #print("Serial port opened Success")
        #ser.sleep(0.3)
        #print(ser.write_timeout())
        #ser.write(b'reset\n')
        print("after serial print")
        while True:
            print("within while loop")
            line = ser.readline().decode().strip()
            print(line)
            
    except serial.SerialException as e:
        print("Error:", e)
        
    finally:
        ser.close()
        
if __name__ == "__main__":
    main()
