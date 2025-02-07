import smbus2
import time
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('ID809')

class DFRobot_ID809:
    # Command packet prefix codes
    CMD_PREFIX_CODE = 0xAA55
    RCM_PREFIX_CODE = 0x55AA
    CMD_DATA_PREFIX_CODE = 0xA55A
    RCM_DATA_PREFIX_CODE = 0x5AA5

    # Command types
    CMD_TYPE = 0xF0
    RCM_TYPE = 0xF0
    DATA_TYPE = 0x0F

    # Commands
    CMD_TEST_CONNECTION = 0x0001
    CMD_SET_PARAM = 0x0002
    CMD_GET_PARAM = 0x0003
    CMD_GET_DEVICE_INFO = 0x0004

    class LEDMode:
        BREATHING = 1
        FAST_BLINK = 2
        KEEPS_ON = 3
        NORMAL_CLOSE = 4
        FADE_IN = 5
        FADE_OUT = 6
        SLOW_BLINK = 7

    class LEDColor:
        GREEN = 1
        RED = 2
        YELLOW = 3
        BLUE = 4
        CYAN = 5
        MAGENTA = 6
        WHITE = 7

    def __init__(self, i2c_bus=1, address=0x1F):
        """Initialize the ID809 fingerprint sensor."""
        self._bus_number = i2c_bus
        self._address = address
        self._bus = None
        self._debug = True
        self._buf = bytearray(32)  # Response buffer

    def begin(self):
        """Initialize the sensor and verify communication."""
        try:
            logger.debug("Initializing I2C bus %d", self._bus_number)
            self._bus = smbus2.SMBus(self._bus_number)
            
            # Try to read device ID first
            logger.debug("Testing connection to device at address 0x%02X", self._address)
            
            # Wait for device to be ready
            time.sleep(0.5)
            
            # Test connection with multiple retries
            for attempt in range(3):
                try:
                    if self.is_connected():
                        logger.info("Successfully connected to device")
                        return True
                except Exception as e:
                    logger.debug(f"Connection attempt {attempt + 1} failed: {e}")
                    time.sleep(0.1)
            
            logger.error("Failed to establish connection after 3 attempts")
            return False
            
        except Exception as e:
            logger.error("Error during initialization: %s", str(e))
            return False

    def is_connected(self):
        """Test if the device is responding."""
        try:
            # Send test connection command
            header = self._pack(self.CMD_TYPE, self.CMD_TEST_CONNECTION, None, 0)
            logger.debug("Sending test connection packet")
            self._send_packet(header)
            
            # Wait for device to process
            time.sleep(0.05)
            
            # Read response
            response = self._response_payload()
            logger.debug("Test connection response: %d", response)
            
            return response == 0
            
        except Exception as e:
            logger.error("Connection test failed: %s", str(e))
            return False

    def _send_packet(self, data):
        """Send packet over I2C with debug logging."""
        try:
            if self._debug:
                logger.debug("Sending packet: %s", ' '.join(f'{x:02X}' for x in data))
                
            # First check if device is ready
            retries = 3
            while retries > 0:
                try:
                    self._bus.read_byte(self._address)
                    break
                except:
                    retries -= 1
                    time.sleep(0.01)
                    
            if retries == 0:
                raise Exception("Device not responding")

            # Write data in chunks
            chunk_size = 16  # Smaller chunks for better reliability
            for i in range(0, len(data), chunk_size):
                chunk = data[i:min(i+chunk_size, len(data))]
                self._bus.write_i2c_block_data(self._address, chunk[0], chunk[1:])
                time.sleep(0.001)  # Small delay between chunks

        except Exception as e:
            logger.error("Error sending packet: %s", str(e))
            raise

    def _response_payload(self):
        """Read and process response with debug logging."""
        try:
            # Read header first (12 bytes)
            resp = []
            
            # Read in smaller chunks
            for i in range(0, 12, 4):
                chunk = self._bus.read_i2c_block_data(self._address, 0, 4)
                resp.extend(chunk)
                time.sleep(0.001)

            if self._debug:
                logger.debug("Response header: %s", ' '.join(f'{x:02X}' for x in resp))

            # Verify header
            if resp[0] != 0x55 or resp[1] != 0xAA:
                logger.error("Invalid response header")
                return 0xFF

            length = (resp[6] << 8) | resp[7]
            ret = (resp[8] << 8) | resp[9]

            if ret != 0:
                logger.error("Command returned error: %d", ret)
                return 0xFF

            # Read payload if present
            if length > 0:
                payload = self._bus.read_i2c_block_data(self._address, 0, length)
                if self._debug:
                    logger.debug("Response payload: %s", ' '.join(f'{x:02X}' for x in payload))
                self._buf = bytearray(payload)

            return 0

        except Exception as e:
            logger.error("Error reading response: %s", str(e))
            return 0xFF

    def _pack(self, cmd_type, cmd, payload, length):
        """Pack command data with debug logging."""
        try:
            header = []
            
            # Add prefix
            if cmd_type == self.CMD_TYPE:
                header.extend([self.CMD_PREFIX_CODE >> 8, self.CMD_PREFIX_CODE & 0xFF])
            else:
                header.extend([self.CMD_DATA_PREFIX_CODE >> 8, self.CMD_DATA_PREFIX_CODE & 0xFF])

            # Add command structure
            header.extend([0, 0])  # SID, DID
            header.extend([cmd >> 8, cmd & 0xFF])
            header.extend([length >> 8, length & 0xFF])

            if payload:
                if isinstance(payload, (list, bytearray)):
                    header.extend(payload)
                else:
                    header.extend([ord(c) for c in payload])

            # Calculate checksum
            cks = 0xFF
            for i in range(2, len(header)):
                cks += header[i]
            header.extend([cks & 0xFF, (cks >> 8) & 0xFF])

            if self._debug:
                logger.debug("Packed command: %s", ' '.join(f'{x:02X}' for x in header))

            return header

        except Exception as e:
            logger.error("Error packing command: %s", str(e))
            raise
