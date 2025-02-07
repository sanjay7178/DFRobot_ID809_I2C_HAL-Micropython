#!/usr/bin/env python3

import smbus2 as smbus
import time
from enum import Enum
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LEDMode(Enum):
    BREATHING = 1
    FAST_BLINK = 2
    KEEPS_ON = 3
    NORMAL_CLOSE = 4
    FADE_IN = 5
    FADE_OUT = 6
    SLOW_BLINK = 7

class LEDColor(Enum):
    GREEN = 1
    RED = 2
    YELLOW = 3
    BLUE = 4
    CYAN = 5
    MAGENTA = 6
    WHITE = 7

class ID809:
    # Command packet prefix codes
    CMD_PREFIX_CODE = 0xAA55
    RCM_PREFIX_CODE = 0x55AA
    CMD_DATA_PREFIX_CODE = 0xA55A
    RCM_DATA_PREFIX_CODE = 0x5AA5

    # Command codes
    CMD_TEST_CONNECTION = 0x0001
    CMD_SET_PARAM = 0x0002
    CMD_GET_PARAM = 0x0003
    CMD_GET_DEVICE_INFO = 0x0004
    CMD_SET_MODULE_SN = 0x0008
    CMD_GET_MODULE_SN = 0x0009
    CMD_ENTER_STANDBY_STATE = 0x000C
    CMD_GET_IMAGE = 0x0020
    CMD_FINGER_DETECT = 0x0021
    CMD_SLED_CTRL = 0x0024
    CMD_STORE_CHAR = 0x0040
    CMD_SEARCH = 0x0063
    CMD_VERIFY = 0x0064
    CMD_DEL_CHAR = 0x0044

    def __init__(self, bus_number=1, address=0x1F):
        """Initialize the ID809 fingerprint sensor."""
        try:
            self.bus = smbus.SMBus(bus_number)
            self.address = address
            self._fingerprint_capacity = 80
            logger.info(f"Initialized ID809 on bus {bus_number} at address 0x{address:02X}")
            
            # Initial device reset sequence
            self._reset_device()
            
        except Exception as e:
            logger.error(f"Failed to initialize SMBus: {str(e)}")
            raise

    def _reset_device(self):
        """Reset the device communication state."""
        try:
            # Read a byte to check device state
            self.bus.read_byte(self.address)
            time.sleep(0.1)
        except:
            pass
        
        # Wait for device to be ready
        time.sleep(0.5)

    def _wait_for_ready(self):
        """Wait for the device to be ready (not returning 0xEE)."""
        max_retries = 10
        for _ in range(max_retries):
            try:
                value = self.bus.read_byte(self.address)
                if value != 0xEE:
                    return True
                time.sleep(0.1)
            except:
                time.sleep(0.1)
        return False

    def _send_packet(self, cmd_type, cmd, payload=None):
        """Send a command packet to the sensor."""
        try:
            if payload is None:
                payload = []
                
            # Wait for device to be ready
            if not self._wait_for_ready():
                logger.error("Device not ready")
                return False
                
            # Construct packet header
            packet = []
            # Prefix (AA 55)
            packet.extend([0xAA, 0x55])
            # SID and DID
            packet.extend([0x00, 0x00])
            # Command
            packet.extend([cmd >> 8, cmd & 0xFF])
            # Length
            packet.extend([len(payload) >> 8, len(payload) & 0xFF])
            
            # Add payload
            packet.extend(payload)
            
            # Calculate checksum
            cks = 0xFF
            for b in packet[2:]:  # Skip prefix bytes
                cks += b
            packet.extend([cks & 0xFF, (cks >> 8) & 0xFF])
            
            logger.debug(f"Sending packet: {[hex(x) for x in packet]}")
            
            # Send the command byte by byte
            for byte in packet:
                self.bus.write_byte(self.address, byte)
                time.sleep(0.001)  # Small delay between bytes
                
            return True
            
        except Exception as e:
            logger.error(f"Error sending packet: {str(e)}")
            return False

    def _read_response(self, expected_length):
        """Read response from the sensor."""
        try:
            # Initial delay before reading
            time.sleep(0.1)
            
            # Wait for ready state
            if not self._wait_for_ready():
                return None
            
            response = []
            for _ in range(expected_length):
                try:
                    byte = self.bus.read_byte(self.address)
                    response.append(byte)
                    time.sleep(0.001)  # Small delay between bytes
                except IOError:
                    break
                    
            logger.debug(f"Read response: {[hex(x) for x in response]}")
            return response
            
        except Exception as e:
            logger.error(f"Error reading response: {str(e)}")
            return None

    def is_connected(self):
        """Test if the sensor is properly connected."""
        try:
            logger.debug("Testing connection...")
            if self._send_packet(self.CMD_PREFIX_CODE, self.CMD_TEST_CONNECTION):
                response = self._read_response(12)
                if response is not None and len(response) >= 12:
                    # Check for valid response prefix (55 AA)
                    if response[0] == 0x55 and response[1] == 0xAA:
                        return True
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def control_led(self, mode: LEDMode, color: LEDColor, blink_count=0):
        """Control the LED ring."""
        try:
            logger.debug(f"Setting LED mode={mode.name}, color={color.name}, blink_count={blink_count}")
            if isinstance(mode, LEDMode):
                mode = mode.value
            if isinstance(color, LEDColor):
                color = color.value
                
            # Adjust payload based on different module versions
            if self._fingerprint_capacity == 80:
                payload = [mode, color, color, blink_count]
            else:
                # Handle different LED control format for other versions
                if mode == 1:  # BREATHING
                    mode = 2
                elif mode == 2:  # FAST_BLINK
                    mode = 4
                elif mode == 3:  # KEEPS_ON
                    mode = 1
                elif mode == 4:  # NORMAL_CLOSE
                    mode = 0
                elif mode == 5:  # FADE_IN
                    mode = 3
                    
                if color == LEDColor.GREEN.value:
                    color_value = 0x84
                elif color == LEDColor.RED.value:
                    color_value = 0x82
                elif color == LEDColor.YELLOW.value:
                    color_value = 0x86
                elif color == LEDColor.BLUE.value:
                    color_value = 0x81
                elif color == LEDColor.CYAN.value:
                    color_value = 0x85
                elif color == LEDColor.MAGENTA.value:
                    color_value = 0x83
                else:
                    color_value = 0x87
                    
                payload = [mode, color_value, color_value, blink_count]
                
            if self._send_packet(self.CMD_PREFIX_CODE, self.CMD_SLED_CTRL, payload):
                response = self._read_response(12)
                if response and len(response) >= 12:
                    # Check response prefix and status
                    if response[0] == 0x55 and response[1] == 0xAA:
                        return response[8] == 0
            return False
            
        except Exception as e:
            logger.error(f"LED control failed: {str(e)}")
            return False

    def detect_finger(self):
        """Detect if a finger is present on the sensor."""
        try:
            logger.debug("Detecting finger...")
            if self._send_packet(self.CMD_PREFIX_CODE, self.CMD_FINGER_DETECT):
                response = self._read_response(12)
                if response and len(response) >= 12:
                    result = response[8] == 0
                    logger.debug(f"Finger detection result: {result}")
                    return result
            return False
        except Exception as e:
            logger.error(f"Finger detection failed: {str(e)}")
            return False
