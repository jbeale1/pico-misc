# Display AHT10 temperature on OLED module - Pi Pico RP2040
# Uses modified "big font" OLED library
# initially based on github.com/nickpmulder/ssd1306big
# also read AHT25 sensor on another I2C port
# 30-Nov-2022 J.Beale

import ssd1306big # modified OLED library
import time
import utime
from machine import Pin, I2C, ADC, SoftI2C
import ahtx0 # AHT10 https://github.com/targetblank/micropython_ahtx0
import aht # AHT25 https://github.com/etno712/aht


i2c1 = I2C(1, sda=Pin(18), scl=Pin(19),  freq=400_000)
sensor1 = ahtx0.AHT10(i2c1) # AHT10 sensor

i2c2 = SoftI2C(scl=Pin(21), sda=Pin(20), freq=400_000)
sensor2 = aht.AHT2x(i2c2, crc=True) # AHT25 sensor

readInterval = 0.5  # seconds between each reading
avgCount = 10       # how many readings to average

write = ssd1306big  # set up OLED display

tStart = time.time()  # seconds since epoch
f = 0.01  # lowpass filter fraction
dAvg = sensor1.temperature
print("epoch,degC,dAvg,T2,RH1,RH2") # CSV column headers


while True:
    Tsum1 = 0
    Hsum1 = 0
    Tsum2 = 0
    Hsum2 = 0
    for i in range(avgCount):
        Tsum1 += sensor1.temperature
        Hsum1 += sensor1.relative_humidity
        Hsum2 += sensor2.humidity
        Tsum2 += sensor2.temperature
        utime.sleep(readInterval)
        
    degC = Tsum1 / avgCount
    RH1 = Hsum1 / avgCount
    degC2 = Tsum2 / avgCount
    RH2 = Hsum2 / avgCount
    
    dAvg = dAvg * (1.0-f) + (f*degC)
    msg1 = "%.3f C" % (degC)
    msg2 = "%.3f C" % (dAvg)
        
    #H2 = sensor2.humidity
    #T2 = sensor2.temperature
        
    epoch=utime.time() # UNIX epoch, in local time zone
    print("%d, %0.3f, %0.4f, %0.3f, %0.2f,%0.2f" % (epoch,degC,dAvg,degC2,RH1,RH2))
    
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
    write.show() # refresh OLED display
    
