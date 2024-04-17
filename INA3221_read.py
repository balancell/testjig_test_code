
import sys
import time
from INA3221_mqtt import *
import json

CONFIG_FILE_PATH : str = "/home/admin/Documents/jig_config.json" #TODO: make this an external argument called when running this script
POLL_RATE = 1	# poll sensor readings once a second



try:
    with open(CONFIG_FILE_PATH, 'r') as file:
        json_data = json.load(file)
except:
    print("Error reading json, check file exists and is formatted correctly")
    json_data = {}


publishingTopic = json_data["Topic"].get("JigName") + "/" + json_data["Topic"].get("data_source_type") + "/" + json_data["Topic"].get("data_source") + "/" + json_data["Topic"].get("message_type")
print(publishingTopic)

Isensor = INA3221_mqtt(publishingTopic)
Isensor.publish(publishingTopic,POLL_RATE)

while True:
    print(readings)
    time.sleep(1)

