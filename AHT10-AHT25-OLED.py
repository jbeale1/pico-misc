# Display AHT10 temperature on OLED module - Pi Pico RP2040
# Uses modified "big font" OLED library
# initially based on github.com/nickpmulder/ssd1306big
# also read AHT25 sensor (needs external 4.7k pullups)
# publish data to wifi network via MQTT
# 02-Dec-2022 J.Beale

import ssd1306big # modified OLED library
import time
import utime
import ujson         # network secrets in json format
from machine import Pin, I2C, SoftI2C, ADC, RTC, reset
import ahtx0 # AHT10 https://github.com/targetblank/micropython_ahtx0
import aht # AHT25 https://github.com/etno712/aht
import MQ    # custom: connect wifi and MQTT
import ntptime  # to set Pico RTC from NTP time server

def blinkSignal(n,t):    # blink LED n times with delay 'time'
    for i in range(n):
        led.on()
        time.sleep(t)
        led.off()
        time.sleep(t)

def getMsg(T, Ta):    # create message string Temperature and direction
    if (T > Ta): # going up or down?
        dir = "+"
    else:
        dir = "-"        
    msg = "%.3f%s" % (T, dir)
    return(msg)

# ============================================
print("Starting AHT10-AHT25 program...")

i2c1 = I2C(1, sda=Pin(18), scl=Pin(19),  freq=400_000)
sensor1 = ahtx0.AHT10(i2c1) # AHT10 sensor

i2c2 = SoftI2C(scl=Pin(21,Pin.PULL_UP), sda=Pin(20,Pin.PULL_UP), freq=400_000)
sensor2 = aht.AHT2x(i2c2, crc=True) # AHT25 sensor

i2c3 = SoftI2C(sda=Pin(14), scl=Pin(15),  freq=400_000)
sensor3 = ahtx0.AHT10(i2c3) # another AHT10 sensor



led = Pin('LED', Pin.OUT)  # Pico W onboard LED for signals
blinkSignal(3,0.1) # start up indicator

write = ssd1306big  # set up OLED display
write.clear()      # update OLED display
write.line1("AHT10-25")
write.show() # refresh OLED display
print("Opened OLED display")

# ===================================================
topic_pub =  'T3'            # MQTT topic to publish under

with open('secrets.json') as fp:  # network credentials
    secrets = ujson.loads(fp.read())
print("Read credentials...")
mq=MQ.MQTTobject() # wifi + MQTT
mq.initWLAN(secrets)  # start up wifi link

write.line2("wifi")
write.show() # refresh OLED display

try:  # make MQTT connection
   client = mq.mqtt_connect(secrets)
except OSError as e:
   blinkSignal(8,0.1) # error indicator
   reconnect()

write.line3("mqtt on")
write.show() # refresh OLED display

#Vsys = ADC(29) # connected through 3:1 divider to Vbus
#VbusConversion = 3.1 * (3.3 / (65535)) # convert to volts in
# -----------------------------------------------------

t = ntptime.time() # epoch.  local time PST is UTC-8
print(t) # DEBUG
tm = time.gmtime(t)
RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))

readInterval = 0.25  # seconds between each reading
avgCount = 60       # how many readings to average
blankAfter = avgCount / 3  # after this many cycles, blank OLED display

tStart = time.time()  # seconds since epoch
f = 0.05  # lowpass filter fraction

dAvg1 = 0
dAvg2 = 0
dAvg3 = 0
initReads = 3
for i in range(initReads):
    dAvg1 += sensor1.temperature
    dAvg2 += sensor2.temperature
    dAvg3 += sensor3.temperature
dAvg1 /= initReads
dAvg2 /= initReads
dAvg3 /= initReads

print("epoch,T1,T2,T3, RH1,RH2,RH3, Vbus") # CSV column headers


while True:
    try:
        Tsum1 = 0
        Hsum1 = 0
        Tsum2 = 0
        Hsum2 = 0
        Tsum3 = 0
        Hsum3 = 0
        Vbus = 0  # reading of input supply voltage
        for i in range(avgCount):
            Tsum1 += sensor1.temperature
            Hsum1 += sensor1.relative_humidity
            Hsum2 += sensor2.humidity
            Tsum2 += sensor2.temperature
            Hsum3 += sensor3.relative_humidity
            Tsum3 += sensor3.temperature
            # Vbus += Vsys.read_u16() * VbusConversion # volts from ext. power
            utime.sleep(readInterval)
            if (i == blankAfter):
                write.clear() # blank OLED
                write.show()  # refresh status

            
        degC1 = Tsum1 / avgCount
        RH1 = Hsum1 / avgCount
        degC2 = Tsum2 / avgCount
        RH2 = Hsum2 / avgCount
        degC3 = Tsum3 / avgCount
        RH3 = Hsum3 / avgCount
        #Vbus /= avgCount
        
        dAvg1 = dAvg1 * (1.0-f) + (f*degC1)
        dAvg2 = dAvg2 * (1.0-f) + (f*degC2)
        dAvg3 = dAvg3 * (1.0-f) + (f*degC3)
                   
        epoch=utime.time() # UNIX epoch, in local time zone
        outs = ("%d, %0.3f,%0.3f,%0.3f, %0.2f,%0.2f,%0.2f" %
              (epoch,degC1,degC2,degC3,RH1,RH2,RH3))
        print(outs)
        # MQTT publish prone to [Errno 104] ECONNRESET
        try:
            client.publish(topic_pub, outs)
        except Exception as e:
            print(e)           
            try:  # try to reconnect MQTT
                client = mq.mqtt_connect(secrets)
            except OSError as e:
                print("Could not reconnect")
                write.clear()      # update OLED display
                write.line1("MQTT ERR")
                write.show() # refresh OLED display
                blinkSignal(8,0.1) # error indicator
                pass
            pass  # oh well, will try next time
        
        tNow = time.time()

        write.clear()      # update OLED display
        msg = getMsg(degC1, dAvg1)
        write.line1(msg)
        msg = getMsg(degC2, dAvg2)
        write.line2(msg)
        msg = getMsg(degC3, dAvg3)
        write.line3(msg)
        write.show() # refresh OLED display
    except OSError as e:
        print("Encountered OSError in main loop")
        print(e)
        write.clear()      # update OLED display
        write.line1("ERROR")
        write.line2(e)
        write.show() # refresh OLED display
        time.sleep(5)
        reset()
