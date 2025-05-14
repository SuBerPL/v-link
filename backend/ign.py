import threading
import time
import os
import lgpio
from .shared.shared_state import shared_state

class IGNThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.IGNITION_PIN = 1
        self.chip = lgpio.gpiochip_open(0)  # Open GPIO chip

        self._stop_event = threading.Event()
        self.daemon = True

    def run(self):
        # Initialize GPIO pin here after the thread starts
        try:
            # Free GPIO pin if it's already claimed
            try:
                lgpio.gpio_free(self.chip, self.IGNITION_PIN)
            except lgpio.error:
                print(f"GPIO {self.IGNITION_PIN} ready.")
            
            # Now claim the GPIO pin
            lgpio.gpio_claim_input(self.chip, self.IGNITION_PIN)
            
            # Monitor ignition pin
            self.monitor_ignition()
        except lgpio.error as e:
            print(f"Error during GPIO initialization: {e}")

    def stop_thread(self):
        print("Stopping IGN thread.")
        self._stop_event.set()
        # Free GPIO pin when stopping
        try:
            lgpio.gpio_free(self.chip, self.IGNITION_PIN)
        except lgpio.error as e:
            print(f"Error freeing GPIO {self.IGNITION_PIN}: {e}")
        lgpio.gpiochip_close(self.chip)  # Close GPIO chip

    def monitor_ignition(self):
        previous_state = None  # Variable to track the previous state of the ignition pin
        
        while not self._stop_event.is_set():
            try:
                # Read GPIO pin value (LOW = Ignition OFF)
                current_state = lgpio.gpio_read(self.chip, self.IGNITION_PIN)
                
                # Check if the state has changed
                if current_state != previous_state:
                    if current_state == 0: # Pin is raised high when Ignition is turned off.
                        shared_state.ign_state.clear()  # Ignition is OFF, so clear the state
                    else:
                        shared_state.ign_state.set()  # Ignition is ON, so set the state                    
                    # Update previous state for the next iteration
                    previous_state = current_state

            except lgpio.error as e:
                print(f"Error reading GPIO {self.IGNITION_PIN}: {e}")
                time.sleep(1)  # Avoid tight looping if there's a problem
                continue

            time.sleep(1)  # Avoid high CPU usage

