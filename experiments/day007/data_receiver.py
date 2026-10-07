import json

message = '{"device_id": "Motor01", "rpm": 1500, "temperature": 63.5, "running": true}'

data = json.loads(message)

print("设备ID：", data["device_id"])
print("转速：", data["rpm"])
print("温度：", data["temperature"])
print("运行状态：", data["running"])