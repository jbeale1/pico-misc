# Read two AHT10 Temp/RH sensors
# Uses 1.3" SH1106 OLED display
# Pi Pico, uPython v1.19.1
# 14-Dec-2022 J.Beale

from machine import Pin, ADC, PWM, I2C, SoftI2C
from time import sleep, time, ticks_ms
import utime
import sh1106  # OLED driver from github.com/robert-hh/SH1106
import ahtx0   # AHT10 https://github.com/targetblank/micropython_ahtx0
import vsys    # read Vsys voltage

swVersion = "RH Readout 0.2"

# I2C connection to OLED display (addr = 0x3c)
i2c1 = I2C(1, sda=Pin(14,Pin.PULL_UP), scl=Pin(15,Pin.PULL_UP), freq=400_000)

# I2C connection to AHT10 sensor (addr = 0x38)
i2c0 = I2C(0, sda=Pin(16,Pin.PULL_UP), scl=Pin(17,Pin.PULL_UP), freq=400_000)

# I2C connection to OLED display2 (addr = 0x3c)
i2c2 = SoftI2C(scl=Pin(19,Pin.PULL_UP), sda=Pin(18,Pin.PULL_UP), freq=400_000)

#devices = i2c2.scan()
#if devices:
#    for d in devices:
#        print(hex(d))

sensor1 = ahtx0.AHT10(i2c0) # AHT10 sensor #1
sensor2 = ahtx0.AHT10(i2c2) # AHT10 sensor #2


width = 128  # OLED size
height=64

# Set up OLED with sh1106 library
display = sh1106.SH1106_I2C(width, height, i2c1, None, addr=0x3c, rotate=180)
display.sleep(False)
display.fill(0)
display.text(swVersion,1,1, color=1)
display.show()

# pushbuttons to ground to INC/DEC the PWM frequency
p1 = Pin(22, Pin.IN, Pin.PULL_UP) # GPIO22 = Pico Pin 29
p2 = Pin(21, Pin.IN, Pin.PULL_UP) # GPIO21 = Pico Pin 27

# vs = vsys.Vsys(vref=3.210, voff=0.02) # to read Pico Vsys voltage

avgCount = 4  # how many readings to average together
#readInterval = 0.156  # 0.163 seconds between each reading (1 ch)
readInterval = 0.07  # 0.163 seconds between each reading (2 ch)

tStart = ticks_ms()

print("sec, T1, T2, RH1, RH2")  # CSV column headers

while True:
    try:
        Tsum1 = 0
        Hsum1 = 0
        Tsum2 = 0
        Hsum2 = 0
        for i in range(avgCount):
            Tsum1 += sensor1.temperature
            Hsum1 += sensor1.relative_humidity
            Tsum2 += sensor2.temperature
            Hsum2 += sensor2.relative_humidity
            utime.sleep(readInterval)
            
        degC = Tsum1 / avgCount
        RH = Hsum1 / avgCount
        degC2 = Tsum2 / avgCount
        RH2 = Hsum2 / avgCount
        et = (ticks_ms() - tStart)/1000.0 # units of seconds
        print("%.1f, %.3f, %.3f, %.3f, %.3f" % (et, degC, degC2, RH, RH2))
        msg1 = ("%4.3fC %4.3f%%" % (degC, RH))
        msg2 = ("%4.3fC %4.3f%%" % (degC2, RH2))
        msg3 = ("%.1f s" % (et))
        display.fill(0)
        display.text(msg1,1,10, color=1)
        display.text(msg2,1,20, color=1)
        display.text(msg3,1,30, color=1)
        display.show()
        
    except OSError as e:
        print("Encountered OSError in main loop")
        print(e)
        write.clear()      # update OLED display
        write.line1("ERROR")
        write.line2(e)
        write.show() # refresh OLED display
        time.sleep(5)
        reset()
