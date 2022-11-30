# Read one AHT10 Temp/RH sensor on Pi Pico I2C bus 1
# (Mfr suggests 1 read / 5 sec, due to self-heating)
# 29-Nov-2022 J.Beale

import utime
from machine import Pin, I2C
import ahtx0 # https://github.com/targetblank/micropython_ahtx0

i2c1 = I2C(1, sda=Pin(18), scl=Pin(19),  freq=400_000)

sensor1 = ahtx0.AHT10(i2c1)
avgCount = 5

while True:
    Tsum1 = 0
    Hsum1 = 0
    for i in range(avgCount):
        Tsum1 += sensor1.temperature
        Hsum1 += sensor1.relative_humidity
        utime.sleep(0.2)
        
    T1 = Tsum1 / avgCount
    H1 = Hsum1 / avgCount    
    epoch=utime.time() # UNIX epoch, in local time zone
    print("%d, %0.3f, %0.3f" % (epoch,T1,H1))
