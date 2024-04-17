#!/usr/bin/env python

# Library adapted from SDL_Pi_INA3221.py Python Driver Code
# SwitchDoc Labs March 4, 2015	 
# V 1.2


#encoding: utf-8
 
import time
import smbus
import paho.mqtt.client as paho
import json
import threading


# constants

#/*=========================================================================
#    I2C ADDRESS/BITS
#    -----------------------------------------------------------------------*/
INA3221_ADDRESS =                         (0x40)    # 1000000 (A0+A1=GND)
INA3221_READ    =                         (0x01)
#/*=========================================================================*/

#/*=========================================================================
#    CONFIG REGISTER (R/W)
#    -----------------------------------------------------------------------*/
INA3221_REG_CONFIG            =          (0x00)
#    /*---------------------------------------------------------------------*/
INA3221_CONFIG_RESET          =          (0x8000)  # Reset Bit

INA3221_CONFIG_ENABLE_CHAN1   =          (0x4000)  # Enable Channel 1
INA3221_CONFIG_ENABLE_CHAN2   =          (0x2000)  # Enable Channel 2
INA3221_CONFIG_ENABLE_CHAN3   =          (0x1000)  # Enable Channel 3

INA3221_CONFIG_AVG2     =                (0x0800)  # AVG Samples Bit 2 - See table 3 spec
INA3221_CONFIG_AVG1     =                (0x0400)  # AVG Samples Bit 1 - See table 3 spec
INA3221_CONFIG_AVG0     =                (0x0200)  # AVG Samples Bit 0 - See table 3 spec

INA3221_CONFIG_VBUS_CT2 =                (0x0100)  # VBUS bit 2 Conversion time - See table 4 spec
INA3221_CONFIG_VBUS_CT1 =                (0x0080)  # VBUS bit 1 Conversion time - See table 4 spec
INA3221_CONFIG_VBUS_CT0 =                (0x0040)  # VBUS bit 0 Conversion time - See table 4 spec

INA3221_CONFIG_VSH_CT2  =                (0x0020)  # Vshunt bit 2 Conversion time - See table 5 spec
INA3221_CONFIG_VSH_CT1  =                (0x0010)  # Vshunt bit 1 Conversion time - See table 5 spec
INA3221_CONFIG_VSH_CT0  =                (0x0008)  # Vshunt bit 0 Conversion time - See table 5 spec

INA3221_CONFIG_MODE_2   =                (0x0004)  # Operating Mode bit 2 - See table 6 spec
INA3221_CONFIG_MODE_1   = 	         (0x0002)  # Operating Mode bit 1 - See table 6 spec
INA3221_CONFIG_MODE_0 	=                (0x0001)  # Operating Mode bit 0 - See table 6 spec

#/*=========================================================================*/

#/*=========================================================================
#    SHUNT VOLTAGE REGISTER (R)
#    -----------------------------------------------------------------------*/
INA3221_REG_SHUNTVOLTAGE_1   =             (0x01)
#/*=========================================================================*/

#/*=========================================================================
#    BUS VOLTAGE REGISTER (R)
#    -----------------------------------------------------------------------*/
INA3221_REG_BUSVOLTAGE_1     =             (0x02)
#/*=========================================================================*/

SHUNT_RESISTOR_VALUE         = (0.1)   # default shunt resistor value of 0.1 Ohm



class INA3221_mqtt():



    ###########################
    # INA3221 Code
    ###########################
    def __init__(self, topic, poll_rate = 1, host = "localhost", port = 1883, twi=1, addr=INA3221_ADDRESS, s1=0.1,s2=0.1,s3=0.1):
        self._bus = smbus.SMBus(twi)
        self._addr = addr
        config = INA3221_CONFIG_ENABLE_CHAN1 |		\
                    INA3221_CONFIG_ENABLE_CHAN2 |	\
                    INA3221_CONFIG_ENABLE_CHAN3 |	\
                    INA3221_CONFIG_AVG1 |		\
                    INA3221_CONFIG_VBUS_CT2 |		\
                    INA3221_CONFIG_VSH_CT2 |		\
                    INA3221_CONFIG_MODE_2 |		\
                    INA3221_CONFIG_MODE_1 |		\
                    INA3221_CONFIG_MODE_0
        self.shunts=[s1,s2,s3]
        self._write_register_little_endian(INA3221_REG_CONFIG, config)
        self.host = host
        self.port = port
        self.client = paho.Client()
        self.client.on_message = self.on_message #setting  on message callback to our own method
        self.connect(topic)
        self.sensorReadings = {}


    def connect(self, topic):
        if self.client.connect(self.host,self.port,60) !=0:
          print("Couldn't connect to the mqtt broker. Publish function returns reading object which can be used instead")
          
        self.client.loop_start()
        subscription_topic = topic + "/read"
        self.client.subscribe(subscription_topic)
        
    
    def on_message(self,client,userdata,msg):
        print(f"{msg.topic}: {msg.payload.decode()}")
        ### TODO : Do some message handling i.e Call a publish if message received 
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
               
    
    def _write(self, register, data):
        #print "addr =0x%x register = 0x%x data = 0x%x " % (self._addr, register, data)
        self._bus.write_byte_data(self._addr, register, data)


    def _read(self, data):

        returndata = self._bus.read_byte_data(self._addr, data)
        #print "addr = 0x%x data = 0x%x %i returndata = 0x%x " % (self._addr, data, data, returndata)
        return returndata


    def _read_register_little_endian(self, register): 
	
        result = self._bus.read_word_data(self._addr,register) & 0xFFFF
        lowbyte = (result & 0xFF00)>>8 
        highbyte = (result & 0x00FF) << 8
        switchresult = lowbyte + highbyte 
        #print "Read 16 bit Word addr =0x%x register = 0x%x switchresult = 0x%x " % (self._addr, register, switchresult)
        return switchresult
   
   
    def _write_register_little_endian(self, register, data): 

        data = data & 0xFFFF
        # reverse configure byte for little endian
        lowbyte = data>>8
        highbyte = (data & 0x00FF)<<8
        switchdata = lowbyte + highbyte
        self._bus.write_word_data(self._addr, register, switchdata)
        #print "Write  16 bit Word addr =0x%x register = 0x%x data = 0x%x " % (self._addr, register, data)
       


    def _getBusVoltage_raw(self, channel):
	#Gets the raw bus voltage (16-bit signed integer, so +-32767)

        value = self._read_register_little_endian(INA3221_REG_BUSVOLTAGE_1+(channel -1) *2) 
        if value > 32767:
            value -= 65536
        return value

    def _getShuntVoltage_raw(self, channel):
	#Gets the raw shunt voltage (16-bit signed integer, so +-32767)
	
        value = self._read_register_little_endian(INA3221_REG_SHUNTVOLTAGE_1+(channel -1) *2)
        if value > 32767:
            value -= 65536
        return value

    # public functions ######################################################################################
    #########################################################################################################

    def getBusVoltage_V(self, channel):
	# Gets the Bus voltage in volts

        value = self._getBusVoltage_raw(channel)
        return value * 0.001


    def getShuntVoltage_mV(self, channel):
	# Gets the shunt voltage in mV (so +-168.3mV)

        value = self._getShuntVoltage_raw(channel)
        return value * 0.005

    def getCurrent_A(self, channel):
    #Gets the current value in mA, taking into account the config settings and current LSB
    	
        valueDec = self.getShuntVoltage_mV(channel)/(1000.0*self.shunts[channel-1])              
        return valueDec

    def getPower_W(self,channel):
    #Calculates the power usage on each channel
    
        current = self.getCurrent_A(channel)
        voltage = self.getBusVoltage_V(channel)
        power = current*voltage
        return power

    def printArbitraryRegister(self,register):
    #Print out whats stored in an user specified register
    
        register_val = self._read_register_little_endian(register)
        return hex(register_val)
        
    def _publishOnce(self,publishingTopic):
    #Publish all sensor readings to an mqtt server with a specified topic
    
        for i in range(1, 4):
          key = f"Ch{i}"  # Construct the key as "Ch_1", "Ch_2", "Ch_3"
          value = [self.getCurrent_A(i), self.getBusVoltage_V(i)]  # Create an array with two elements based on the current index
          self.sensorReadings[key] = value  # Assign the key-value pair to the dictionary
          time.sleep(0.1)
          
        self.client.publish(publishingTopic,json.dumps(self.sensorReadings),0)
        return self.sensorReadings
        
        
    def _publishReadings_periodic(self,publishingTopic,interval):
    #Publish all sensor readings to an mqtt server with a specified topic
        while True:
        
            for i in range(1, 4):
              key = f"Ch{i}"  # Construct the key as "Ch_1", "Ch_2", "Ch_3"
              value = [self.getCurrent_A(i), self.getBusVoltage_V(i)]  # Create an array with two elements based on the current index
              self.sensorReadings[key] = value  # Assign the key-value pair to the dictionary
             # time.sleep(0.1)
              
            self.client.publish(publishingTopic,json.dumps(self.sensorReadings),0)
            time.sleep(interval)
        
    def publish(self,poll_rate,publishingTopic):

        thread = threading.Thread(target=self._publishReadings_periodic, args=(publishingTopic,poll_rate,))
        thread.daemon = True  # Set daemon to True to automatically terminate thread when main program exits
        thread.start()
