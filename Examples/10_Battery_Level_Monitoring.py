#!/usr/bin/env/python
# File name   : BatteryLevelMonitoring.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/03/11
import time
import smbus


average_voltage = 0.0

full_voltage = 8.4
WarningThreshold = 6.3
# read the ADC value of channel 0
ADCVref = 5.2
channel = 0
R15 = 3000
R17 = 1000
DivisionRatio = R17 / (R15 + R17)

class ADS7830(object):
    def __init__(self):
        self.cmd = 0x84
        self.bus=smbus.SMBus(1)
        self.address = 0x48 # 0x48 is the default i2c address for ADS7830 Module.   
        
    def analogRead(self, chn): # ADS7830 has 8 ADC input pins, chn:0,1,2,3,4,5,6,7
        value = self.bus.read_byte_data(self.address, self.cmd|(((chn<<2 | chn>>1)&0x07)<<4))
        return value


if __name__ == "__main__":
    adc = ADS7830()
    while True:
        ADCValue = adc.analogRead(channel)    # read the ADC value of channel 0
        A0Voltage = ADCValue / 255.0 * ADCVref  # calculate the voltage value
        actual_battery_voltage = A0Voltage / DivisionRatio
        percentage = int((actual_battery_voltage - WarningThreshold) / (full_voltage - WarningThreshold) * 100)
        print ('ADC Value : %d, actual_battery_voltage %.2f, percentage: %d%%'%(ADCValue, actual_battery_voltage, percentage))
        time.sleep(0.5)
