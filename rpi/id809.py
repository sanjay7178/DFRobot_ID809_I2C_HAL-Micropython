from smbus2 import SMBus
import time
import struct
import RPi.GPIO as GPIO

class ID809:
    # Constants
    DEVICE_ADDR = 0x1F
    CMD_PREFIX = 0xAA55
    RCM_PREFIX = 0x55AA
    CMD_TYPE = 0xF0
    ERR_SUCCESS = 0x00
    ERR_ID809 = 0xFF

    def __init__(self, bus_number=1):
        self.bus = SMBus(bus_number)
        self.fingerprint_capacity = 80
        self._number = 0
        self._state = 0
        self._error = self.ERR_SUCCESS
        self._buf = bytearray(32)

    def begin(self):
        try:
            device_info = self.get_device_info()
            if device_info:
                if device_info[-1] == '4':
                    self.fingerprint_capacity = 80
                elif device_info[-1] == '3':
                    self.fingerprint_capacity = 200
                return True
        except:
            pass
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
        return self._buf[0] if ret == self.ERR_SUCCESS else 0

    def collection_fingerprint(self, timeout):
        if self._number > 2:
            self._error = "GATHER_OUT"
            return self.ERR_ID809

        start_time = time.time()
        while not self.detect_finger():
            if (time.time() - start_time) > timeout:
                self._error = "TIMEOUT"
                self._state = 0
                return self.ERR_ID809
            time.sleep(0.01)

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

    # Private methods
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
