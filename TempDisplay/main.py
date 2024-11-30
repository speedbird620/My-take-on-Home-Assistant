import network
import time
import gc
import json
import machine
import config
from machine import UART
from machine import Pin
from umqtt.simple import MQTTClient

uart = UART(1, baudrate=115200, invert=UART.INV_RX, rx=Pin(5), timeout=11000)
#uart = open("test_data.txt")

led = machine.Pin("LED", machine.Pin.OUT)
led.on()

network.hostname('HANmeter')
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PSK)
led.off()

#def sub_cb(topic, msg, retain, dup):
#    print((topic, msg, retain, dup))

def sub_cb(topic, msg):
    #print((topic, msg))
    print(msg.decode("utf-8"))




s_old = ""

waitcount = 0
while wlan.status() != 3:
   waitcount+=1
   time.sleep(0.5)
   led.toggle()
   if waitcount > 120:
      led.off()
      machine.reset()

#led on when connected to wlan
led.on()
print("WIFI CONNECTED")
mqc = MQTTClient("tempdisplay", config.MQTTHost, 1883, config.MQTTUser, config.MQTTPass)

try:
   mqc.connect()
except:
   print("MQTT NO JOY, rebooting")
   time.sleep(2)
   machine.soft_reset()
   
print("MQTT CONNECTED")

mqc.set_callback(sub_cb)
#mqc.subscribe('temp')
mqc.subscribe(config.MQTTTopic)
   
while True:

    mqc.wait_msg()

    

    #time.sleep(0.3)

    gc.collect()
    led.on()

