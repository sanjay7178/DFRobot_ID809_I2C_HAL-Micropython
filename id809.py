from machine import I2C, Pin
import time
import struct

class ID809:
    # Command codes
    CMD_PREFIX_CODE = 0xAA55
    RCM_PREFIX_CODE = 0x55AA
    CMD_DATA_PREFIX_CODE = 0xA55A
    RCM_DATA_PREFIX_CODE = 0x5AA5
    
    CMD_TYPE = 0xF0
    RCM_TYPE = 0xF0
    DATA_TYPE = 0x0F
    
    # Error codes
    ERR_SUCCESS = 0x00
    ERR_ID809 = 0xFF
    
    # LED modes
    LED_MODES = {
        'BREATHING': 1,
        'FAST_BLINK': 2,
        'KEEPS_ON': 3,
        'NORMAL_CLOSE': 4,
        'FADE_IN': 5,
        'FADE_OUT': 6,
        'SLOW_BLINK': 7
    }
    
    # LED colors  
    LED_COLORS = {
        'GREEN': 1,
        'RED': 2,
        'YELLOW': 3,
        'BLUE': 4,
        'CYAN': 5,
        'MAGENTA': 6,
        'WHITE': 7
    }

    def __init__(self, i2c, address=0x1F):
        self.i2c = i2c
        self.addr = address
        self.fingerprint_capacity = 80
        self._number = 0
        self._state = 0
        self._error = self.ERR_SUCCESS

    def begin(self):
        """Initialize the sensor"""
        device_info = self.get_device_info()
        if device_info:
            if device_info[-1] == '4':
                self.fingerprint_capacity = 80
            elif device_info[-1] == '3':
                self.fingerprint_capacity = 200
            return True
        return False
    
    def is_connected(self):
        """Test connection with sensor"""
        header = self._pack(self.CMD_TYPE, 0x0001, None, 0)
        self._send_packet(header)
        time.sleep_ms(50)
        ret = self._response_payload()
        return ret == self.ERR_SUCCESS

    def ctrl_led(self, mode, color, blink_count):
        """Control the LED ring"""
        data = bytearray(4)
        if self.fingerprint_capacity == 80:
            data[0] = mode
            data[1] = data[2] = color
            data[3] = blink_count
        else:
            # Handle 200 capacity device LED mapping
            mode_map = {1:2, 2:4, 3:1, 4:0, 5:3}
            data[0] = mode_map.get(mode, mode)
            color_val = {1:0x84, 2:0x82, 3:0x86, 4:0x81, 5:0x85, 6:0x83, 7:0x87}
            data[1] = data[2] = color_val.get(color, 0x87)
            
        header = self._pack(self.CMD_TYPE, 0x0024, data, 4)
        self._send_packet(header)
        time.sleep_ms(50)
        return self._response_payload()

    def detect_finger(self):
        """Detect if finger is present"""
        header = self._pack(self.CMD_TYPE, 0x0021, None, 0)
        self._send_packet(header)
        time.sleep_ms(240)
        ret = self._response_payload()
        if ret == self.ERR_SUCCESS:
            return self._buf[0]
        return 0

    def collection_fingerprint(self, timeout):
        """Collect fingerprint image"""
        if self._number > 2:
            self._error = "GATHER_OUT"
            return self.ERR_ID809
            
        start = time.ticks_ms()
        while not self.detect_finger():
            if time.ticks_diff(time.ticks_ms(), start) > timeout * 1000:
                self._error = "TIMEOUT"
                self._state = 0
                return self.ERR_ID809
            time.sleep_ms(10)
            
        ret = self._get_image()
        if ret != self.ERR_SUCCESS:
            self._state = 0
            return self.ERR_ID809
            
        ret = self._generate(self._number)
        if ret != self.ERR_SUCCESS:
            self._state = 0
            return self.ERR_ID809
            
        self._number += 1
        self._state = 1
        return ret

    def store_fingerprint(self, fid):
        """Store collected fingerprint"""
        ret = self._merge()
        if ret != self.ERR_SUCCESS:
            return self.ERR_ID809
            
        self._number = 0
        data = bytearray(4)
        data[0] = fid
        
        header = self._pack(self.CMD_TYPE, 0x0040, data, 4)
        self._send_packet(header)
        time.sleep_ms(360)
        return self._response_payload()

    def search(self):
        """Search for matching fingerprint"""
        if self._state != 1:
            return 0
            
        data = bytearray(6)
        data[2] = 1
        data[4] = self.fingerprint_capacity
        self._number = 0
        
        header = self._pack(self.CMD_TYPE, 0x0063, data, 6)
        self._send_packet(header)
        time.sleep_ms(360)
        
        ret = self._response_payload()
        if ret == self.ERR_SUCCESS:
            return self._buf[0]
        return 0

    # Private helper methods
    def _send_packet(self, packet):
        """Send command packet to sensor"""
        self.i2c.writeto(self.addr, packet)
        
    def _response_payload(self):
        """Read response from sensor"""
        try:
            data = self.i2c.readfrom(self.addr, 32)
            if data[0] != 0xee:
                return self.ERR_ID809
            return self.ERR_SUCCESS
        except:
            return self.ERR_ID809
            
    def _pack(self, cmd_type, cmd, payload, length):
        """Pack command packet"""
        packet = bytearray(26)
        if cmd_type == self.CMD_TYPE:
            struct.pack_into('>H', packet, 0, self.CMD_PREFIX_CODE)
        else:
            struct.pack_into('>H', packet, 0, self.CMD_DATA_PREFIX_CODE)
            
        packet[2] = 0  # SID
        packet[3] = 0  # DID
        struct.pack_into('>H', packet, 4, cmd)
        struct.pack_into('>H', packet, 6, length)
        
        if payload:
            packet[8:8+length] = payload
            
        # Calculate checksum
        cks = 0xFF
        for i in range(2, 8+length):
            cks += packet[i]
        struct.pack_into('>H', packet, 8+length, cks & 0xFFFF)
        
        return packet

    def _get_image(self):
        """Capture fingerprint image"""
        header = self._pack(self.CMD_TYPE, 0x0020, None, 0)
        self._send_packet(header)
        time.sleep_ms(360)
        return self._response_payload()

    def _generate(self, ram_id):
        """Generate fingerprint template"""
        data = bytearray(2)
        data[0] = ram_id
        header = self._pack(self.CMD_TYPE, 0x0060, data, 2)
        self._send_packet(header)
        time.sleep_ms(360)
        return self._response_payload()

    def _merge(self):
        """Merge fingerprint templates"""
        data = bytearray(3)
        data[2] = self._number
        header = self._pack(self.CMD_TYPE, 0x0061, data, 3)
        self._send_packet(header)
        time.sleep_ms(360)
        return self._response_payload()
