#!/usr/bin/env python3

from smbus2 import SMBus
import time
import struct

class ID809:
    # Constants
    DEVICE_ADDR = 0x1F
    CMD_PREFIX = 0xAA55
    RCM_PREFIX = 0x55AA
    CMD_TYPE = 0xF0
    ERR_SUCCESS = 0x00
    ERR_ID809 = 0xFF

    def __init__(self, bus_number=1):
        print("Initializing ID809...")
        try:
            self.bus = SMBus(bus_number)
            print(f"Successfully opened I2C bus {bus_number}")
        except Exception as e:
            print(f"Failed to open I2C bus: {str(e)}")
            raise e
            
        self.fingerprint_capacity = 80
        self._number = 0
        self._state = 0
        self._error = self.ERR_SUCCESS
        self._buf = bytearray(32)

    def begin(self):
        print("Beginning sensor initialization...")
        try:
            # Test basic I2C communication
            print("Testing I2C communication...")
            self.bus.write_quick(self.DEVICE_ADDR)
            print("Basic I2C write successful")
            
            # Try reading from sensor
            print("Attempting to read from sensor...")
            try:
                data = self.bus.read_i2c_block_data(self.DEVICE_ADDR, 0, 1)
                print(f"Read data from sensor: {data}")
            except Exception as e:
                print(f"Read test failed: {str(e)}")
                return False

            # Test connection with sensor command
            print("Testing sensor connection...")
            if self.is_connected():
                print("Sensor connection test passed")
                return True
            else:
                print("Sensor connection test failed")
                return False

        except Exception as e:
            print(f"Initialization failed with error: {str(e)}")
            return False

    def is_connected(self):
        try:
            print("Checking sensor connection...")
            header = self._pack(self.CMD_TYPE, 0x0001, None, 0)
            print("Command packet created")
            
            print("Sending packet to sensor...")
            self._send_packet(header)
            print("Packet sent")
            
            time.sleep(0.05)
            print("Reading response...")
            response = self._response_payload()
            print(f"Response received: {response}")
            
            return response == self.ERR_SUCCESS
        except Exception as e:
            print(f"Connection check failed: {str(e)}")
            return False

    def _send_packet(self, packet):
        try:
            print(f"Sending packet of length {len(packet)}")
            print(f"Packet data: {[hex(x) for x in packet]}")
            
            for i in range(0, len(packet), 32):
                chunk = packet[i:i + 32]
                print(f"Sending chunk: {[hex(x) for x in chunk]}")
                self.bus.write_i2c_block_data(self.DEVICE_ADDR, 0, list(chunk))
                time.sleep(0.001)
                
            print("Packet sent successfully")
        except Exception as e:
            print(f"Send packet failed: {str(e)}")
            raise e

    def _response_payload(self):
        try:
            print("Reading response...")
            self._buf = bytearray(self.bus.read_i2c_block_data(self.DEVICE_ADDR, 0, 32))
            print(f"Response data: {[hex(x) for x in self._buf]}")
            
            if self._buf[0] == 0xee:
                print("Valid response received")
                return self.ERR_SUCCESS
            else:
                print(f"Invalid response header: {hex(self._buf[0])}")
                return self.ERR_ID809
                
        except Exception as e:
            print(f"Response read failed: {str(e)}")
            return self.ERR_ID809

    def _pack(self, cmd_type, cmd, payload, length):
        try:
            packet = bytearray(26)
            struct.pack_into('>H', packet, 0, self.CMD_PREFIX)
            packet[2:4] = b'\x00\x00'  # SID, DID
            struct.pack_into('>H', packet, 4, cmd)
            struct.pack_into('>H', packet, 6, length)

            if payload:
                packet[8:8+length] = payload

            # Checksum
            cks = 0xFF
            for i in range(2, 8+length):
                cks += packet[i]
            struct.pack_into('>H', packet, 8+length, cks & 0xFFFF)

            print(f"Created packet: {[hex(x) for x in packet]}")
            return packet
        except Exception as e:
            print(f"Packet creation failed: {str(e)}")
            raise e

def main():
    print("Starting debug test...")
    print("Checking I2C devices...")
    
    try:
        # Try to detect I2C devices
        import subprocess
        result = subprocess.run(['i2cdetect', '-y', '1'], capture_output=True, text=True)
        print("i2cdetect output:")
        print(result.stdout)
    except Exception as e:
        print(f"i2cdetect failed: {str(e)}")

    try:
        print("\nInitializing sensor...")
        sensor = ID809()
        
        print("\nStarting sensor...")
        if sensor.begin():
            print("Sensor initialization successful!")
        else:
            print("Sensor initialization failed!")
            
    except Exception as e:
        print(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    main()
