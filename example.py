from machine import I2C, Pin
import time
from id809 import ID809

# Initialize I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21))  # Adjust pins as needed

# Create sensor instance
fp = ID809(i2c)

# Initialize
if not fp.begin():
    print("Failed to initialize sensor!")
    while True:
        time.sleep(1)

def enroll_finger():
    """Enroll a new fingerprint"""
    # Set LED to breathing blue
    fp.ctrl_led(fp.LED_MODES['BREATHING'], fp.LED_COLORS['BLUE'], 0)
    
    print("Place finger on sensor")
    
    # Collect fingerprint 3 times
    for i in range(3):
        while fp.collection_fingerprint(10) != 0:
            print("Collection failed, try again")
            time.sleep(1)
            
        print(f"Collection {i+1} successful")
        fp.ctrl_led(fp.LED_MODES['FAST_BLINK'], fp.LED_COLORS['YELLOW'], 3)
        
        print("Remove finger")
        while fp.detect_finger():
            time.sleep(0.1)
            
        time.sleep(1)
        
    # Store fingerprint
    fp.ctrl_led(fp.LED_MODES['FAST_BLINK'], fp.LED_COLORS['BLUE'], 3)
    ret = fp.store_fingerprint(1)  # Store as ID 1
    
    if ret == 0:
        print("Enrollment successful!")
        fp.ctrl_led(fp.LED_MODES['KEEPS_ON'], fp.LED_COLORS['GREEN'], 0)
    else:
        print("Enrollment failed!")
        fp.ctrl_led(fp.LED_MODES['KEEPS_ON'], fp.LED_COLORS['RED'], 0)
    
    time.sleep(2)
    fp.ctrl_led(fp.LED_MODES['NORMAL_CLOSE'], fp.LED_COLORS['BLUE'], 0)

def verify_finger():
    """Verify a fingerprint"""
    print("Place finger to verify")
    fp.ctrl_led(fp.LED_MODES['BREATHING'], fp.LED_COLORS['BLUE'], 0)
    
    if fp.collection_fingerprint(10) == 0:
        match_id = fp.search()
        
        if match_id > 0:
            print(f"Match found! ID: {match_id}")
            fp.ctrl_led(fp.LED_MODES['KEEPS_ON'], fp.LED_COLORS['GREEN'], 0)
        else:
            print("No match found")
            fp.ctrl_led(fp.LED_MODES['KEEPS_ON'], fp.LED_COLORS['RED'], 0)
    else:
        print("Failed to capture fingerprint")
        fp.ctrl_led(fp.LED_MODES['KEEPS_ON'], fp.LED_COLORS['RED'], 0)
    
    time.sleep(2)
    fp.ctrl_led(fp.LED_MODES['NORMAL_CLOSE'], fp.LED_COLORS['BLUE'], 0)

# Main loop
while True:
    print("\n1: Enroll fingerprint")
    print("2: Verify fingerprint")
    
    choice = input("Select option (1-2): ")
    
    if choice == '1':
        enroll_finger()
    elif choice == '2':
        verify_finger()
    else:
        print("Invalid choice")
    
    time.sleep(1)
