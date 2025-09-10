import time
import math
import keyboard
import File_Handling as FH
from System_Config import config
import sim
import Calculations as C
import ctypes as ct  # Import ctypes for joint position retrieval

# Config vars
ALTITUDE_LIMITS = config.get('altitude_limits', [-90, 90])
AZIMUTH_LIMITS = config.get('azimuth_limits', [0, 360])
PING_RA_DEC = config.get('celestial_ping_time', 3)
MOVEMENT_TIMEOUT = 10  # Increased timeout for slower telescope movement
POSITION_TOLERANCE = 0.01  # Tolerance in radians for checking if target is reached

# Global variable for telescope connection
clientID = None

def test_con() -> bool:
    """
    Test and (re)establish connection to CoppeliaSim telescope.
    Returns True if connected, False otherwise.
    """
    global clientID
    try:
        if clientID is None or sim.simxGetConnectionId(clientID) == -1:
            print("Connecting to telescope.")
            sim.simxFinish(-1)  # Close all opened connections
            clientID = sim.simxStart('127.0.0.1', 19999, True, True, 5000, 5)
            if clientID != -1:
                print("Connected to telescope.")
                return True
            else:
                print("Failed to connect to telescope.")
                FH.write_log("system", "Telescope Connection", "error", "Failed to connect to telescope.")
                return False
        return True
    except Exception as e:
        FH.write_log("system", "Telescope Connection", "error", f"Connection error: {e}")
        print(f"Connection error: {e}")
        return False

def check_limits(alt: float, az: float) -> bool:
    """
    Check if the given altitude and azimuth are within the telescope's movement limits.
    """
    return ALTITUDE_LIMITS[0] <= alt <= ALTITUDE_LIMITS[1] and AZIMUTH_LIMITS[0] <= az <= AZIMUTH_LIMITS[1]

def get_current_joint_position(joint_handle: int) -> float:
    """
    Get the current position of a joint in radians using direct ctypes call.
    """
    position = ct.c_float()
    # Access the raw ctypes function from sim.py
    c_GetJointPosition = sim.c_GetJointPosition
    # Initialize streaming mode
    ret = c_GetJointPosition(clientID, joint_handle, ct.byref(position), sim.simx_opmode_streaming)
    if ret == sim.simx_return_ok or ret == sim.simx_return_novalue_flag:
        time.sleep(0.05)  # Wait for streaming to initialize
        # Retrieve position with buffer mode
        ret = c_GetJointPosition(clientID, joint_handle, ct.byref(position), sim.simx_opmode_buffer)
        if ret == sim.simx_return_ok:
            return position.value
        else:
            raise RuntimeError(f"Failed to get joint position: {ret}")
    else:
        raise RuntimeError(f"Failed to initialize joint position streaming: {ret}")

def wait_for_joint_position(joint_handle: int, target_position: float) -> bool:
    """
    Wait until the joint reaches the target position within tolerance or timeout.
    Returns True if target reached, False if timeout.
    """
    start_time = time.time()
    while time.time() - start_time < MOVEMENT_TIMEOUT:
        current_position = get_current_joint_position(joint_handle)
        if abs(current_position - target_position) < POSITION_TOLERANCE:
            return True
        time.sleep(0.1)
    return False

def move_tel(alt: float, az: float):
    """
    Move the telescope to the specified altitude and azimuth without accumulation.
    """
    if not check_limits(alt, az):
        raise ValueError(f"Out of limits: Alt={alt} (limits={ALTITUDE_LIMITS}), Az={az} (limits={AZIMUTH_LIMITS})")
    try:
        if not test_con():
            raise RuntimeError("Connection failed")
        
        # Get joint handles
        baseJointHandle = sim.simxGetObjectHandle(clientID, 'Base_joint', sim.simx_opmode_blocking)[1]
        mountJointHandle = sim.simxGetObjectHandle(clientID, 'Mount_joint', sim.simx_opmode_blocking)[1]

        # Convert to radians
        alt_rad = math.radians(alt)
        az_rad = math.radians(az)

        # Ensure clockwise motion for azimuth by calculating shortest path
        current_az = get_current_joint_position(baseJointHandle)
        az_diff = (az_rad - current_az) % (2 * math.pi)
        if az_diff > math.pi:
            az_diff -= 2 * math.pi  # Prefer clockwise rotation
        target_az = current_az + az_diff

        # Start simulation if not already running
        sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)

        # Set target positions
        sim.simxSetJointTargetPosition(clientID, baseJointHandle, target_az, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, mountJointHandle, alt_rad, sim.simx_opmode_oneshot)

        # Wait for joints to reach target positions
        base_reached = wait_for_joint_position(baseJointHandle, target_az)
        mount_reached = wait_for_joint_position(mountJointHandle, alt_rad)

        if base_reached and mount_reached:
            FH.write_log("system", "Telescope Movement", "success", f"Moved telescope to Alt: {alt}, Az: {az}")
            print("Telescope moved successfully.")
        else:
            FH.write_log("system", "Telescope Movement", "warning", f"Timeout moving telescope to Alt: {alt}, Az: {az}")
            print("Warning: Telescope movement timed out.")
    except Exception as e:
        FH.write_log("system", "Telescope Movement", "error", f"Failed to move telescope to Alt: {alt}, Az: {az} -> Error: {e}")
        print(f"Error moving telescope: {e}")
        raise

def telescope_rest():
    """
    Move the telescope to its rest (default) position (Alt=90, Az=0 - straight up).
    """
    global clientID  # Declared at the start
    try:
        if not test_con():
            raise RuntimeError("Connection failed")
        
        baseJointHandle = sim.simxGetObjectHandle(clientID, 'Base_joint', sim.simx_opmode_blocking)[1]
        mountJointHandle = sim.simxGetObjectHandle(clientID, 'Mount_joint', sim.simx_opmode_blocking)[1]
        
        # Convert to radians
        alt_rad = math.radians(90)
        az_rad = math.radians(0)

        # Ensure clockwise motion for azimuth
        current_az = get_current_joint_position(baseJointHandle)
        az_diff = (az_rad - current_az) % (2 * math.pi)
        if az_diff > math.pi:
            az_diff -= 2 * math.pi
        target_az = current_az + az_diff

        sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, baseJointHandle, target_az, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, mountJointHandle, alt_rad, sim.simx_opmode_oneshot)

        # Wait for joints to reach target positions
        base_reached = wait_for_joint_position(baseJointHandle, target_az)
        mount_reached = wait_for_joint_position(mountJointHandle, alt_rad)

        if base_reached and mount_reached:
            print("Rest mode entered.")
            FH.write_log("system", "Rest Mode", "success", "Telescope entered rest mode.")
        else:
            print("Warning: Rest mode movement timed out.")
            FH.write_log("system", "Rest Mode", "warning", "Timeout entering rest mode.")

        sim.simxStopSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxFinish(clientID)
        clientID = None
    except Exception as e:
        FH.write_log("system", "Rest Mode", "error", f"Failed to enter rest mode: {e}")
        print(f"Error entering rest mode: {e}")
        raise

def track_celestial_object(code: str):
    """
    Continuously track a celestial object by code, updating telescope position.
    Press 'q' to stop tracking.
    """
    try:
        while True:
            start_time = time.time()
            while time.time() - start_time < PING_RA_DEC:
                if keyboard.is_pressed('q') or keyboard.is_pressed('Q'):
                    print("Stopping tracking...")
                    telescope_rest()
                    FH.write_log("system", "Tracking", "success", "Stopped tracking celestial object.")
                    return
                time.sleep(0.1)
            _, name, ra, dec = C.get_celestial_object_details(code)
            alt, az = C.convert_radec_to_altaz(ra, dec)
            if check_limits(alt, az):
                print(f"Tracking Celestial Object -> NAME: {name}, CODE: {code}, RA: {ra:.3f} hours, Dec: {dec:.3f}°")
                print(f"Telescope tracking Alt: {alt:.2f}°, Az: {az:.2f}°\nPress q to stop tracking.\n")
                if test_con():
                    move_tel(alt, az)
                    FH.write_log("system", "Track Celestial Object", "success", f"Started tracking celestial object -> NAME: {name}, CODE: {code}")
                else:
                    FH.write_log("system", "Telescope Movement", "error", f"Failed to move telescope for object {name} (RA: {ra}, Dec: {dec})")
                    break
            else:
                print(f"Target coordinates (RA: {ra:.3f} hours, Dec: {dec:.3f}°) -> Out of bounds!")
                print(f"Coordinates (Alt: {alt:.2f}°, Az: {az:.2f}°) -> Stopping movement.")
                FH.write_log("system", "Tracking", "warning", f"Celestial object out of bounds: Alt: {alt}, Az: {az}.")
                if test_con():
                    telescope_rest()
                break
    except KeyboardInterrupt:
        FH.write_log("system", "Tracking", "warning", "Tracking interrupted by user.")
        if test_con():
            telescope_rest()
        print("Tracking stopped by user.")
    except Exception as e:
        FH.write_log("system", "Tracking", "error", f"Error occurred during tracking: {e}")
        print(f"Error occurred during tracking: {e}")

def close():
    """
    Close the CoppeliaSim connection (call on program exit).
    """
    global clientID
    if clientID is not None and clientID != -1:
        sim.simxStopSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxFinish(clientID)
        clientID = None
        print("CoppeliaSim connection closed.")

def main():
    """
    Test function.
    """
    test_con()
    track_celestial_object("M31")
    close()

if __name__ == '__main__':
    main()