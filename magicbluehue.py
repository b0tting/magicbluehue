from classes.qhue import Bridge
from classes.rgb_cie import Converter
import time
import json
import os
from subprocess import call

hue_bridge_ip="192.168.51.72"
hue_bridge_apikey='bacchusbacchus'
hue_lamp_number=2

bm_address = "FB:6F:13:A3:C1:98"
bm_handle = "0x000c"
bm_on_command = "cc2333"
bm_color_prefix = "56"
bm_color_suffix = "00f0aa3b070001"
bm_off_command = "cc2433"

## Sleep time between bluetooth commands in seconds. 
## Increase if you get weird errors
sleep_time=0.4

## Poll time in seconds
## Decrease if you want more accurate response times in the bulb following
## your HUE changes
poll_time=2

def gatttool_call(value):
        call(["gatttool", "-t", "random", "-b", bm_address, "--char-write", "--handle="+bm_handle, "--value="+value])
        time.sleep(0.4)

def set_color(hexcolor):
	colorstring = bm_color_prefix + hexcolor + bm_color_suffix
	gatttool_call(colorstring)

b = Bridge(hue_bridge_ip, hue_bridge_apikey)
converter = Converter()
laststate = "1"
lastcolor = 0
while True:
	state = b.lights[hue_lamp_number]()
	currstate = (state['state']['on'])
	if (currstate != laststate):
		laststate = currstate
		if(currstate):
			gatttool_call(bm_on_command)
		else:
			gatttool_call(bm_off_command)
				
	if (currstate):
		color = converter.CIE1931ToHex(state['state']['xy'][0], state['state']['xy'][1], bri=state['state']['bri'])
		if color != lastcolor:
			set_color(color)
			lastcolor = color
	time.sleep(poll_time)

