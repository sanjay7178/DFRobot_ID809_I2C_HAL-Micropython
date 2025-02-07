#!/usr/bin/env python3

from id809 import DFRobot_ID809
import time
import signal
import sys
import RPi.GPIO as GPIO

# Global flag for handling Ctrl+C
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print('\nGracefully shutting down...')
    running = False
    
class FingerprintExample:
    def __init__(self):
        """Initialize the fingerprint sensor"""
        self.fp = DFRobot_ID809()
        self.next_id = 1  # Track the next available ID
        
    def initialize(self):
        """Initialize the sensor and verify connection"""
        try:
            if not self.fp.begin():
                print("Failed to initialize sensor! Please check your connection.")
                return False
                
            print("Fingerprint sensor initialized successfully!")
            return True
        except Exception as e:
            print(f"Error initializing sensor: {e}")
            return False
            
    def register_fingerprint(self):
        """Register a new fingerprint"""
        try:
            print("\n=== Fingerprint Registration ===")
            
            # Set LED to breathing blue
            self.fp.ctrl_led(self.fp.LEDMode.BREATHING, self.fp.LEDColor.BLUE)
            
            # Try to collect fingerprint 3 times
            samples_collected = 0
            while samples_collected < 3:
                print(f"\nCollecting sample {samples_collected + 1}/3")
                print("Please place your finger on the sensor...")
                
                if self.fp.collection_fingerprint(timeout=10) == 0:
                    print("Sample captured successfully!")
                    # Blink yellow to indicate success
                    self.fp.ctrl_led(self.fp.LEDMode.FAST_BLINK, self.fp.LEDColor.YELLOW, 3)
                    samples_collected += 1
                else:
                    print("Failed to capture sample! Please try again.")
                    self.fp.ctrl_led(self.fp.LEDMode.FAST_BLINK, self.fp.LEDColor.RED, 2)
                    continue
                    
                print("Please lift your finger")
                while self.fp.detect_finger():
                    time.sleep(0.1)
                
                time.sleep(1)
            
            # Store the fingerprint
            print("\nProcessing and storing fingerprint...")
            if self.fp.store_fingerprint(self.next_id) == 0:
                print(f"Fingerprint stored successfully with ID: {self.next_id}")
                self.fp.ctrl_led(self.fp.LEDMode.KEEPS_ON, self.fp.LEDColor.GREEN, 0)
                self.next_id += 1
                time.sleep(2)
            else:
                print("Failed to store fingerprint!")
                self.fp.ctrl_led(self.fp.LEDMode.KEEPS_ON, self.fp.LEDColor.RED, 0)
                time.sleep(2)
                
        except Exception as e:
            print(f"Error during registration: {e}")
        finally:
            self.fp.ctrl_led(self.fp.LEDMode.NORMAL_CLOSE, self.fp.LEDColor.BLUE, 0)
            
    def match_fingerprint(self):
        """Match a fingerprint against stored templates"""
        try:
            print("\n=== Fingerprint Matching ===")
            print("Place your finger on the sensor...")
            
            self.fp.ctrl_led(self.fp.LEDMode.BREATHING, self.fp.LEDColor.BLUE)
            
            if self.fp.collection_fingerprint(timeout=10) == 0:
                print("Fingerprint captured, searching database...")
                
                match_id = self.fp.search()
                if match_id > 0:
                    print(f"Match found! Fingerprint ID: {match_id}")
                    self.fp.ctrl_led(self.fp.LEDMode.KEEPS_ON, self.fp.LEDColor.GREEN, 0)
                else:
                    print("No matching fingerprint found.")
                    self.fp.ctrl_led(self.fp.LEDMode.KEEPS_ON, self.fp.LEDColor.RED, 0)
            else:
                print("Failed to capture fingerprint!")
                self.fp.ctrl_led(self.fp.LEDMode.KEEPS_ON, self.fp.LEDColor.RED, 0)
                
            print("\nPlease lift your finger")
            while self.fp.detect_finger():
                time.sleep(0.1)
                
            time.sleep(2)
            
        except Exception as e:
            print(f"Error during matching: {e}")
        finally:
            self.fp.ctrl_led(self.fp.LEDMode.NORMAL_CLOSE, self.fp.LEDColor.BLUE, 0)
            
    def delete_fingerprint(self):
        """Delete a stored fingerprint"""
        try:
            print("\n=== Delete Fingerprint ===")
            id_to_delete = input("Enter fingerprint ID to delete (or 'all' to delete all): ")
            
            if id_to_delete.lower() == 'all':
                if self.fp.del_fingerprint(0xFF) == 0:  # 0xFF is DELALL
                    print("All fingerprints deleted successfully!")
                    self.next_id = 1
                else:
                    print("Failed to delete fingerprints!")
            else:
                try:
                    id_num = int(id_to_delete)
                    if self.fp.del_fingerprint(id_num) == 0:
                        print(f"Fingerprint ID {id_num} deleted successfully!")
                        if id_num == self.next_id - 1:
                            self.next_id = id_num
                    else:
                        print(f"Failed to delete fingerprint ID {id_num}!")
                except ValueError:
                    print("Invalid ID number!")
                    
        except Exception as e:
            print(f"Error during deletion: {e}")
            
    def run(self):
        """Main program loop"""
        if not self.initialize():
            return
            
        global running
        while running:
            print("\n=== Fingerprint Sensor Menu ===")
            print("1. Register new fingerprint")
            print("2. Match fingerprint")
            print("3. Delete fingerprint")
            print("4. Exit")
            print("=============================")
            
            choice = input("Select an option (1-4): ")
            
            if choice == '1':
                self.register_fingerprint()
            elif choice == '2':
                self.match_fingerprint()
            elif choice == '3':
                self.delete_fingerprint()
            elif choice == '4':
                print("\nExiting program...")
                self.fp.ctrl_led(self.fp.LEDMode.NORMAL_CLOSE, self.fp.LEDColor.BLUE, 0)
                break
            else:
                print("\nInvalid option! Please try again.")
                
def main():
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and run the fingerprint example
    example = FingerprintExample()
    example.run()
    
if __name__ == "__main__":
    main()
