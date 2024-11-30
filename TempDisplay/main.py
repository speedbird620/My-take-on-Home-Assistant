import network
import time
import gc
import json
import machine
import config
from machine import UART
from machine import Pin
from umqtt.simple import MQTTClient
import time
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_RGB565

uart = UART(1, baudrate=115200, invert=UART.INV_RX, rx=Pin(5), timeout=11000)
#uart = open("test_data.txt")

display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_RGB565, rotate=0)
display.set_backlight(0.5)

# set up constants for drawing
WIDTH, HEIGHT = display.get_bounds()
BLACK = display.create_pen(0, 0, 0)
RED = display.create_pen(255, 0, 0)
GREEN = display.create_pen(0, 255, 0)
BLUE = display.create_pen(0, 0, 255)
WHITE = display.create_pen(255, 255, 255)
PURPLE = display.create_pen(255, 0, 255)

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
    #print((topic, value))
    print(msg.decode("utf-8"))
    txt = msg.decode("utf-8")   # ('6.4', '10:55')
    #txt = "('6.4', '10:55')"
    
    pos1 = txt.find("'")        # 1
    txt2 = txt[pos1+1:]         # 6.4', '10:55')
    pos2 = txt2.find("'")       # 3
    temp = (txt2[:pos2])        # 6.4
    txt3 = (txt2[pos2+4:])      # 10:55')
    pos3 = txt3.find("'")       # 5
    tajm = (txt3[:pos3])
    print("Tajm: " + tajm + " , temp: " + temp)

    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)
    #display.text(msg.decode("utf-8") + "°C",30,70,8,10)
    
    display.text(tajm,30,10,8,5)
    display.text(temp + "°C",30,70,8,10)
    display.update()


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

