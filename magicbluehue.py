from classes.qhue import Bridge
from classes.rgb_cie import Converter
import time
from subprocess import PIPE, Popen, call, STDOUT
import logging

## Follow HUE color if true, or just follow lamp state if failse
follow_color=True

## Your HUE Bridge details
## Find these in the HUE app
## Create a new API key by following the instructions at:
## http://www.developers.meethue.com/documentation/getting-started
hue_bridge_ip="192.168.51.72"
hue_bridge_apikey='yourpw'

## The lamp number of the lamp we are going to follow. You can find these
## numbers in the HUE app in front of the light names.
hue_lamp_number=2

## The BLUETOOTH addresses of your magicblue bulbs. Add more by seperating with a comma
## For eample, ["FB:6F:13:A3:C1:98", "12:34:56:78:C1:98"]
bm_addresses = ["FB:6F:13:A3:C1:98"]

## Some magic numbers
bm_handle = "0x000c"
bm_on_command = "cc2333"
bm_color_prefix = "56"
bm_color_suffix = "00f0aa3b070001"
bm_off_command = "cc2433"

gatttool_location="/usr/bin/gatttool"

## Sleep time between bluetooth commands in seconds. 
## Increase if you get weird errors
sleep_time=0.4

## Poll time in seconds
## Decrease if you want more accurate response times in the bulb following
## your HUE changes
## If you get "connect error: Function not implemented (38)" errors, your poll time is too high
poll_time=2

## Logging default level. Set to logging.INFO for more detailed info
logging.basicConfig(level=logging.ERROR)

logger = logging.getLogger("magicbluehue")

def gatttool_call(value):
    for bm in bm_addresses:
        ## Logger abuse!! If we are at a higher error level then just ERROR, use Popen instead of call().
        ## This will lag the updates, but will actually display errors
        if(logger.level < logging.ERROR):
            p = Popen([gatttool_location, "-t", "random", "-b", bm, "--char-write", "--handle="+bm_handle, "--value="+value], stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            ## The actual error when not finding the BT addres is "connect error: Transport endpoint is not connected (107)"
            if(stderr.find("107") > -1):
                logger.error("Could not connect to Magicblue lamp " + bm + ". Is the power on?")
        else:
            call([gatttool_location, "-t", "random", "-b", bm, "--char-write", "--handle="+bm_handle, "--value="+value], stderr=STDOUT)
        time.sleep(0.4)

def set_color(hexcolor):
    colorstring = bm_color_prefix + hexcolor + bm_color_suffix
    gatttool_call(colorstring)

b = Bridge(hue_bridge_ip, hue_bridge_apikey)
converter = Converter()
laststate = "1"
lastcolor = 0

print("Now following HUE lamp " + str(hue_lamp_number) + " with our " + str(len(bm_addresses)) + " Magicblue lamps")
while True:
    try:
        state = b.lights[hue_lamp_number]()
        currstate = (state['state']['on'])
        if currstate != laststate:
            laststate = currstate
            if currstate:
                logger.info("HUE switched on, following..")
                gatttool_call(bm_on_command)
            else:
                logger.info("HUE switched off, following..")
                gatttool_call(bm_off_command)

        if currstate and follow_color:
            color = converter.CIE1931ToHex(state['state']['xy'][0], state['state']['xy'][1], bri=state['state']['bri'])
            if color != lastcolor:
                logger.info("HUE changed color, following..")
                set_color(color)
                lastcolor = color
    except Exception as e:
        print(e.message)
    logger.debug("..poller ping!")
    time.sleep(poll_time)

