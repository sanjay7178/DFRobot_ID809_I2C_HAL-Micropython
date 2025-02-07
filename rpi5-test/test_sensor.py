#!/usr/bin/env python3

import os
import sys
import time
import subprocess
from id809 import DFRobot_ID809

def check_i2c_devices():
    """Scan for I2C devices"""
    print("\nScanning I2C bus:")
    try:
        output = subprocess.check_output(['i2cdetect', '-y', '1']).decode()
        print(output)
    except:
        print("Could not scan I2C bus")

def check_voltages():
    """Try to read power-related sysfs entries"""
    print("\nPower status:")
    try:
        with open('/sys/class/power_supply/rpi_power/voltage_now', 'r') as f:
            voltage = float(f.read().strip()) / 1000000
            print(f"System voltage: {voltage:.2f}V")
    except:
        print("Could not read system voltage")

def test_i2c_read(address):
    """Test reading from I2C address"""
    import smbus2
    bus = smbus2.SMBus(1)
    print(f"\nTesting I2C read from address 0x{address:02X}:")
    try:
        data = bus.read_byte(address)
        print(f"Read successful: 0x{data:02X}")
        return True
    except Exception as e:
        print(f"Read failed: {str(e)}")
        return False
    finally:
        bus.close()

def main():
    print("Starting ID809 sensor extended diagnostic test...")
    
    # Check I2C devices
    check_i2c_devices()
    
    # Check power
    check_voltages()
    
    # Test direct I2C read
    test_i2c_read(0x1F)
    
    print("\nInitializing sensor...")
    fp = DFRobot_ID809()
    
    for attempt in range(3):
        print(f"\nAttempt {attempt + 1}:")
        if fp.begin():
            print("✓ Sensor initialized successfully!")
            
            if fp.is_connected():
                print("✓ Connection test passed!")
                sys.exit(0)
            else:
                print("✗ Connection test failed")
        else:
            print("✗ Initialization failed")
        time.sleep(1)
    
    print("\nDiagnostic checklist:")
    print("□ Verify these connections:")
    print("  - VCC → RPi 3.3V (Pin 1)")
    print("  - GND → RPi GND (Pin 6)")
    print("  - SDA → RPi SDA (Pin 3)")
    print("  - SCL → RPi SCL (Pin 5)")
    print("  - IRQ/Touch → RPi GPIO (if present)")
    print("□ Check voltages with multimeter:")
    print("  - VCC to GND should be 3.3V")
    print("  - SDA to GND should be ~3.3V")
    print("  - SCL to GND should be ~3.3V")
    print("□ Verify I2C is enabled:")
    print("  sudo raspi-config")
    print("□ Check I2C permissions:")
    print("  sudo usermod -aG i2c $USER")

if __name__ == "__main__":
    main()
