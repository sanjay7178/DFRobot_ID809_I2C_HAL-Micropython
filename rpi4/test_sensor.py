#!/usr/bin/env python3

from id809 import DFRobot_ID809
import time
import sys

def main():
    print("Starting ID809 sensor test...")
    
    # Create sensor instance with debug enabled
    fp = DFRobot_ID809()
    
    print("\nAttempting to initialize sensor...")
    if fp.begin():
        print("Sensor initialized successfully!")
        
        print("\nTesting connection...")
        if fp.is_connected():
            print("Connection test passed!")
        else:
            print("Connection test failed!")
    else:
        print("Sensor initialization failed!")
        
    print("\nTest complete.")

if __name__ == "__main__":
    main()
