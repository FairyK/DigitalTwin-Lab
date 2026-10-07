import json
import random

motors = [
    "Motor01",
    "Motor02",
    "Motor03"
]

for motor_id in motors:

    data = {
        "device_id": motor_id,
        "rpm": random.randint(1000, 1800),
        "temperature": round(random.uniform(30, 70), 2),
        "running": True,
        "fault": False
    }

    print(json.dumps(data))