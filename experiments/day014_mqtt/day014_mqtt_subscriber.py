import json
import paho.mqtt.client as mqtt

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
TOPIC = "digitaltwin/factory/motors/+"


def validate_message(data):
    required = {
        "schema_version",
        "device_id",
        "timestamp",
        "sequence",
        "rpm",
        "temperature",
        "running",
        "fault",
    }

    if not isinstance(data, dict):
        return False, "JSON 根节点必须是 object"

    missing = required - data.keys()
    if missing:
        return False, f"缺少字段：{sorted(missing)}"

    if data["schema_version"] != 1:
        return False, "不支持的数据版本"

    if data["device_id"] not in {"Motor01", "Motor02"}:
        return False, "未知设备 ID"

    for key in ("rpm", "temperature"):
        value = data[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, f"{key} 必须是数值"

    if not isinstance(data["sequence"], int) or isinstance(
        data["sequence"], bool
    ):
        return False, "sequence 必须是整数"

    if not isinstance(data["running"], bool):
        return False, "running 必须是布尔值"

    if not isinstance(data["fault"], bool):
        return False, "fault 必须是布尔值"

    if data["rpm"] < 0:
        return False, "rpm 不能小于 0"

    if not -20 <= data["temperature"] <= 200:
        return False, "temperature 超出允许范围"

    return True, "OK"


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("已连接 Broker，开始订阅：", TOPIC)
        client.subscribe(TOPIC, qos=1)
    else:
        print(f"连接失败：{reason_code}")


def on_message(client, userdata, msg):
    try:
        text = msg.payload.decode("utf-8")
        data = json.loads(text)

        ok, reason = validate_message(data)
        if not ok:
            print(f"[拒绝] topic={msg.topic} 原因={reason}")
            return

        expected_topic = (
            f"digitaltwin/factory/motors/{data['device_id']}"
        )
        if msg.topic != expected_topic:
            print("[拒绝] Topic 与 device_id 不匹配")
            return

        print(
            f"[收到] device={data['device_id']} "
            f"seq={data['sequence']} "
            f"rpm={data['rpm']} "
            f"temp={data['temperature']} "
            f"running={data['running']} "
            f"fault={data['fault']}"
        )

    except UnicodeDecodeError:
        print("[拒绝] 消息不是有效的 UTF-8 文本")
    except json.JSONDecodeError as exc:
        print(f"[拒绝] JSON 解析失败：{exc}")


def main():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="day014-subscriber",
    )
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nSubscriber 已停止")
        client.disconnect()


if __name__ == "__main__":
    main()