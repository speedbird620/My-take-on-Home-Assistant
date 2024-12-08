import network
import time
import gc
import json
import machine
import config
import array
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

tajm = ""
i_tajm = -999
temp = ""
f_temp = -999.9
tajm_old = ""
temp_old = ""
temp_1hago = ""
tempmax = ""
tempmin = ""
f_tempmax = -999
f_tempmin = 999
lasttime = 9999999999
temparray = array.array('f', (0 for _ in range(60))) 

i = 0
while i < 59:
    i = i + 1
    temparray[i] = -999.9
    #print(str(i))


def sub_cb(topic, msg):
    global tajm
    global temp
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
    #print("Tajm: " + tajm + " , temp: " + temp)
    

def disp_updt(tid, temperatur, temperatur_1h, temperatur_max, temperatur_min):
    """
    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)
    #display.text(msg.decode("utf-8") + "°C",30,70,8,10)
    
    display.text(tid,30,10,8,5)
    display.text(temperatur + "°C",30,70,8,10)
    display.update()
    """
    
    display.set_pen(WHITE)
    display.clear()
    display.set_pen(BLACK)
    display.text(tid,30,10,8,5)
    display.text(temperatur,30,70,8,10)
    display.text("1h:",30,140,8,5)
    display.text(temperatur_1h,140,140,8,5)
    display.text("max:",30,170,8,5)
    display.text(temperatur_max,140,170,8,5)
    display.text("min:",30,200,8,5)
    display.text(temperatur_min,140,200,8,5)
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

    #mqc.wait_msg()
    try:
        mqc.check_msg()
    except:    
        time.sleep(1)

    #lasttime = time.time()

    if time.time() > (lasttime + 300):
        print("No update for " + str(time.time() - lasttime) + " s. Rebooting.")
        machine.reset()
    
    
    if (tajm[0:2] != tajm_old[0:2]) and (tajm[0:2] == "10") :		# A new day
        tempmax = temp
        tempmin = temp
    
    if temp != "":
        #print(temp)
        f_temp = float(temp)
        #print(f_temp)
        #try:
        if (f_temp > f_tempmax):
            f_tempmax = f_temp
        #except:
        #    whatever = True
        #    print("A")
            
        #try:
        if f_temp < f_tempmin:
            f_tempmin = f_temp
        #except:
        #    whatever = True
        #    print("B")


    if (tajm != tajm_old):		# A new minute
        f_temp = -999.9
        i_tajm = -999

        try:		# Is it an integer?
            i_tajm = int(tajm[3:5])
        except:
            whatever = True

        try:		# Is it a float?
            f_temp = float(tajm[3:5])
        except:
            whatever = True

        if f_temp > -999 and i_tajm > -999:		# Yes is was integer and float
            if temparray[i_tajm] > -999:
                #print("C: " + temp_1hago + " arr:" + str(temparray[i_tajm]) + " i: " + str(i_tajm))
                temp_1hago = str(temparray[i_tajm])
                #print("D: " + temp_1hago)
            else:
                #print("A: " + temp_1hago)
                temp_1hago = "" 
            temparray[i_tajm] = f_temp
        
        
    if (tajm != tajm_old) or (temp != temp_old):
        lasttime = time.time()
        #print("B: " + temp_1hago)
        disp_updt(tajm, temp, temp_1hago, str(f_tempmax), str(f_tempmin))

    tajm_old = tajm
    temp_old = temp

    gc.collect()
    led.on()
    time.sleep(1)


