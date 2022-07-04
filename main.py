import machine
import dht
import time
import ssd1306
from umqttsimple import MQTTClient
import network
import ubinascii
import bmp280

"""
Battery related
"""
# EXPERIMENTAL:
# Set to True when running on battery power
# Set to False for when plugged in or when debugging on battery
battery = False

"""
Internet and connectivity
"""
# WIFI
ssid = "<ssid>"
password = "<password>"


def conn_wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    sta.connect(ssid, password)

    while sta.isconnected() == False:
        pass


# MQTT
mqtt_server = "<ip>"
client_id = ubinascii.hexlify(machine.unique_id())
mqtt_user = "<username>"
mqtt_pwd = "<password>"

# MQTT topics
topic_pub_temp = b'esp/dht22/temp'
topic_pub_hum = b'esp/dht22/hum'
topic_pub_press = b'esp/bmp280/press'

def conn_mqtt():
    """ Connect to selected MQTT broker """
    global client_id, mqtt_server, mqtt_user, mqtt_pwd
    client = MQTTClient(client_id,
                        mqtt_server,
                        user=mqtt_user,
                        password=mqtt_pwd)
    client.connect()
    print("Connected to %s MQTT broker' % (mqtt_server)")
    return client


""" Declare I2C pins """
# I2C
i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21))

"""
Sensors, LEDs and devices
"""
# DHT22
dh = dht.DHT22(machine.Pin(4))

# BMP280 for air pressure
bmp = bmp280.BMP280(i2c)

# SSD1306 OLED
oled_width = 128
oled_height = 32
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# LEDs
led_red = machine.Pin(16, machine.Pin.OUT)
led_yellow = machine.Pin(17, machine.Pin.OUT)
led_green = machine.Pin(18, machine.Pin.OUT)

# LED colors
red = [1, 0, 0]
green = [0, 1, 0]
yellow = [0, 0, 1]


def led_color(color):
    led_red(color[0])
    led_green.value(color[1])
    led_yellow(color[2])


"""
Reset function
"""
def reboot():
    """ Reboot device """
    time.sleep(5)
    machine.reset()

"""
Connect to WIFI and MQTT broker
"""
# WIFI
try:
    conn_wifi()
    print("Connection successful")
    time.sleep(5)

    if battery == False:
        led_color(green)
        oled.text("WiFi", 10, 5)
        oled.text("successful!", 10, 20)
        oled.show()
        oled.fill(0)
        time.sleep(2)

except OSError as e:
    if battery == False:
        led_color(red)
        oled.text(str("Wifi error!"), 10, 5)
        oled.text("Resetting..", 10, 20)
        oled.show()
        time.sleep(2)

    reboot()

# MQTT
try:
    client = conn_mqtt()
    if battery == 0:
        oled.text("Broker", 10, 5)
        oled.text("successful!", 10, 20)
        oled.show()
        oled.fill(0)

    time.sleep(2)

except OSError as e:
    if battery == False:
        print("Failed to connect to MQTT Broker. Reconnecting..")
        led_color(red)
        oled.text("MQTT failed", 10, 5)
        oled.text("Reconnecting..", 10, 20)
        oled.show()
        oled.fill(0)

    reboot()

while True:
    dh.measure()
    tem = round(dh.temperature(), 2)
    hum = round(dh.humidity(), 2)
    press = bmp.getPress()
    time.sleep(2)

    if (battery == False):
        print("Humidity: " + str(hum) + "%")
        print("Temperature: " + str(tem) + "°C")
        print("Pressure: " + str(press) + " Pa")

        if tem < 25 and tem > 15:
            led_color(green)
        elif tem > 25 and tem < 30:
            led_color(yellow)
        elif tem > 30:
            led_color(red)

        oled.text("Temp: " + str(tem) + "C", 10, 5)
        oled.text("Humi: " + str(hum) + "%", 10, 20)
        oled.show()
        oled.fill(0)

    try:
        client.publish(topic_pub_temp, str(tem))
        client.publish(topic_pub_hum, str(hum))
        client.publish(topic_pub_press, str(press))
        time.sleep(2)

    except OSError as e:
        if battery == False:
            led_color(red)
            print("Couldn't publish to MQTT broker!")
            oled.text("Could not pub", 10, 5)
            oled.text("MQTT to broker", 10, 20)
            oled.show()
            oled.fill(0)
        reboot()

    if (battery == True):
        machine.deepsleep(600000)  # 10 minutes deep sleep
    else:
        time.sleep(300)
