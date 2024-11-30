import network
import webrepl
import time
import gc
import machine
import config
from machine import UART
from machine import Pin
from umqtt.simple import MQTTClient


uart = UART(1, baudrate=115200, invert=UART.INV_RX, rx=Pin(5), timeout=11000)
s = "text"
counter = 0


#mqc = MQTTClient("HANMeter", config.MQTTHost, 1883, "muser", "Password12+")
mqc = MQTTClient(config.MyHostName, config.MQTTHost, 1883)
try:
   mqc.connect()
except:
   machine.soft_reset()
print("MQTT CONNECTED")
workbuffert = bytearray(1024)
mv = memoryview(workbuffert)

while True:
   mvpos=0
   s = uart.readline()
   print("s = " + str(s))
   s_uart = str(s)
   
   #while s[0] != ord('/'):
   while s_uart[0] != '/':
      s = uart.readline()
      print("s = " + str(s))
      s_uart = str(s)
      #print("NEW HAN PACKAGE")

   mv[mvpos : mvpos+len(s)] = s
   mvpos += len(s)
   led.off()

   #while s[0]!= ord('!'):
   while s_uart[0]!= ord('!'):
      s = uart.readline()
      print("s = " + str(s))
      s_uart = str(s)
      mv[mvpos : mvpos+len(s)] = s
      mvpos += len(s)
   try:
      mqc.publish(config.MQTTTopic,workbuffert[0:mvpos])
   except:
      machine.soft_reset()

   gc.collect()
   led.on()