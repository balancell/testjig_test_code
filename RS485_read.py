import serial

SERIAL_PORT = '/dev/ttyAMA5'
BAUD_RATE = 115200

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
        
        while True:
            line = ser.read()
            print("Received:", line)
            
    except serial.SerialException as e:
        print("Error:", e)
        
    finally:
        ser.close()
        
if __name__ == "__main__":
    main()
