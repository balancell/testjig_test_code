import can

def read_can0():
    bus = can.interface.Bus(channel='can0', bustype='socketcan')
    
    try:
        while True:
            message = bus.recv()
            
            print(f"ID: {message.arbitration_id} Data: {message.data}")
            
    except KeyboardInterrupt:
        bus.shutdown()
        
        
read_can0()