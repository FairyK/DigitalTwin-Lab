import json
import time
from datetime import datetime, timezone, timedelta

import paho.mqtt.client as mqtt

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
BEIJING_TZ = timezone(timedelta(hours=8))

motors = {
    "Motor01": {
        "rpm": 1200,
        "temperature": 42.0,
        "running": True,
        "fault": False,
        "sequence": 0,
    },
    "Motor02": {
        "rpm": 0,
        "temperature": 28.0,
        "running": False,
        "fault": False,
        "sequence": 0,
    },
}


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("已连接 MQTT Broker")
    else:
        print(f"连接失败：{reason_code}")


def make_message(device_id, state):
    state["sequence"] += 1

    return {
        "schema_version": 1,
        "device_id": device_id,
        "timestamp": datetime.now(BEIJING_TZ).isoformat(
            timespec="seconds"
        ),
        "sequence": state["sequence"],
        "rpm": state["rpm"],
        "temperature": round(state["temperature"], 1),
        "running": state["running"],
        "fault": state["fault"],
    }


def main():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="day014-publisher",
    )
    client.on_connect = on_connect

    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_start()

        while True:
            for device_id, state in motors.items():
                if state["running"] and not state["fault"]:
                    state["temperature"] = min(
                        state["temperature"] + 0.3, 95.0
                    )
                elif not state["running"]:
                    state["temperature"] = max(
                        state["temperature"] - 0.2, 20.0
                    )

                message = make_message(device_id, state)
                topic = f"digitaltwin/factory/motors/{device_id}"
                payload = json.dumps(
                    message,
                    ensure_ascii=False,
                )

                info = client.publish(
                    topic,
                    payload,
                    qos=1,
                    retain=False,
                )
                info.wait_for_publish()

                print(f"已发布：{topic} | {payload}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nPublisher 正在退出")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()