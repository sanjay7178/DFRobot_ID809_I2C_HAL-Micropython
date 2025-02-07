/*
   example.cpp
   Demonstration of using the adapted DFRobot_ID809_I2C library on Raspberry Pi
*/

#include <iostream>
#include "DFRobot_ID809_I2C.h"

int main()
{
    DFRobot_ID809_I2C fingerprintSensor(0x1F); // Default I2C address, adjust if needed
    if(!fingerprintSensor.begin()){
        std::cerr << "Failed to initialize fingerprint sensor." << std::endl;
        return 1;
    }

    std::cout << "Sensor initialized. Trying some operations..." << std::endl;

    // Example: set security level
    if(!fingerprintSensor.setSecurityLevel(5)){
        std::cerr << "Failed to set security level." << std::endl;
    } else {
        std::cout << "Security level set to 5." << std::endl;
    }

    // Example: read status
    uint8_t status = 0;
    if(fingerprintSensor.readDeviceStatus(status)){
        std::cout << "Sensor status: " << (int)status << std::endl;
    } else {
        std::cerr << "Failed to read status." << std::endl;
    }

    // Example: capture fingerprint
    if(fingerprintSensor.captureFingerprint()){
        std::cout << "Fingerprint capture command sent successfully." << std::endl;
    } else {
        std::cerr << "Failed to capture fingerprint." << std::endl;
    }

    // Example: match fingerprint
    uint16_t userID = 0;
    if(fingerprintSensor.matchFingerprint(userID)){
        std::cout << "Fingerprint matched with user ID: " << userID << std::endl;
    } else {
        std::cerr << "Match operation failed." << std::endl;
    }

    return 0;
}
