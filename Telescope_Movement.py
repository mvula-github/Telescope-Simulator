import time
import math
import keyboard
import Calculations as C
import File_Handling as FH
from System_Config import config
import sim

# Load telescope movement limits from configuration
ALTITUDE_LIMITS = config.get('altitude_limits')
AZIMUTH_LIMITS = config.get('azimuth_limits')
if ALTITUDE_LIMITS is None or AZIMUTH_LIMITS is None:
    # Fallback to safe defaults
    ALTITUDE_LIMITS = [-90.0, 90.0]
    AZIMUTH_LIMITS = [-180.0, 180.0]

# Time interval for updating celestial coordinates
PING_RA_DEC = config.get('celestial_ping_time')

# Global variable for telescope connection to CoppeliaSim
clientID = None

def _clamp(value, lower, upper):
    return max(lower, min(upper, value))

def _normalize_azimuth_deg(az):
    # Normalize to range [-180, 180]
    return ((az + 180.0) % 360.0) - 180.0

def test_con():
    """
    Test and (re)establish connection to CoppeliaSim telescope.
    Returns True if connected, False otherwise.
    """
    global clientID
    try:
        # Check if connection is not established or lost
        if clientID is None or sim.simxGetConnectionId(clientID) == -1:
            print("Connecting to telescope.")
            sim.simxFinish(-1)  # Close all opened connections
            # Attempt to connect to CoppeliaSim remote API server
            clientID = sim.simxStart('127.0.0.1', 19999, True, True, 5000, 5)
            if clientID != -1:
                return True
            else:
                print("Failed to connect to telescope.")
                FH.write_log("admin", "Telescope Connection", False, "Failed to connect to telescope.")
                return False
        return True
    except Exception as e:
        FH.write_log("admin", "Telescope Connection", False, f"Connection error: {e}")
        return False

def telescope_rest():
    """
    Move the telescope to its rest (default) position.
    """
    global clientID
    try:
        # Ensure connection is established
        if not test_con():
            print("Cannot enter rest mode: telescope not connected.")
            FH.write_log("admin", "Rest Mode", False, "Failed to enter rest mode: not connected")
            return
        # Get handles for base and mount joints
        ret_b, baseJointHandle = sim.simxGetObjectHandle(clientID, 'Base_joint', sim.simx_opmode_blocking)
        ret_m, mountJointHandle = sim.simxGetObjectHandle(clientID, 'Mount_joint', sim.simx_opmode_blocking)
        if ret_b != 0 or ret_m != 0:
            raise RuntimeError("Failed to get joint handles for rest mode")
        # Start simulation and move joints to rest position (0 degrees)
        sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, baseJointHandle, 0.0, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, mountJointHandle, 0.0, sim.simx_opmode_oneshot)
        time.sleep(3)
        # Stop simulation and disconnect
        sim.simxStopSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxFinish(clientID)
        clientID = None
        print("Rest mode entered.")
        FH.write_log("admin", "Rest Mode", True, "Telescope entered rest mode.")
    except Exception as e:
        FH.write_log("admin", "Rest Mode", False, f"Failed to enter rest mode: {e}")
        print(f"Error entering rest mode: {e}")

def move_tel(alt, az):
    """
    Move the telescope to the specified altitude and azimuth.
    """
    try:
        # Validate within configured limits
        if not check_limits(alt, az):
            raise ValueError(f"Requested Alt/Az out of limits: Alt={alt}, Az={az}")
        # Ensure connection
        if not test_con():
            raise RuntimeError("Telescope not connected")
        # Get handles for base and mount joints
        ret_b, baseJointHandle = sim.simxGetObjectHandle(clientID, 'Base_joint', sim.simx_opmode_blocking)
        ret_m, mountJointHandle = sim.simxGetObjectHandle(clientID, 'Mount_joint', sim.simx_opmode_blocking)
        if ret_b != 0 or ret_m != 0:
            raise RuntimeError("Failed to get joint handles for movement")
        # Start simulation and move joints to target positions (converted to radians)
        sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)
        # Normalize azimuth for base joint and clamp altitude
        normalized_az = _normalize_azimuth_deg(az)
        clamped_alt = _clamp(alt, ALTITUDE_LIMITS[0], ALTITUDE_LIMITS[1])
        sim.simxSetJointTargetPosition(clientID, baseJointHandle, math.radians(normalized_az), sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, mountJointHandle, math.radians(clamped_alt), sim.simx_opmode_oneshot)
        time.sleep(3)
        FH.write_log("admin", "Telescope Movement", True, f"Moved telescope to Alt: {alt}, Az: {az}")
    except Exception as e:
        FH.write_log("admin", "Telescope Movement", False, f"Failed to move telescope to Alt: {alt}, Az: {az} -> Error: {e}")
        print(f"Error moving telescope: {e}")

def check_limits(alt, az):
    """
    Check if the given altitude and azimuth are within the telescope's movement limits.
    """
    # Return True if both altitude and azimuth are within configured limits
    return ALTITUDE_LIMITS[0] <= alt <= ALTITUDE_LIMITS[1] and AZIMUTH_LIMITS[0] <= az <= AZIMUTH_LIMITS[1]

def track_celestial_object(code):
    """
    Continuously track a celestial object by code, updating telescope position.
    Press 'q' to stop tracking.
    """
    try:
        while True:
            start_time = time.time()
            # Wait for the configured ping interval or until 'q' is pressed
            while time.time() - start_time < PING_RA_DEC:
                try:
                    stop_pressed = keyboard.is_pressed('q') or keyboard.is_pressed('Q')
                except Exception:
                    stop_pressed = False
                if stop_pressed:
                    print("Stopping tracking...")
                    telescope_rest()
                    FH.write_log("admin", "Tracking", True, "Stopped tracking celestial object.")
                    return
                time.sleep(0.1)
            # Get celestial object details and convert to Alt/Az
            code, name, ra, dec = C.get_celestial_object_details(code)
            alt, az = C.convert_radec_to_altaz(ra, dec)
            if check_limits(alt, az):
                print(f"Tracking Celestial Object -> NAME: {name}, CODE: {code}, RA: {ra:.3f} hours, Dec: {dec:.3f}°")
                print(f"Telescope tracking Alt: {alt:.2f}°, Az: {az:.2f}°\nPress q to stop tracking.\n")
                if test_con():
                    move_tel(alt, az)
                    FH.write_log("admin", "Track Celestial Object", True, f"Started tracking celestial object -> NAME: {name}, CODE: {code}")
                else:
                    FH.write_log("admin", "Telescope Movement", False, f"Failed to move telescope for object {name} (RA: {ra}, Dec: {dec})")
                    break
            else:
                print(f"Target coordinates (RA: {ra:.3f} hours, Dec: {dec:.3f}°) -> Out of bounds!")
                print(f"Coordinates (Alt: {alt:.2f}°, Az: {az:.2f}°) -> Stopping movement.")
                FH.write_log("admin", "Tracking", False, f"Celestial object out of bounds: Alt: {alt}, Az: {az}.")
                if test_con():
                    telescope_rest()
                break
    except KeyboardInterrupt:
        # Handle user interrupt (Ctrl+C)
        FH.write_log("admin", "Tracking", True, "Tracking interrupted by user.")
        if test_con():
            telescope_rest()
        print("Tracking stopped by user.")
    except Exception as e:
        FH.write_log("admin", "Tracking", False, f"Error occurred during tracking: {e}")
        print(f"Error occurred during tracking: {e}")

def main():
    # Start tracking the celestial object with code "M31" (Andromeda Galaxy)
    track_celestial_object("M31")

if __name__ == '__main__':
    main()