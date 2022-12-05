# Set PWM level manually with potentiometer
# Use 1.3" SH1106 OLED display
# Pi Pico, uPython v1.15
# 4-Dec-2022 J.Beale

from machine import Pin, ADC, PWM, I2C
from time import sleep, time
import sh1106  # 1.3" wide OLED display

swVersion = "PWM Control 1.1"

VSYS_ADC_INPUT = 3  # read Vsys voltage on ADC
Pin(29, Pin.IN) # no pullup/down for pin 29 reading Vsys
vsysCh = ADC(3) # connects to Vsys
ADCmax = 65535  # max reported by ADC().read_u16
Vref = 3.2335   # measured value of V3.3 (ADC Vref)
Rratio = 3.0    # Pico 3:1 onboard Vsys divider
vScale = Rratio * Vref / ADCmax
vOffset = +0.027  # where does this come from?

def getVsys():  # read vSys in volts
    return (vsysCh.read_u16() * vScale + vOffset)

i2c1 = I2C(1, sda=Pin(14,Pin.PULL_UP), scl=Pin(15,Pin.PULL_UP),  freq=400_000)
#devices = i2c1.scan()
#if devices:
#    for d in devices:
#        print(hex(d))


width = 128
height=64
f = 0.01   # low-pass filter fraction for vsysVoltage avg

# sh1106 library needs some reset pin specified, even if not used
display = sh1106.SH1106_I2C(width, height, i2c1, Pin(2), addr=0x3c, rotate=180)
display.reset()
display.init_display()
sleep(0.1)
display.fill_rect(0,0, 127, 63, 0)
display.text(swVersion,1,1, color=1)
display.show()

# create an input pin on pin #2, with a pull up resistor
p1 = Pin(22, Pin.IN, Pin.PULL_UP) # GPIO22 = Pico Pin 29
p2 = Pin(21, Pin.IN, Pin.PULL_UP) # GPIO21 = Pico Pin 27


TEC=PWM(Pin(12))   # PWM to TEC controller
pwmFreq = 1000
TEC.freq(pwmFreq)

pot=ADC(28)        # creating potentiometer object
nAvg = 10          # average this many ADC readings
loops = 0          # loop counter
vsysVoltage  = getVsys()
vAvg = vsysVoltage
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
                
        vsysVoltage  = getVsys()
        if (vsysVoltage > vMax):
            vMax = vsysVoltage
        if (vsysVoltage < vMin):
            vMin = vsysVoltage
        vAvg = (vAvg * (1.0-f)) + (f * vsysVoltage)
        
        loops += 1
        tElapsed = time() - tStart
        tString = ("%s s %.3f V" % (tElapsed,vAvg))  # elapsed time, V
        if (loops % 10) == 0:
            print("%s, %s" % (outs, tString))
        TEC.duty_u16(potValue)
        
        display.fill_rect(1,19, 50, 10, 1)
        display.text(outs,1,20, color=0)
        
        outs2 = ("%d Hz" % pwmFreq)
        display.fill_rect(64,19, 127, 10, 0)
        display.text(outs2,64,20, color=1)
        display.show()

        outs2 = ("%.2f %.2f %.3f" % (vMin,vMax,vAvg))
        display.fill_rect(0,40, 127, 30, 0)
        display.text(outs2,1,40, color=1)

        display.fill_rect(0,52, 127, 42, 0)
        display.text(tString,1,52, color=1)
        
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
