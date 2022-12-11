# Set PWM level manually with potentiometer
# Also measure Vsys voltage with ADC
# Uses 1.3" SH1106 OLED display
# Pi Pico, uPython v1.19.1
# 4-Dec-2022 J.Beale

from machine import Pin, ADC, PWM, I2C
from time import sleep, time
import sh1106  # OLED driver from github.com/robert-hh/SH1106
import vsys    # read Vsys voltage

swVersion = "PWM Control 1.2"

i2c1 = I2C(1, sda=Pin(14,Pin.PULL_UP), scl=Pin(15,Pin.PULL_UP),  freq=400_000)
#devices = i2c1.scan()
#if devices:
#    for d in devices:
#        print(hex(d))


width = 128
height=64
f = 0.01   # low-pass filter fraction for vsysVoltage avg

# Set up OLED with sh1106 library
display = sh1106.SH1106_I2C(width, height, i2c1, None, addr=0x3c, rotate=180)
display.sleep(False)
display.fill(0)
display.text(swVersion,1,1, color=1)
display.show()

# pushbuttons to ground to INC/DEC the PWM frequency
p1 = Pin(22, Pin.IN, Pin.PULL_UP) # GPIO22 = Pico Pin 29
p2 = Pin(21, Pin.IN, Pin.PULL_UP) # GPIO21 = Pico Pin 27

vs = vsys.Vsys(vref=3.210, voff=0.02) # to read Pico Vsys voltage
    
TEC=PWM(Pin(12))   # PWM to TEC controller
pwmFreq = 1000
TEC.freq(pwmFreq)

pot=ADC(28)        # creating potentiometer object
nAvg = 10          # average this many ADC readings
loops = 0          # loop counter

vAvg = vs.read()   # read Vsys voltage
vMax = vAvg
vMin = vAvg

tStart = time()    # uPython epoch from Jan.2000

try:
    while True:
        potValue = 0
        for i in range(nAvg):
            potValue += pot.read_u16()           #reading analog pin
            sleep(0.01)
        potValue = int(potValue/ nAvg)
        pct = 100.0 * potValue/65535
        outs=("%0.1f %%" % pct)              # PWM setting in # from 0..100
                
        vsysVoltage = vs.read()   # read Vsys voltage
        if (vsysVoltage > vMax):
            vMax = vsysVoltage
        if (vsysVoltage < vMin):
            vMin = vsysVoltage
        vAvg = (vAvg * (1.0-f)) + (f * vsysVoltage)
        
        loops += 1
        tElapsed = time() - tStart
        tString = ("%s s %.3f V" % (tElapsed,vsysVoltage))  # elapsed time, V
        if (loops % 10) == 0:
            print("%s, %s" % (outs, tString))
        TEC.duty_u16(potValue)

        display.fill_rect(0,10,128,63, 0)
        display.text(outs,1,20, color=1)
        
        outs2 = ("%d Hz" % pwmFreq)
        display.text(outs2,64,20, color=1)

        outs2 = ("%.2f %.2f %.4f" % (vMin,vMax,vAvg))
        display.text(outs2,1,40, color=1)

        display.text(tString,1,52, color=1)
        display.show()


        if (p1.value() == 0):  # up/down control for PWM frequency
            pwmFreq *= 1.05
        if (p2.value() == 0):
            pwmFreq /= 1.05
        if (pwmFreq < 1000):  # limit minimum PWM frequency
            pwmFreq = 1000
        TEC.freq(int(pwmFreq))
        sleep(0.25)
        
except KeyboardInterrupt:
    TEC.duty_u16(0)
    print("Program has halted, PWM set to 0")
    
