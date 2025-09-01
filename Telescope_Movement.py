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

# Time interval for updating celestial coordinates
PING_RA_DEC = config.get('celestial_ping_time')

# Global variable for telescope connection to CoppeliaSim
clientID = None

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
    try:
        # Get handles for base and mount joints
        baseJointHandle = sim.simxGetObjectHandle(clientID, 'Base_joint', sim.simx_opmode_blocking)[1]
        mountJointHandle = sim.simxGetObjectHandle(clientID, 'Mount_joint', sim.simx_opmode_blocking)[1]
        # Start simulation and move joints to rest position (0 degrees)
        sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, baseJointHandle, 0.0, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, mountJointHandle, 0.0, sim.simx_opmode_oneshot)
        time.sleep(3)
        # Stop simulation and disconnect
        sim.simxStopSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxFinish(clientID)
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
        # Get handles for base and mount joints
        baseJointHandle = sim.simxGetObjectHandle(clientID, 'Base_joint', sim.simx_opmode_blocking)[1]
        mountJointHandle = sim.simxGetObjectHandle(clientID, 'Mount_joint', sim.simx_opmode_blocking)[1]
        # Start simulation and move joints to target positions (converted to radians)
        sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, baseJointHandle, math.radians(az), sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, mountJointHandle, math.radians(alt), sim.simx_opmode_oneshot)
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
                if keyboard.is_pressed('q') or keyboard.is_pressed('Q'):
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