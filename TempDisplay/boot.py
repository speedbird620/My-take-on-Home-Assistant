import network
import webrepl
import time
import gc
import machine
import config
from machine import UART
from machine import Pin
from umqtt.simple import MQTTClient


led = machine.Pin("LED", machine.Pin.OUT)
led.on()

highPin = Pin(4, machine.Pin.OUT)
highPin.on()

network.hostname(config.MyHostName)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PSK)
#wlan.ifconfig(('192.168.2.2', '255.255.255.0', '192.168.2.1', '8.8.8.8')) # Static IP
led.off()

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
print("IP: ", wlan.ifconfig()[0])
webrepl.start()
