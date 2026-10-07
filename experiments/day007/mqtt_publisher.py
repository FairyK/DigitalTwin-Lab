import json
import random
import time

import paho.mqtt.client as mqtt


client = mqtt.Client()

client.connect("localhost", 1883, 60)

while True:

    data = {
        "device_id": "Motor01",
        "rpm": random.randint(1000, 1800),
        "temperature": round(random.uniform(30, 70), 2),
        "running": True,
        "fault": False
    }

    message = json.dumps(data)

    client.publish(
        "factory/motor/Motor01/state",
        message
    )

    print("发送：", message)

    time.sleep(1)