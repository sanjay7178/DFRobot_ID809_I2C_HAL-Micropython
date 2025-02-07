/*
   DFRobot_ID809_I2C.h
   Adapted for Raspberry Pi from the original Arduino-based DFRobot_ID809_I2C library
   https://github.com/DFRobot/DFRobot_ID809_I2C

   Make sure to review any relevant license terms in the original repository.
*/

#ifndef DFROBOT_ID809_I2C_H
#define DFROBOT_ID809_I2C_H

#include <stdint.h>
#include <string.h>
#include <stdio.h>

class DFRobot_ID809_I2C
{
public:
    DFRobot_ID809_I2C(uint8_t i2cAddr = 0x1F);
    ~DFRobot_ID809_I2C();

    // Initialize the sensor on Raspberry Pi via the specified I2C address
    bool begin();

    // Example function from the original library’s feature set
    // Adjust or expand according to the command set used by the ID809 device
    bool setSecurityLevel(uint8_t level);
    bool readDeviceStatus(uint8_t &status);
    bool captureFingerprint();
    bool matchFingerprint(uint16_t &userID);

private:
    // Low-level I2C read/write
    bool i2cWriteBytes(const uint8_t *data, size_t len);
    bool i2cReadBytes(uint8_t *data, size_t len);

    // Delay helper for Raspberry Pi (milliseconds)
    void delayMs(unsigned int ms);

    // The I2C address for the ID809 fingerprint sensor
    uint8_t _address;
    // File descriptor for I2C device (from wiringPiI2CSetup or similar)
    int     _i2cFd;
};

#endif
