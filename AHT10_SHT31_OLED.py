# Read AHT10, SHT31 Temp/RH sensors
# Uses 1.3" SH1106 OLED display
# Pi Pico, uPython v1.19.1
# 08-Feb-2023 J.Beale

from machine import Pin, ADC, PWM, I2C, SoftI2C
from time import sleep, time, ticks_ms
import utime
import sh1106  # OLED  driver: github.com/robert-hh/SH1106
import ahtx0   # AHT10 driver: github.com/targetblank/micropython_ahtx0
import sys

swVersion = "RH Readout 0.4"

# I2C connection to OLED display (addr = 0x3c)
i2c1 = I2C(1, sda=Pin(14,Pin.PULL_UP), scl=Pin(15,Pin.PULL_UP), freq=400_000)

# I2C connection to AHT10 sensor1 (addr = 0x38)
i2c0 = I2C(0, sda=Pin(16,Pin.PULL_UP), scl=Pin(17,Pin.PULL_UP), freq=400_000)

# I2C connection to AHT10 sensor2 (addr = 0x3c)
i2c2 = SoftI2C(scl=Pin(19,Pin.PULL_UP), sda=Pin(18,Pin.PULL_UP), freq=400_000)

# I2C connection to AHT10 sensor3 (addr = 0x3c)
i2c3 = SoftI2C(scl=Pin(13,Pin.PULL_UP), sda=Pin(12,Pin.PULL_UP), freq=400_000)

# I2C connection to SHT31 sensor4 (addr = 0x44)
i2c4= SoftI2C(scl=Pin(9,Pin.PULL_UP), sda=Pin(8,Pin.PULL_UP), freq=400_000)

#devices = i2c4.scan()
#if devices:
#    for d in devices:
#        print(hex(d))       
#sys.exit()        

sensor1 = ahtx0.AHT10(i2c0) # AHT10 sensor #1
sensor2 = ahtx0.AHT10(i2c2) # AHT10 sensor #2
sensor3 = ahtx0.AHT10(i2c3) # AHT10 sensor #3
# sensor4 = sht3x.SHT3X(i2c4) # SHT31 sensor #4

# command words for SHT3x sensor
CMD_DoOneShot = b'\x24\x00' # one-shot measure, H type
CMD_DoReset   = b'\x30\xa2' # soft reset command
CMD_HeaterOn  = b'\x30\x6d' # turn heater on
CMD_HeaterOff = b'\x30\x66' # turn heater off
 
# calculates 8-Bit checksum for SHT3x using given polynomial
def CRC_8(data):
  POLY = 0x131  # P(x) = x^8 + x^5 + x^4 + 1 = 100110001
  crc = 0xff    # CRC is single byte, starting with value 0xFF
  for byte in data:
    crc ^= byte
    for _ in range (8):
      if(crc & 0x80):
          crc = (crc << 1) ^ POLY
      else:
          crc = (crc << 1)
  return crc

def TRH_get(self): # for SHT3x Temp/RH sensor
        status = self.i2c.writeto(self.addr,CMD_DoOneShot) 
        utime.sleep(1)
        buf = self.i2c.readfrom(self.addr, 6) # get 6 bytes
        buf1 = bytes([buf[0], buf[1], buf[2]])  # 2 bytes + CRC
        c1 = CRC_8(buf1)  # should be zero
        buf2 = bytes([buf[3], buf[4], buf[5]])  # 2 bytes + CRC
        c2 = CRC_8(buf2)  # should be zero
        if (c1 != 0) or (c2 != 0):  # CRC error on Temp or RH
            print("# ERROR %d %d",c1,c2)
            return([-999,-999])
        temperature_raw = buf[0] << 8 | buf[1]
        temperature = (175.0 * float(temperature_raw) / 65535.0) - 45
        humidity_raw = buf[3] << 8  | buf[4]
        humidity = (100.0 * float(humidity_raw) / 65535.0)
        sensor_data = [temperature, humidity]
        return sensor_data

def TRH_reset(self):
        status = self.i2c.writeto(self.addr,CMD_DoReset) 

def TRH_SetHeat(self, heat):
    if (heat == True):
        status = self.i2c.writeto(self.addr,CMD_HeaterOn) 
    else:
        status = self.i2c.writeto(self.addr,CMD_HeaterOff) 

class Object(object):
    pass

sense4 = Object()
sense4.i2c = i2c4  # an i2c object (HW or SW)
sense4.addr = 0x44 # i2C address of device on bus
TRH_reset(sense4)

SHT31_Heat = False  # if the internal heater is turned on
TRH_SetHeat(sense4, SHT31_Heat)  # update the heater value

# sys.exit()

width = 128  # OLED size
height=64

# Set up OLED with sh1106 library
display = sh1106.SH1106_I2C(width, height, i2c1, None, addr=0x3c, rotate=180)
display.sleep(False)
display.fill(0)
display.text(swVersion,1,1, color=1)
display.show()


avgCount = 10  # how many readings to average together
#readInterval = 0.156  # 0.163 seconds between each reading (1 ch)
#readInterval = 0.07  # 0.163 seconds between each reading (2 ch)

CycleLength = 40 # how many cycles before switching heater on/off

tCycles = 0  # loop counter
tStart = ticks_ms()

print("sec, T1, T2, T3, T4, RH1, RH2, RH3, RH4, T")  # CSV column headers

while True:
    try:
        Tsum1 = 0
        Hsum1 = 0
        Tsum2 = 0
        Hsum2 = 0
        Tsum3 = 0
        Hsum3 = 0
        Tsum4 = 0
        Hsum4 = 0
        for i in range(avgCount):
            Tsum1 += sensor1.temperature
            Hsum1 += sensor1.relative_humidity
            Tsum2 += sensor2.temperature
            Hsum2 += sensor2.relative_humidity
            Tsum3 += sensor3.temperature
            Hsum3 += sensor3.relative_humidity
            trhData = TRH_get(sense4)
            Tsum4 += trhData[0]
            Hsum4 += trhData[1]

            # utime.sleep(readInterval)
            
        degC = Tsum1 / avgCount
        RH = Hsum1 / avgCount
        degC2 = Tsum2 / avgCount
        RH2 = Hsum2 / avgCount
        degC3 = Tsum3 / avgCount
        RH3 = Hsum3 / avgCount
        degC4 = Tsum4 / avgCount
        RH4 = Hsum4 / avgCount
        et = (ticks_ms() - tStart)/1000.0 # units of seconds
        print("%.1f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %d"
              % (et, degC, degC2, degC3, degC4, RH, RH2, RH3, RH4, SHT31_Heat))
        msg1 = ("1 %4.2fC %4.2f%%" % (degC, RH))
        msg2 = ("2 %4.2fC %4.2f%%" % (degC2, RH2))
        msg3 = ("3 %4.2fC %4.2f%%" % (degC3, RH3))
        msg4 = ("4 %4.2fC %4.2f%%" % (degC4, RH4))
        msgT = ("%.1f s" % (et))
        display.fill(0)
        display.text(msg1,1,10, color=1)
        display.text(msg2,1,20, color=1)
        display.text(msg3,1,30, color=1)
        display.text(msg4,1,40, color=1)
        display.text(msgT,1,50, color=1)
        display.show()
        
        tCycles += 1
        if (tCycles >= CycleLength):
            tCycles = 0
            SHT31_Heat = not (SHT31_Heat)
        TRH_SetHeat(sense4, SHT31_Heat)  # update the heater value

        
    except OSError as e:
        print("Encountered OSError in main loop")
        print(e)
        write.clear()      # update OLED display
        write.line1("ERROR")
        write.line2(e)
        write.show() # refresh OLED display
        time.sleep(5)
        reset()            
