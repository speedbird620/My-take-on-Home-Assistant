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

network.hostname(config.MyHostName)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PSK)
led.off()

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
mqc = MQTTClient(config.MQTTTopic, config.MQTTHost, 1883, config.MQTTUser, config.MQTTPass)

try:
   mqc.connect()
except:
   print("MQTT NO JOY, rebooting")
   time.sleep(2)
   machine.soft_reset()
   
print("MQTT CONNECTED")

while True:
    mvpos = 0
    t = uart.readline()
    #s = uart.readline()
    #s = "aaa"
    #print('t: ' + str(t))
    #s = ""

    try:
         s = t.decode("utf-8")
    except:        
         s = ""
         print('Except done when decoding!')

    if len(s) > 3 and s != s_old:
        #print('A')
        #print('s: ' + s)

        #a = 9
        #config_payload = """{"hanport_a": {"power":""" + str(a) + "}}"
        #mqc.publish(config.MQTTTopic,config_payload)

        prefix = """{"hanport_a": {"""
        suffix = "}}"
        message = ""
        value = ""

        if (s[:9]) == "0-0:1.0.0":
            # Dagens Datum/ Tid (normaltid)
            # 0-0:1.0.0(231117132609W)
            message = "date"
            value = s[10:22]

        elif (s[:9]) == "1-0:1.8.0":
            # Mätarställning Aktiv Energi Uttag, kWh
            # 1-0:1.8.0(00010293.840*kWh)
            message = "a_meter_u"
            value = s[10:22]

        elif (s[:9]) == "1-0:2.8.0":
            # Mätarställning Aktiv Energi Inmatning, kWh
            # 1-0:2.8.0(00000000.000*kWh)
            message = "a_meter_i"
            value = s[10:22]

        elif (s[:9]) == "1-0:3.8.0":
            # Mätarställning Reaktiv Energi Uttag, kVArh
            # 1-0:3.8.0(00000957.525*kVArh)
            message = "r_meter_u"
            value = s[10:22]

        elif (s[:9]) == "1-0:4.8.0":
            # Mätarställning Rektiv Energi Inmatning , kVArh
            # 1-0:4.8.0(00001483.853*kVArh)
            message = "r_meter_i"
            value = s[10:22]

        elif (s[:9]) == "1-0:1.7.0":
            # Aktiv effekt uttag, kW
            # 1-0:1.7.0(0000.345*kW)
            message = "a_effekt_u"
            value = s[10:18]

        elif (s[:9]) == "1-0:2.7.0":
            # Aktiv effekt inmatning, kW
            # 1-0:2.7.0(0000.000*kW)
            message = "a_effekt_u"
            value = s[10:18]

        elif (s[:9]) == "1-0:3.7.0":
            # Reaktiv effekt uttag, kWAr
            # 1-0:3.7.0(0000.252*kVAr)
            message = "r_effekt_u"
            value = s[10:18]

        elif (s[:9]) == "1-0:4.7.0":
            # Reaktiv effekt inmatning, kVAr
            # 1-0:4.7.0(0000.252*kVAr)
            message = "r_effekt_i"
            value = s[10:18]

        elif (s[:10]) == "1-0:21.7.0":
            # Aktiv effekt uttag L1, kW
            # 1-0:21.7.0(0000.205*kW)
            message = "a_effekt_l1_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:41.7.0":
            # Aktiv effekt uttag L2, kW
            # 1-0:41.7.0(0000.288*kW)
            message = "a_effekt_l2_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:61.7.0":
            # Aktiv effekt uttag L3, kW
            # 1-0:61.7.0(0000.006*kW)
            message = "a_effekt_l3_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:22.7.0":
            # Aktiv effekt inmatning L1, kW
            # 1-0:22.7.0(0000.000*kW)
            message = "a_effekt_l1_i"
            value = s[11:18]

        elif (s[:10]) == "1-0:42.7.0":
            # Aktiv effekt L2 inmatning, kW
            # 1-0:42.7.0(0000.000*kW)
            message = "a_effekt_l2_i"
            value = s[11:18]

        elif (s[:10]) == "1-0:62.7.0":
            # Aktiv effekt L3 inmatning, kW
            # 1-0:62.7.0(0000.000*kW)
            message = "a_effekt_l3_i"
            value = s[11:18]

        elif (s[:10]) == "1-0:23.7.0":
            # Reaktiv effekt uttag L1, kW
            # 1-0:23.7.0(0000.000*kVAr)
            message = "r_effekt_l1_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:43.7.0":
            # Reaktiv effekt L2 uttag, kW
            # 1-0:23.7.0(0000.000*kVAr)
            message = "r_effekt_l2_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:63.7.0":
            # Reaktiv effekt L3 uttag, kW
            # 1-0:23.7.0(0000.000*kVAr)
            message = "r_effekt_l3_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:24.7.0":
            # Reaktiv effekt inmatning L1, kW
            # 1-0:24.7.0(0000.102*kVAr)
            message = "r_effekt_l1_i"
            value = s[11:18]

        elif (s[:10]) == "1-0:44.7.0":
            # Reaktiv effekt inmatning L2, kW
            # 1-0:24.7.0(0000.102*kVAr)
            message = "r_effekt_l2_i"
            value = s[11:18]

        elif (s[:10]) == "1-0:64.7.0":
            # Reaktiv effekt inmatning L3, kW
            # 1-0:24.7.0(0000.102*kVAr)
            message = "r_effekt_l3_i"
            value = s[11:18]

        elif (s[:10]) == "1-0:23.7.0":
            # Reaktiv effekt uttag L1, kW
            # 1-0:23.7.0(0000.000*kVAr)
            message = "r_effekt_l1_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:43.7.0":
            # Reaktiv effekt L2 uttag, kW
            # 1-0:43.7.0(0000.000*kVAr)
            message = "r_effekt_l2_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:63.7.0":
            # Reaktiv effekt L3 uttag, kW
            # 1-0:23.7.0(0000.000*kVAr)
            message = "r_effekt_l3_u"
            value = s[11:18]

        elif (s[:10]) == "1-0:32.7.0":
            # Fasspänning L1, v
            # 1-0:32.7.0(229.4*V)
            message = "volt_l1"
            value = s[11:16]

        elif (s[:10]) == "1-0:52.7.0":
            # Fasspänning L2, v
            # 1-0:52.7.0(228.6*V)
            message = "volt_l2"
            value = s[11:16]

        elif (s[:10]) == "1-0:72.7.0":
            # Fasspänning L3, v
            # 1-0:72.7.0(230.0*V)
            message = "volt_l3"
            value = s[11:16]

        elif (s[:10]) == "1-0:31.7.0":
            # Fasström L1, v
            # 1-0:31.7.0(000.1*A)
            message = "amp_l1"
            value = s[11:16]

        elif (s[:10]) == "1-0:51.7.0":
            # Fasström L1, A
            # 1-0:51.7.0(000.7*A)
            message = "amp_l2"
            value = s[11:16]

        elif (s[:10]) == "1-0:71.7.0":
            # Fasström L3, v
            # 1-0:71.7.0(001.1*A)
            message = "amp_l3"
            value = s[11:16]

        else:
            print('Else: ' + s)

        #print("A: " + value)
        #print("C: " + str(value.find(".")))
        
        if value.find(".") > 0:
            f = float(value)
            value = str(f)
            #print("B: " + value)
            
        
        if len(value) > 0:
            #payload = prefix + '"' + message + '"' + ': ' + '1.32' + suffix
            payload = prefix + '"' + message + '"' + ': ' + value + suffix
            #print('p: ' + payload)
            
            try:
                mqc.publish(config.MQTTTopic,payload)
                #print('Payload: ' + payload)
            except:
                #machine.soft_reset()
                print('Except done when publish!')

        if (date[:6] != date_old) and (date != ""):
            print("A new date, lets reboot!")
            machine.soft_reset()

    s_old = s
    date_old = date[:6]


    #time.sleep(0.3)

    gc.collect()
    led.on()



