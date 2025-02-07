#### DFRobot_ID809_I2C_HAL-Micropython

MicroPython version:

1. Simplified class structure using native MicroPython I2C implementation
2. Removed Arduino-specific memory management 
3. Implemented core fingerprint functions: enrollment, verification, LED control
4. Used time.sleep_ms() for timing instead of Arduino delay()
5. Streamlined error handling and packet processing
6. Removed hardware serial communication, using only I2C

The code supports the main functionality of fingerprint enrollment, verification, and LED control. You'll need to connect the sensor's SDA and SCL pins to your MicroPython board's I2C pins.


---

Here are the pin connections between Raspberry Pi 4 and the DFRobot ID809 fingerprint sensor:

```
Raspberry Pi 4           ID809 Sensor
------------------------------------
Pin 1 (3.3V)    -->     VCC
Pin 3 (SDA1/GPIO2) -->  SDA 
Pin 5 (SCL1/GPIO3) -->  SCL
Pin 6 (GND)     -->     GND
Pin 40 (GPIO21) -->     IRQ (optional, for interrupt)
```

Key notes:
- Sensor operates on 3.3V 
- Uses I2C communication (SDA/SCL)
- Default I2C address: 0x1F
- Enable I2C in raspi-config if not already enabled
