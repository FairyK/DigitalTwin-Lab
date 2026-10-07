import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, rc):

    print("MQTT连接成功")

    client.subscribe(
        "factory/motor/Motor01/state"
    )


def on_message(client, userdata, msg):

    print("收到消息：")
    print(msg.topic)
    print(msg.payload.decode())


client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.loop_forever()