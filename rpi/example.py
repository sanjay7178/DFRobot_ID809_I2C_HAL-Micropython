#!/usr/bin/env python3

from ID809 import ID809
import time

def main():
    # Initialize sensor
    fp = ID809()
    
    if not fp.begin():
        print("Sensor initialization failed")
        return

    while True:
        print("\n1. Enroll Fingerprint")
        print("2. Verify Fingerprint")
        print("3. Exit")
        
        choice = input("Choose option: ")

        if choice == '1':
            # Enrollment
            empty_id = fp.get_empty_id()
            if empty_id == fp.ERR_ID809:
                print("No empty slots available")
                continue

            print(f"Place finger on sensor {3} times")
            for i in range(3):
                fp.ctrl_led(1, 4, 0)  # Blue breathing LED
                print(f"\nScan {i+1}/3")
                
                while fp.collection_fingerprint(10) != 0:
                    print("Failed, try again")
                
                fp.ctrl_led(2, 3, 3)  # Yellow blink
                print("Remove finger")
                while fp.detect_finger():
                    time.sleep(0.1)
                time.sleep(1)

            if fp.store_fingerprint(empty_id) == 0:
                print(f"Stored as ID {empty_id}")
                fp.ctrl_led(3, 1, 0)  # Green solid
            else:
                print("Store failed")
                fp.ctrl_led(3, 2, 0)  # Red solid
            time.sleep(2)

        elif choice == '2':
            # Verification
            print("Place finger to verify")
            fp.ctrl_led(1, 4, 0)  # Blue breathing
            
            if fp.collection_fingerprint(10) == 0:
                match_id = fp.search()
                if match_id:
                    print(f"Match found! ID: {match_id}")
                    fp.ctrl_led(3, 1, 0)  # Green solid
                else:
                    print("No match found")
                    fp.ctrl_led(3, 2, 0)  # Red solid
                time.sleep(2)
            else:
                print("Scan failed")

        elif choice == '3':
            break

if __name__ == '__main__':
    main()
