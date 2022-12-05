"""
# vsys.py : Read Pico Vsys voltage using ADC channel 3 (GPIO 29)
# J.Beale 4-Dec-2022

# Usage Example:
import vsys
from time import sleep, time

vs = vsys.Vsys() # to read Pico Vsys voltage
while True:
    volts = vs.read()
    print(volts)
    sleep(1)
"""

from machine import Pin, ADC

class Vsys():
    def __init__(self):
        self.vOffset = +0.027  # individually measured offset
        self.Vref = 3.2335     # individually measured value of ADC Vref
        Pin(29, Pin.IN)        # no pullup/down for pin 29 reading Vsys
        self.vsysCh = ADC(3)   # connects to Vsys
        self.ADCmax = 65535    # max reported by ADC().read_u16
        self.Rratio = 3.0      # Pico 3:1 onboard Vsys divider
        self.vScale = self.Rratio * self.Vref / self.ADCmax

    def read(self):  # read vSys in volts
        return (self.vsysCh.read_u16() * self.vScale + self.vOffset)

