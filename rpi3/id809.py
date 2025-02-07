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

    # LED Modes
    LED_BREATHING = 1
    LED_FAST_BLINK = 2
    LED_ON = 3
    LED_OFF = 4
    LED_FADE_IN = 5
    LED_FADE_OUT = 6
    LED_SLOW_BLINK = 7

    # LED Colors
    LED_GREEN = 1
    LED_RED = 2
    LED_YELLOW = 3
    LED_BLUE = 4
    LED_CYAN = 5
    LED_MAGENTA = 6
    LED_WHITE = 7

    def __init__(self, bus_number=1):
        self.bus = SMBus(bus_number)
        self.fingerprint_capacity = 80
        self._number = 0
        self._state = 0
        self._error = self.ERR_SUCCESS
        self._buf = bytearray(32)

    def begin(self):
        return self.is_connected()

    def verify_fingerprint(self):
        """Verify fingerprint with proper detection"""
        print("\nPlace finger to verify")
        self.ctrl_led(self.LED_BREATHING, self.LED_BLUE, 0)
        
        if self.collection_fingerprint(10) == 0:
            print("Scanning...")
            match_id = self.search()
            
            if match_id > 0:  # Ensure we have a valid match ID
                print(f"Match found! ID #{match_id}")
                self.ctrl_led(self.LED_ON, self.LED_GREEN, 0)
                return match_id
            else:
                print("No match found")
                self.ctrl_led(self.LED_ON, self.LED_RED, 0)
                return 0
        else:
            print("Scan failed!")
            self.ctrl_led(self.LED_ON, self.LED_RED, 0)
            return 0

    def enroll_fingerprint(self, empty_id):
        """Full enrollment process with proper finger detection"""
        for i in range(3):
            self.ctrl_led(self.LED_BREATHING, self.LED_BLUE, 0)
            print(f"\nPlace finger for scan #{i+1}")
            
            # Wait for finger placement and capture
            if self.collection_fingerprint(10) != 0:
                print("Scan failed! Try again")
                continue
            
            self.ctrl_led(self.LED_FAST_BLINK, self.LED_YELLOW, 3)
            print("Remove finger")
            
            # Wait for finger removal
            while self.detect_finger():
                time.sleep(0.1)
            print("Finger removed")
            time.sleep(1)
        
        print("\nProcessing...")
        if self.store_fingerprint(empty_id) == 0:
            return True
        return False

    def is_connected(self):
        try:
            header = self._pack(self.CMD_TYPE, 0x0001, None, 0)
            self._send_packet(header)
            time.sleep(0.05)
            return self._response_payload() == self.ERR_SUCCESS
        except:
            return False

    def detect_finger(self):
        header = self._pack(self.CMD_TYPE, 0x0021, None, 0)
        self._send_packet(header)
        time.sleep(0.24)
        ret = self._response_payload()
        if ret == self.ERR_SUCCESS:
            # Check if finger is actually present (0x00 = no finger, 0x01 = finger detected)
            return self._buf[0] == 0x01
        return False


    def collection_fingerprint(self, timeout):
        if self._number > 2:
            self._error = "GATHER_OUT"
            return self.ERR_ID809

        print("Waiting for finger...")
        start_time = time.time()
        
        # Wait for finger to be placed
        while not self.detect_finger():
            if (time.time() - start_time) > timeout:
                print("Timeout waiting for finger!")
                self._error = "TIMEOUT"
                self._state = 0
                return self.ERR_ID809
            time.sleep(0.1)
        
        print("Finger detected!")
        time.sleep(0.5)  # Small delay to ensure finger is stable
        
        ret = self._get_image()
        if ret != self.ERR_SUCCESS:
            print("Failed to capture image!")
            self._state = 0
            return self.ERR_ID809

        ret = self._generate(self._number)
        if ret != self.ERR_SUCCESS:
            print("Failed to generate template!")
            self._state = 0
            return self.ERR_ID809

        self._number += 1
        self._state = 1
        return ret



    def store_fingerprint(self, fid):
        ret = self._merge()
        if ret != self.ERR_SUCCESS:
            return self.ERR_ID809

        self._number = 0
        data = bytearray(4)
        data[0] = fid

        header = self._pack(self.CMD_TYPE, 0x0040, data, 4)
        self._send_packet(header)
        time.sleep(0.36)
        return self._response_payload()

    def search(self):
        if self._state != 1:
            return 0

        data = bytearray(6)
        data[2] = 1
        data[4] = self.fingerprint_capacity
        self._number = 0

        header = self._pack(self.CMD_TYPE, 0x0063, data, 6)
        self._send_packet(header)
        time.sleep(0.36)

        ret = self._response_payload()
        return self._buf[0] if ret == self.ERR_SUCCESS else 0

    def get_empty_id(self):
        data = bytearray(4)
        data[0] = 1
        data[2] = self.fingerprint_capacity

        header = self._pack(self.CMD_TYPE, 0x0045, data, 4)
        self._send_packet(header)
        time.sleep(0.1)

        ret = self._response_payload()
        return self._buf[0] if ret == self.ERR_SUCCESS else self.ERR_ID809

    def ctrl_led(self, mode, color, blink_count):
        data = bytearray(4)
        data[0] = mode
        data[1] = data[2] = color
        data[3] = blink_count

        header = self._pack(self.CMD_TYPE, 0x0024, data, 4)
        self._send_packet(header)
        time.sleep(0.05)
        return self._response_payload()

    def _send_packet(self, packet):
        for i in range(0, len(packet), 32):
            chunk = packet[i:i + 32]
            self.bus.write_i2c_block_data(self.DEVICE_ADDR, 0, list(chunk))
            time.sleep(0.001)

    def _response_payload(self):
        try:
            self._buf = bytearray(self.bus.read_i2c_block_data(self.DEVICE_ADDR, 0, 32))
            return self.ERR_SUCCESS if self._buf[0] == 0xee else self.ERR_ID809
        except:
            return self.ERR_ID809

    def _pack(self, cmd_type, cmd, payload, length):
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

        return packet

    def _get_image(self):
        header = self._pack(self.CMD_TYPE, 0x0020, None, 0)
        self._send_packet(header)
        time.sleep(0.36)
        return self._response_payload()

    def _generate(self, ram_id):
        data = bytearray(2)
        data[0] = ram_id
        header = self._pack(self.CMD_TYPE, 0x0060, data, 2)
        self._send_packet(header)
        time.sleep(0.36)
        return self._response_payload()

    def _merge(self):
        data = bytearray(3)
        data[2] = self._number
        header = self._pack(self.CMD_TYPE, 0x0061, data, 3)
        self._send_packet(header)
        time.sleep(0.36)
        return self._response_payload()


def main():
    print("Initializing fingerprint sensor...")
    fp = ID809()
    
    if not fp.begin():
        print("Failed to initialize sensor!")
        return

    print("Sensor initialized successfully!")
    
    while True:
        print("\nFingerprint Sensor Menu:")
        print("1. Enroll New Fingerprint")
        print("2. Verify Fingerprint")
        print("3. Test LED")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ")

        if choice == '1':
            empty_id = fp.get_empty_id()
            if empty_id == fp.ERR_ID809:
                print("No empty slots available!")
                continue

            print(f"\nStarting enrollment for ID #{empty_id}")
            print("You'll need to scan your finger 3 times")
            
            if fp.enroll_fingerprint(empty_id):
                print(f"Success! Fingerprint stored as ID #{empty_id}")
                fp.ctrl_led(fp.LED_ON, fp.LED_GREEN, 0)
            else:
                print("Failed to store fingerprint!")
                fp.ctrl_led(fp.LED_ON, fp.LED_RED, 0)
            
            time.sleep(2)
            fp.ctrl_led(fp.LED_OFF, fp.LED_BLUE, 0)

        elif choice == '2':
            match_id = fp.verify_fingerprint()
            if match_id > 0:
                print(f"Match found! ID #{match_id}")
            time.sleep(2)
            fp.ctrl_led(fp.LED_OFF, fp.LED_BLUE, 0)

        elif choice == '3':
            print("\nTesting LED patterns...")
            modes = [fp.LED_BREATHING, fp.LED_FAST_BLINK, fp.LED_ON, fp.LED_FADE_IN]
            colors = [fp.LED_BLUE, fp.LED_GREEN, fp.LED_RED, fp.LED_YELLOW]
            
            for mode in modes:
                for color in colors:
                    print(f"Testing mode {mode} with color {color}")
                    fp.ctrl_led(mode, color, 3)
                    time.sleep(2)
            
            fp.ctrl_led(fp.LED_OFF, fp.LED_BLUE, 0)
            print("LED test complete")

        elif choice == '4':
            print("\nExiting...")
            break

        else:
            print("\nInvalid choice! Please select 1-4")








if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
