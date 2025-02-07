import smbus2
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('ID809')

class DFRobot_ID809:
    def __init__(self, i2c_bus=1, address=0x1F):
        self._bus_number = i2c_bus
        self._address = address
        self._bus = None
        self._buf = bytearray(32)

    def begin(self):
        """Initialize with improved device detection"""
        try:
            logger.debug("Opening I2C bus %d", self._bus_number)
            self._bus = smbus2.SMBus(self._bus_number)
            
            # Initial delay
            time.sleep(1.0)
            
            # Try to detect device
            if not self._detect_device():
                logger.error("Device not detected at address 0x%02X", self._address)
                return False
                
            # Reset device communication
            if not self._reset_communication():
                logger.error("Failed to reset device communication")
                return False
                
            # Test connection
            if not self._test_connection():
                logger.error("Connection test failed")
                return False
                
            logger.info("Device initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Initialization error: %s", str(e))
            return False

    def _detect_device(self):
        """Check if device responds to I2C address"""
        try:
            # Try to read a byte from the device
            for _ in range(3):
                try:
                    self._bus.read_byte(self._address)
                    logger.debug("Device detected at address 0x%02X", self._address)
                    return True
                except:
                    time.sleep(0.1)
            return False
        except:
            return False

    def _reset_communication(self):
        """Reset the device communication state"""
        try:
            # Send a sequence of bytes to reset device state
            reset_sequence = [0x00, 0xFF, 0xFF, 0xFF]
            for byte in reset_sequence:
                try:
                    self._bus.write_byte(self._address, byte)
                    time.sleep(0.01)
                except:
                    pass
            
            # Clear any pending responses
            for _ in range(5):
                try:
                    self._bus.read_byte(self._address)
                    time.sleep(0.01)
                except:
                    break
                    
            return True
        except:
            return False

    def _test_connection(self):
        """Test basic communication with device"""
        try:
            # Simple test sequence
            test_data = [0xAA, 0x55, 0x00, 0x01]
            
            # Write test data
            self._bus.write_i2c_block_data(self._address, test_data[0], test_data[1:])
            time.sleep(0.05)
            
            # Try to read response
            try:
                resp = self._bus.read_byte(self._address)
                logger.debug("Test response: 0x%02X", resp)
                return True
            except:
                return False
                
        except Exception as e:
            logger.error("Connection test error: %s", str(e))
            return False

    def is_connected(self):
        """Check if device is responding"""
        return self._test_connection()
