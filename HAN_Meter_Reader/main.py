# HAN-port reader for Swedish power meters for Raspberry Pi Pico
# avionics@skyracer.net
#
# 0.1 - First version
# 0.2 - Object oriented the message handling
# 0.3 - Added a physical jumper and enabled internal watchdog

import network
import time
import gc
import json
import machine
import config
from machine import UART, Pin, WDT
from umqtt.simple import MQTTClient

# Starting the UART
uart = UART(1, baudrate=115200, invert=UART.INV_RX, rx=Pin(5), timeout=11000)

# Defining the LED
led = machine.Pin("LED", machine.Pin.OUT)
led.off()

# Defining the pins
pin14 = Pin("GP14", Pin.IN)
pin15 = Pin("GP15", Pin.OUT)

# Set pin 15 to provide the power to the jumper
pin15.on()

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
j = 0
k = 0
last = 0
WatchDogIsAlive = False
MQTTmessageArray = [
                    'date', 
					'a_meter_u',
					'a_meter_i',
					'r_meter_u',
					'r_meter_i',
					'a_effekt_u',
					'a_effekt_u',
					'r_effekt_u',
					'r_effekt_i',
					'a_effekt_l1_u',
					'a_effekt_l2_u',
					'a_effekt_l3_u',
					'a_effekt_l1_i',
					'a_effekt_l2_i',
					'a_effekt_l3_i',
					'r_effekt_l1_u',
					'r_effekt_l2_u',
					'r_effekt_l3_u',
					'r_effekt_l1_i',
					'r_effekt_l2_i',
					'r_effekt_l3_i',
					'r_effekt_l1_u',
					'r_effekt_l2_u',
					'r_effekt_l3_u',
					'volt_l1',
					'volt_l2',
					'volt_l3',
					'amp_l1',
					'amp_l2',
					'amp_l3']
					
identifierArray = 	[
					'0-0:1.0.0',
					'1-0:1.8.0',
					'1-0:2.8.0',
					'1-0:3.8.0',
					'1-0:4.8.0',
					'1-0:1.7.0',
					'1-0:2.7.0',
					'1-0:3.7.0',
					'1-0:4.7.0',
					'1-0:21.7.0',
					'1-0:41.7.0',
					'1-0:61.7.0',
					'1-0:22.7.0',
					'1-0:42.7.0',
					'1-0:62.7.0',
					'1-0:23.7.0',
					'1-0:43.7.0',
					'1-0:63.7.0',
					'1-0:24.7.0',
					'1-0:44.7.0',
					'1-0:64.7.0',
					'1-0:23.7.0',
					'1-0:43.7.0',
					'1-0:63.7.0',
					'1-0:32.7.0',
					'1-0:52.7.0',
					'1-0:72.7.0',
					'1-0:31.7.0',
					'1-0:51.7.0',
					'1-0:71.7.0'
					]

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

# Check if the watchdog shall be enabled:
# Jumper between pin 14 and 15 = enable watchdog (pin 15 is already set high)
# Jumper between pin 14 and GND = disable watchdog
if pin14() and not WatchDogIsAlive:
    # Pin14 is high, the jumper is set and the watchdog shall be enabled
    wdt = WDT(timeout=2000)             # Enabling the built in watchdog
    wdt.feed()                          # Feeding the watchdog
    WatchDogIsAlive = True              # Setting the watchdog flag
    print("The watchdog is alive!")

# The main loop: here we go!
while True:

	# Note: the UART buffert size of the RP2040/RP2350 is only 256 characters. Since
	# the baudrate is so high, the buffert is filled very quickly. In order to mitigate 
	# this shortcoming, the information in the UART is transferred to an array in a 
	# while loop as quickliy as possible. Once all of the information in the buffert 
	# is obatined it can be sorted out later. The interval between the messages from 
	# the HAN-port is sent every 10 seconds, there are plenty of time after the message
	# is placed in the array.

    if WatchDogIsAlive:
        wdt.feed()		    # Feeding the watchdog

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

				# The message is consisting of three parts: identifier, the content and the end
				# Example in this case: '0-0:1.0.0(231117132609W)'
				# Identifier: 	'0-0:1.0.0('
				# Content:		'231117132609'
				# The end: 		'W)'
               
                value = ''
                k = 0							# Reset of array counter
                while k < len(identifierArray) and value == '':
                    # Doing this until we run out of array or a value is found
                    if s[0:len(identifierArray[k])] == identifierArray[k]:
                        # The identifier in the string matches an identifier in the array, we found the message
                        message = MQTTmessageArray[k]		# Saving the message string to send it later
                        if s.find('*') > 0:
                            # Messages with '*' is measurements. Cropping away the identifier and the end 
                            value = s[(len(identifierArray[k]) + 1):(s.find('*'))]
                        elif s.find('W') > 0:
                            # Messages with 'W' is the date stamp. Cropping away the identifier and the end
                            value = s[(len(identifierArray[k]) + 1):(s.find('W'))]
                            date = s[10:16]                 # Saving the date for a later time
                            tajm = s[16:22]                 # Saving the time for a later date
                    k = k + 1								# Notching up the array counter

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


    

