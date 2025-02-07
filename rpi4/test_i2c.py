#!/usr/bin/env python3

from id809 import DFRobot_ID809
import time
import smbus2

def check_i2c():
    """Check I2C configuration and device presence"""
    try:
        # Try to open the I2C bus
        bus = smbus2.SMBus(1)
        print("I2C bus opened successfully")
        
        # Try to read from the device address
        try:
            bus.read_byte(0x1F)
            print("Successfully read from device at address 0x1F")
        except OSError as e:
            print(f"Failed to read from device: {e}")
            
        bus.close()
        
    except Exception as e:
        print(f"Failed to open I2C bus: {e}")
        return False
    
    return True

def main():
    print("Starting fingerprint sensor test...")
    
    # Check I2C setup
    print("\nChecking I2C configuration...")
    if not check_i2c():
        print("I2C setup failed!")
        return
        
    print("\nInitializing sensor...")
    try:
        fp = DFRobot_ID809()
        if fp.begin():
            print("Sensor initialized successfully!")
            
            # Test basic communication
            if fp.is_connected():
                print("Communication test passed!")
            else:
                print("Communication test failed!")
        else:
            print("Sensor initialization failed!")
            
    except Exception as e:
        print(f"Error during initialization: {e}")
        
if __name__ == "__main__":
    main()
