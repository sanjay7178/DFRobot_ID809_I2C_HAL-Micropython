/*
   DFRobot_ID809_I2C.cpp
   Adapted for Raspberry Pi from the original Arduino-based DFRobot_ID809_I2C library
   https://github.com/DFRobot/DFRobot_ID809_I2C
*/

#include "DFRobot_ID809_I2C.h"

// If you want to use wiringPi, include these:
#include <wiringPi.h>
#include <wiringPiI2C.h>

// Alternatively, if you prefer direct Linux I2C calls:
#include <unistd.h>      // For usleep()
#include <fcntl.h>       // For open()
#include <sys/ioctl.h>   // For ioctl()
#include <linux/i2c-dev.h> // For I2C_SLAVE

#include <iostream>
#include <chrono>
#include <thread>

DFRobot_ID809_I2C::DFRobot_ID809_I2C(uint8_t i2cAddr)
  : _address(i2cAddr),
    _i2cFd(-1)
{
}

DFRobot_ID809_I2C::~DFRobot_ID809_I2C()
{
    // Close the device file if it was opened
    if(_i2cFd >= 0){
        close(_i2cFd);
    }
}

bool DFRobot_ID809_I2C::begin()
{
    // Example approach with direct Linux I2C calls:
    const char *i2cPath = "/dev/i2c-1";
    _i2cFd = open(i2cPath, O_RDWR);
    if(_i2cFd < 0){
        std::cerr << "Failed to open I2C bus at " << i2cPath << std::endl;
        return false;
    }

    if(ioctl(_i2cFd, I2C_SLAVE, _address) < 0){
        std::cerr << "Failed to set I2C address to 0x" 
                  << std::hex << (int)_address << std::endl;
        return false;
    }

    // Alternatively, if using wiringPi:
    // _i2cFd = wiringPiI2CSetup(_address);
    // if(_i2cFd < 0) {
    //     std::cerr << "Failed to initialize I2C with address 0x"
    //               << std::hex << (int)_address << std::endl;
    //     return false;
    // }

    // You could add device-specific init commands here
    return true;
}

bool DFRobot_ID809_I2C::setSecurityLevel(uint8_t level)
{
    // Example of sending a command to the sensor
    // The actual command bytes depend on the ID809 datasheet
    // Below is a placeholder approach
    uint8_t cmd[3] = { 0x01, 0x0A, level };
    return i2cWriteBytes(cmd, sizeof(cmd));
}

bool DFRobot_ID809_I2C::readDeviceStatus(uint8_t &status)
{
    // Example of reading a status byte from the sensor
    // The exact read command depends on the ID809 datasheet
    // For demonstration:
    uint8_t cmd[1] = { 0x00 };  // Possibly a 'read status' command
    if(!i2cWriteBytes(cmd, 1)){
        return false;
    }

    uint8_t resp[1] = {0};
    if(!i2cReadBytes(resp, 1)){
        return false;
    }

    status = resp[0];
    return true;
}

bool DFRobot_ID809_I2C::captureFingerprint()
{
    // Placeholder for capturing a fingerprint
    // All logic depends on the actual ID809 protocol
    uint8_t cmd[2] = { 0x02, 0x01 };
    return i2cWriteBytes(cmd, sizeof(cmd));
}

bool DFRobot_ID809_I2C::matchFingerprint(uint16_t &userID)
{
    // Placeholder for matching a fingerprint
    // Typically you'd send a command and read back user ID if matched
    uint8_t cmd[2] = { 0x03, 0x01 };
    if(!i2cWriteBytes(cmd, sizeof(cmd))){
        return false;
    }

    uint8_t resp[2] = {0};
    if(!i2cReadBytes(resp, 2)){
        return false;
    }
    // Example: the sensor returns an ID in these 2 bytes
    userID = (resp[0] << 8) | resp[1];
    return true;
}

bool DFRobot_ID809_I2C::i2cWriteBytes(const uint8_t *data, size_t len)
{
    if(_i2cFd < 0) return false;

    // For direct Linux I2C:
    ssize_t bytesWritten = write(_i2cFd, data, len);
    if(bytesWritten < 0 || (size_t)bytesWritten != len){
        std::cerr << "I2C write error\n";
        return false;
    }

    // If using wiringPiI2C you would do repeated calls to wiringPiI2CWriteReg8 or similar
    return true;
}

bool DFRobot_ID809_I2C::i2cReadBytes(uint8_t *data, size_t len)
{
    if(_i2cFd < 0) return false;

    // For direct Linux I2C:
    ssize_t bytesRead = read(_i2cFd, data, len);
    if(bytesRead < 0 || (size_t)bytesRead != len){
        std::cerr << "I2C read error\n";
        return false;
    }

    return true;
}

void DFRobot_ID809_I2C::delayMs(unsigned int ms)
{
    // Simple cross-platform approach using chrono
    std::this_thread::sleep_for(std::chrono::milliseconds(ms));
}
