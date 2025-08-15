import time
import uinput
from enum import Enum, auto
from .shared.shared_state import shared_state

def current_time_ms():
    return int(time.time() * 1000)

def time_elapsed(start_time):
    return current_time_ms() - start_time
    
class ButtonState(Enum):
    IDLE = auto()
    PRESSED = auto()
    LONG_PRESSED = auto()
    RELEASED = auto()

class JoystickState(Enum):
    IDLE = auto()
    MOVING = auto()

class ButtonHandler:
    def __init__(self, click_timeout, long_press_duration, mouse_speed):
        self.click_timeout = click_timeout
        self.long_press_duration = long_press_duration
        self.mouse_speed = mouse_speed
        self.mouse_mode = False

        self.button_state = ButtonState.IDLE
        self.joystick_state = JoystickState.IDLE
        self.current_button = None
        self.current_joystick_button = None
        self.last_button_at = None
        self.long_press_executed = False
        self.last_joystick_at = 0

        self.input_device = uinput.Device([
            uinput.REL_X,        # Relative X axis (horizontal movement)
            uinput.REL_Y,        # Relative Y axis (vertical movement)
            uinput.BTN_LEFT,     # Mouse left click
            uinput.KEY_BACKSPACE,
            uinput.KEY_N,
            uinput.KEY_V,
            uinput.KEY_H,
            uinput.KEY_SPACE,
            uinput.KEY_UP,
            uinput.KEY_DOWN,
            uinput.KEY_LEFT,
            uinput.KEY_RIGHT,
            uinput.KEY_A,
            uinput.KEY_R
        ])

    def handle(self, button_name):
        self._handle_buttons(button_name)
        self._handle_joystick(button_name)

    def _handle_buttons(self, button_name):
        if not button_name:
            if self.button_state != ButtonState.IDLE:
                self.timeout_button()  # Check if the current button needs to be released
            return

        now = current_time_ms()

        if button_name != self.current_button:
            if self.current_button:
                self._release_button(self.current_button, time_elapsed(self.button_down_at))
            self._press_button(button_name)
            self.current_button = button_name
            self.button_state = ButtonState.PRESSED
            self.button_down_at = now

        self.last_button_at = now

        # Trigger long press action if duration is exceeded and not already triggered
        if self.button_state == ButtonState.PRESSED and time_elapsed(self.button_down_at) > self.long_press_duration:
            self.button_state = ButtonState.LONG_PRESSED
            if not self.long_press_executed:  # Trigger only once
                print("test")
                self._trigger_long_press_action(button_name)
                self.long_press_executed = True

    def _press_button(self, button_name):
        """Press a button and trigger corresponding action."""
        print(f"Button pressed: {button_name}")
        
        match button_name:
            case "BTN_ENTER":
                print('Enter')
                if self.mouse_mode:
                    print('Left mouse click')
                    self.input_device.emit(uinput.BTN_LEFT, 1)
                    self.input_device.emit(uinput.BTN_LEFT, 0)
                else:
                    print('Spacebar')
                    self.input_device.emit_click(uinput.KEY_SPACE, 1)
            case "BTN_BACK":
                print('Back')
                self.input_device.emit_click(uinput.KEY_BACKSPACE, 1)
            case "BTN_NEXT":
                print('Next')
                self.input_device.emit_click(uinput.KEY_N, 1)
            case "BTN_PREV":
                print('Previous')
                self.input_device.emit_click(uinput.KEY_V, 1)
            case "BTN_VOL_UP":
                print('Volume up')
            case "BTN_VOL_DOWN":
                print('Volume down')
            case "BTN_YES":
                print('Accept Call')
                self.input_device.emit_click(uinput.KEY_A, 1)
            case "BTN_NO":
                print('Reject Call')
                self.input_device.emit_click(uinput.KEY_R, 1)
        
    def _trigger_long_press_action(self, button_name):
        """Perform a long press action."""
        print(f"Long press action triggered for {button_name}")
        match button_name:
            case "BTN_ENTER":
                shared_state.rtiStatus = not shared_state.rtiStatus
                shared_state.hdmi_event.set()
                print(f"Toggled RTI status to {shared_state.rtiStatus}")
            case "BTN_PREV":
                self.mouse_mode = not self.mouse_mode
                print(f"Toggled mouse mode to {self.mouse_mode}")

    def _release_button(self, button_name, press_duration):
        """Reset button state and ensure no redundant long-press actions."""
        print(f"Button released: {button_name} after {press_duration}ms")

        if self.long_press_executed:
            print(f"Long press action already handled for {button_name}, skipping.")
            self.long_press_executed = False
        else:
            print(f"Button {button_name} released without long press action.")

        # Reset button state
        self.button_state = ButtonState.IDLE
        self.current_button = None

    def timeout_button(self):
        """Automatically release a button if it exceeds the click timeout."""
        if self.current_button and time_elapsed(self.last_button_at) > self.click_timeout:
            self._release_button(self.current_button, time_elapsed(self.button_down_at))

    def _handle_joystick(self, joystick_name):
        """Handle joystick actions based on the current mode (mouse or keyboard)."""
        now = current_time_ms()

        # If no joystick input, reset state but don't reset the timeout
        if not joystick_name:
            self.joystick_state = JoystickState.IDLE
            self.current_joystick_button = None
            return

        # Mouse mode: Continuous movement
        if self.mouse_mode:
            match joystick_name:
                case "BTN_UP":
                    self._move_mouse(0, -1)
                case "BTN_DOWN":
                    self._move_mouse(0, 1)
                case "BTN_LEFT":
                    self._move_mouse(-1, 0)
                case "BTN_RIGHT":
                    self._move_mouse(1, 0)
            return
        
        # Enforce click timeout for keyboard mode
        if now - self.last_joystick_at < self.click_timeout:
            return

        print(f"Joystick moved: {joystick_name}")
        self.last_joystick_at = now  # Update timestamp to enforce timeout

        # Perform single key press for keyboard mode
        match joystick_name:
            case "BTN_UP":
                self.input_device.emit_click(uinput.KEY_UP, 1)
            case "BTN_DOWN":
                self.input_device.emit_click(uinput.KEY_H, 1)
            case "BTN_LEFT":
                self.input_device.emit_click(uinput.KEY_LEFT, 1)
            case "BTN_RIGHT":
                self.input_device.emit_click(uinput.KEY_RIGHT, 1)

    def _move_mouse(self, dx, dy):
        scaled_dx = int(dx * self.mouse_speed)
        scaled_dy = int(dy * self.mouse_speed)

        self.input_device.emit(uinput.REL_X, scaled_dx)
        self.input_device.emit(uinput.REL_Y, scaled_dy)

        print(f"Moving mouse, dx={scaled_dx}, dy={scaled_dy}, speed={self.mouse_speed}")
