# Display Pi Pico internal temperature on OLED module
# uses modified "big font" OLED library
# initially based on github.com/nickpmulder/ssd1306big
# 29-Nov-2022 J.Beale

import ssd1306big
import time
from random import randint
from machine import ADC

Tsense = ADC(4) # RP2040 internal temperature sensor

def getTemp():  # read internal temp in degrees C    
    reading = Tsense.read_u16() * (3.3 / 65535)
    degC = 27 - (reading - 0.706)/0.001721
    return degC

write = ssd1306big

tStart = time.time()  # seconds since epoch
f = 0.01  # lowpass filter fraction
dAvg = getTemp()

while True:
    degC = getTemp()
    dAvg = dAvg * (1.0-f) + (f*degC)
    msg1 = "%.2f C" % (degC)
    msg2 = "%.2f C" % (dAvg)
    
    write.clear()
    write.line1(msg1)
    write.line2(msg2)
    
    if (degC > dAvg): # going up or down?
        dir = "+"
    else:
        dir = "-"
    tNow = time.time()
    elapsed = tNow - tStart
    rstr = "%d %s" % (elapsed,dir)
    write.line3(rstr)
    write.show()
    time.sleep(1) 
    
