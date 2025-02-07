cmake_minimum_required(VERSION 3.0)
project(DFRobot_ID809_RPi)

set(CMAKE_CXX_STANDARD 11)

# If you are using wiringPi, you might need to find or link it
# find_library(WIRINGPI_LIB wiringPi)

add_executable(example
    example.cpp
    DFRobot_ID809_I2C.cpp
)

# Link wiringPi if needed:
# target_link_libraries(example ${WIRINGPI_LIB})

# Or with direct I2C calls, you typically don't need special libs, 
# but you do need to link against the standard C library, which is default on Linux.
