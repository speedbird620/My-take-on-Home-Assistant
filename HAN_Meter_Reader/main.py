import network
import time
import gc
import json
import machine
import config
from machine import UART, Pin
from umqtt.simple import MQTTClient

# Starting the UART
uart = UART(1, baudrate=115200, invert=UART.INV_RX, rx=Pin(5), timeout=11000)

# Defining the LED
led = machine.Pin("LED", machine.Pin.OUT)
led.off()

# Defining the network
network.hostname(config.MyHostName)
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config.SSID, config.PSK)
led.off()

# Defining the variables
StringArray = [''] * 50
fail_decode = True
s = ""
tajm = ""
date = ""
date_old = ""
i = 0
last = 0

# Connect to the network
waitcount = 0
while wlan.status() != 3:
   waitcount+=1
   time.sleep(0.5)
   led.toggle()
   if waitcount > 120:
      led.off()
      machine.reset()

# Yay! Led on when connected to wlan
led.on()
print("WIFI CONNECTED")

# Defining the MQTT
mqc = MQTTClient(config.MQTTTopic, config.MQTTHost, 1883, config.MQTTUser, config.MQTTPass)

# Connect to MQTT
try:
    mqc.connect()
except:
    print("MQTT NO JOY, rebooting")
    time.sleep(2)
    machine.soft_reset()
    print("MQTT CONNECTED")

# The main loop: here we go!
while True:

	# Note: the UART buffert size of the RP2040/RP2350 is only 256 characters. Since
	# the baudrate is so high, the buffert is filled very quickly. In order to mitigate 
	# this shortcoming, the information in the UART is transferred to an array in a 
	# while loop as quickliy as possible. Once all of the information in the buffert 
	# is obatined it can be sorted out later. The interval between the messages from 
	# the HAN-port is sent every 10 seconds, there are plenty of time after the message
	# is placed in the array.

	# Reading UART
    while uart.any() > 2:
		# Knock knock ... there is something in the UART buffer
        StringArray[i] = uart.readline()	# Transfer a line to the array
        i = i + 1							# Tick up the array counter
        last = time.ticks_ms()				# Saving the latest time stamp

	# Getting the 
    now = time.ticks_ms()

    # Checking how much time has passed since the last time the UART was read
    if i > 0 and (now > (last + 500)) :
    # I has passed more than 500 ms since the latest line in the UART was read. 
        # Therefore, it can be presumed that the message from the HAN-port is complete.
    
        j = 0   							# Resetting the read out array counter

        # Reading thorugh the array
        while not j > i:
            # We have not yet got to the end of the array

            #print(StringArray[j])
            #print('i: ' + str(i) + ' , j: ' + str(j))

            fail_decode = True				# Resetting the fail flag

            # Decoding UART string from bytes to something readable
            try:
                # Sometimes this will fail (pls dont ask me why), hence the safeguarding with a try
                s = StringArray[j].decode("utf-8")
                # Sucess, reseting the fail detection 
                fail_decode = False

            except:
                # You see, thank goodness I was using a try
                print(tajm + ': Except was done when decoding!')

            # If the decoding was successful, lets disect the string (the fun part)
            if not fail_decode:

                # Setting up the basics in order to complie and send the MQTT-message later
                prefix = """{"hanport_a": {"""
                suffix = "}}"
                message = ""
                value = ""

				# I have to admit that the decoding below is rudimentally done. It can be done 
				# in much fancier ways, but since this is open source code noobs like me will 
				# have a hard time to digest and understand what is done in the code. Therefore
				# I want to keep it stupidly simple by avoiding object orientation. 

				# There are many different types of messages that is decoded in the same manner.
				# I will decsribe one of them in detail. 

				# The message is consisting of three parts: identifier, the content and the end
				# Example in this case: '0-0:1.0.0(231117132609W)'
				# Identifier: 	'0-0:1.0.0('
				# Content:		'231117132609'
				# The end: 		'W)'
				
				# Checking the identifier of the message
                if (s[:9]) == "0-0:1.0.0":
					# Bingo, it is the date/time message according to the manual: 'Dagens Datum/ Tid (normaltid)'
                    # Example '0-0:1.0.0(231117132609W)'
                    message = "date"				# This will later be included in the MQTT-message. Note: this string needs to correspond to the Home Assistant configuration
                    value = s[10:22]				# Extracting the content which will later be included in the MQTT-message
                    date = s[10:16]					# Saving the date for a later time
                    tajm = s[16:22]					# Saving the time for a later date

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

                # In case the string contains a decimal point (.), make it a float
                # and then back to a string to get the format corrected. Otherwise
                # HomeAssistant will fail. Probably there is a better way to do it,
				# but I havent found it yet. Pls let me know.
                if value.find(".") > 0:
					# A decimal point is found, lets make it a float
                    f = float(value)			# Make the string a float
                    value = str(f)				# Make the string great again! God bless America!
                    
                # Ok, time to compile the message
                payload = prefix + '"' + message + '"' + ': ' + value + suffix
                
                # Seding the message
                try:
                    # Using try in case the broker is broken
                    mqc.publish(config.MQTTTopic,payload)
                    
                except:
                    print(tajm + ': Except done when publish!')
                
            # Rebooting at midnight, just for good measure. One never knows ...
            if (date != date_old) and (date_old != ""):
                # A new date is detected
                print(tajm + ": Finnaly, a new day. Lets reboot before we screw things up!")
                machine.soft_reset()

            # Setting variables in order to detect flank
            date_old = date

            # Going out with the garbage
            gc.collect()
            
            # Flipping the LED, just for fun
            led.toggle()

            j = j + 1               		# Notching up the read out array counter
            
        i = 0   							# Resetting the read in array counter


    

