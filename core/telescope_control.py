import time
import math
import core.file_handling as FH
from core.system_config import config
import simulation.sim_interface as sim
import core.calculations as C
import ctypes as ct  # Import ctypes for joint position retrieval
import threading

try:
    import keyboard  # May require elevated privileges on Windows
    _KEYBOARD_AVAILABLE = True
except Exception:
    keyboard = None
    _KEYBOARD_AVAILABLE = False
try:
    import msvcrt  # Windows-only fallback
    _MSVCRT_AVAILABLE = True
except Exception:
    msvcrt = None
    _MSVCRT_AVAILABLE = False

# Load static settings from configuration (limits read dynamically via accessors below)
PING_RA_DEC = config.get('celestial_ping_time', 3)
MOVEMENT_TIMEOUT = config.get('movement_timeout', 10)
POSITION_TOLERANCE = config.get('position_tolerance', 0.01)
FORCE_FIRST_CLOCKWISE = config.get('force_first_movement_clockwise', False)
HEADLESS_TRACKING = config.get('headless_tracking', False)
TRACKING_IN_BACKGROUND = config.get('tracking_in_background', False)
INVERT_ELEVATION_AXIS = bool(config.get('invert_elevation_axis', False))
BASE_JOINT_NAME = config.get('base_joint_name', 'Base_joint')
MOUNT_JOINT_NAME = config.get('mount_joint_name', 'Mount_joint')
PREVENT_BELOW_HORIZON = bool(config.get('prevent_below_horizon', True))
SAFETY_ALT_MARGIN_DEG = float(config.get('safety_alt_margin_deg', 2.0))
SAFETY_AZ_MARGIN_DEG = float(config.get('safety_az_margin_deg', 1.0))

def _get_altitude_limits():
    limits = config.get('altitude_limits', [0, 90])
    if not isinstance(limits, (list, tuple)) or len(limits) != 2:
        return [0, 90]
    return [float(limits[0]), float(limits[1])]

def _get_azimuth_limits():
    limits = config.get('azimuth_limits', [25, 355])
    if not isinstance(limits, (list, tuple)) or len(limits) != 2:
        return [25, 355]
    return [float(limits[0]), float(limits[1])]

# Global variables for telescope connection to CoppeliaSim and movement tracking
clientID = None
is_first_movement = True  # Flag to track if this is the first movement after simulation start
_tracking_thread = None
_tracking_stop_event = threading.Event()

def _assert_sim_lib_loaded():
    if getattr(sim, 'libsimx', None) is None:
        raise RuntimeError(
            "CoppeliaSim remote API library is not loaded. Ensure 'remoteApi' is present next to sim.py "
            "and matches your OS/architecture, then restart the program."
        )

def test_con() -> bool:
    """
    Test and (re)establish connection to CoppeliaSim telescope.
    Returns True if connected, False otherwise.
    """
    global clientID, is_first_movement
    try:
        _assert_sim_lib_loaded()
        # Check if connection is not established or lost
        if clientID is None or sim.simxGetConnectionId(clientID) == -1:
            print("Connecting to telescope.")
            sim.simxFinish(-1)  # Close all opened connections
            # Attempt to connect to CoppeliaSim remote API server
            clientID = sim.simxStart('127.0.0.1', 19999, True, True, 5000, 5)
            if clientID != -1:
                print("Connected to telescope.")
                is_first_movement = True  # Reset for first movement after connection
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
    alt_limits = _get_altitude_limits()
    az_limits = _get_azimuth_limits()
    return alt_limits[0] <= alt <= alt_limits[1] and az_limits[0] <= az <= az_limits[1]

def _effective_limits():
    alt_limits = _get_altitude_limits()
    az_limits = _get_azimuth_limits()
    alt_min = alt_limits[0] + SAFETY_ALT_MARGIN_DEG
    alt_max = alt_limits[1] - SAFETY_ALT_MARGIN_DEG
    az_min = az_limits[0] + SAFETY_AZ_MARGIN_DEG
    az_max = az_limits[1] - SAFETY_AZ_MARGIN_DEG
    if PREVENT_BELOW_HORIZON:
        alt_min = max(alt_min, 0.0 + SAFETY_ALT_MARGIN_DEG)
    # Ensure min <= max even with tight margins
    if alt_min > alt_max:
        alt_min, alt_max = alt_limits[0], alt_limits[1]
    if az_min > az_max:
        az_min, az_max = az_limits[0], az_limits[1]
    return (alt_min, alt_max), (az_min, az_max)

def _clamp_to_limits(alt: float, az: float) -> (float, float):
    (alt_min, alt_max), (az_min, az_max) = _effective_limits()
    # Normalize azimuth to [0, 360)
    az_norm = az % 360
    # Clamp to effective window
    clamped_alt = min(max(alt, alt_min), alt_max)
    clamped_az = min(max(az_norm, az_min), az_max)
    return clamped_alt, clamped_az

def get_current_joint_position(joint_handle: int) -> float:
    """
    Get the current position of a joint in radians using direct ctypes call.
    """
    _assert_sim_lib_loaded()
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
        try:
            current_position = get_current_joint_position(joint_handle)
            if abs(current_position - target_position) < POSITION_TOLERANCE:
                return True
        except Exception as e:
            # Continue waiting, but log the error
            pass
        time.sleep(0.1)
    return False

def move_tel(alt: float, az: float, current_user: str = None):
    """
    Move the telescope to the specified altitude and azimuth without accumulation.
    """
    global is_first_movement
    
    # CRITICAL SAFETY CHECK: Prevent negative altitude (below horizon)
    if alt < 0:
        print(f"ERROR: Altitude {alt}° is below horizon! Clamping to 0° to prevent telescope damage.")
        alt = 0.0
    
    # Always clamp to effective limits if enabled, otherwise validate
    clamp_enabled = bool(config.get('clamp_to_limits', True))
    if clamp_enabled:
        original_alt, original_az = alt, az
        alt, az = _clamp_to_limits(alt, az)
        if (original_alt, original_az) != (alt, az):
            print(f"⚠️  WARNING: Target clamped to safe limits!")
            print(f"   Original: Alt: {original_alt}°, Az: {original_az}°")
            print(f"   Clamped:  Alt: {alt}°, Az: {az}°")
            print(f"   Safety margins: Alt ±{SAFETY_ALT_MARGIN_DEG}°, Az ±{SAFETY_AZ_MARGIN_DEG}°")
    else:
        if not check_limits(alt, az):
            alt_limits = _get_altitude_limits()
            az_limits = _get_azimuth_limits()
            raise ValueError(f"Out of limits: Alt={alt} (limits={alt_limits}), Az={az} (limits={az_limits})")
    try:
        if not test_con():
            raise RuntimeError("Connection failed")
        
        # Get joint handles
        baseJointHandle = sim.simxGetObjectHandle(clientID, BASE_JOINT_NAME, sim.simx_opmode_blocking)[1]
        mountJointHandle = sim.simxGetObjectHandle(clientID, MOUNT_JOINT_NAME, sim.simx_opmode_blocking)[1]

        # Ensure motors and position controllers are enabled and forces sufficient
        try:
            sim.simxSetObjectInt32Param(clientID, baseJointHandle, sim.sim_jointintparam_motor_enabled, 1, sim.simx_opmode_oneshot)
            sim.simxSetObjectInt32Param(clientID, baseJointHandle, sim.sim_jointintparam_ctrl_enabled, 1, sim.simx_opmode_oneshot)
            sim.simxSetJointMaxForce(clientID, baseJointHandle, float(config.get('base_max_force', 1000.0)), sim.simx_opmode_oneshot)

            sim.simxSetObjectInt32Param(clientID, mountJointHandle, sim.sim_jointintparam_motor_enabled, 1, sim.simx_opmode_oneshot)
            sim.simxSetObjectInt32Param(clientID, mountJointHandle, sim.sim_jointintparam_ctrl_enabled, 1, sim.simx_opmode_oneshot)
            
            # Increase force for low altitudes to prevent getting stuck
            base_force = float(config.get('elevation_max_force', 1500.0))
            if alt < 30:  # Increase force for low altitudes
                base_force *= 1.5
                print(f"DEBUG: Low altitude detected ({alt}°), increasing force to {base_force}")
            
            sim.simxSetJointMaxForce(clientID, mountJointHandle, base_force, sim.simx_opmode_oneshot)
        except Exception as _:
            # Ignore parameter setting errors; continue with best effort
            pass

        # Convert to radians - ensure 0°=horizontal, 90°=up
        # If invert is needed, we need to map: 0°->90°, 90°->0° in CoppeliaSim coordinates
        if INVERT_ELEVATION_AXIS:
            # Map user input (0-90°) to CoppeliaSim coordinates (90-0°)
            # But ensure we don't go below 0° in CoppeliaSim coordinates
            coppelia_alt = max(0, 90 - alt)  # Ensure minimum 0° in CoppeliaSim
            alt_rad = math.radians(coppelia_alt)
            print(f"DEBUG: User input {alt}° -> CoppeliaSim {coppelia_alt}° (inverted)")
        else:
            alt_rad = math.radians(alt)
            print(f"DEBUG: User input {alt}° -> CoppeliaSim {alt}° (not inverted)")
        az_rad = math.radians(az)

        # Get current azimuth
        current_az = get_current_joint_position(baseJointHandle)
        print(f"DEBUG: Current Az: {math.degrees(current_az):.2f}°, Target Az: {az:.2f}°")

        # Calculate azimuth movement
        if not is_first_movement or not FORCE_FIRST_CLOCKWISE:
            current_az_degrees = -math.degrees(current_az) % 360
            target_az_degrees = az
            print(f"DEBUG: Converted current: {current_az_degrees:.2f}°, target: {target_az_degrees:.2f}°")
            if target_az_degrees > current_az_degrees:
                direction = "clockwise"
                diff = target_az_degrees - current_az_degrees
                movement_sign = -1
            else:
                direction = "anticlockwise"
                diff = current_az_degrees - target_az_degrees
                movement_sign = 1
            print(f"DEBUG: Direction: {direction}, Raw diff: {diff:.2f}°")
            target_az = -math.radians(target_az_degrees)
            print(f"DEBUG: Subsequent movement - Moving {direction} to {target_az_degrees}°, Target Az: {math.degrees(target_az):.2f}°")
        else:
            # For first movement: optionally force clockwise regardless of shortest path
            if az_rad >= current_az:
                clockwise_distance = az_rad - current_az
            else:
                clockwise_distance = (2 * math.pi) - (current_az - az_rad)
            target_az = current_az - clockwise_distance  # CoppeliaSim uses inverted coordinates
            print(f"DEBUG: First movement CLOCKWISE - Distance: -{math.degrees(clockwise_distance):.2f}°, Target Az: {math.degrees(target_az):.2f}°")
            is_first_movement = False

        # Debug: Elevation joint current vs target
        try:
            current_alt_rad = get_current_joint_position(mountJointHandle)
            # Show user input altitude and CoppeliaSim target
            if INVERT_ELEVATION_AXIS:
                coppelia_target = 90 - alt
                print(f"DEBUG: Current Alt: {math.degrees(current_alt_rad):.2f}°, User Input: {alt:.2f}°, CoppeliaSim Target: {coppelia_target:.2f}° (invert={INVERT_ELEVATION_AXIS})")
            else:
                print(f"DEBUG: Current Alt: {math.degrees(current_alt_rad):.2f}°, Target Alt: {math.degrees(alt_rad):.2f}° (invert={INVERT_ELEVATION_AXIS})")
        except Exception:
            pass

        # Start simulation if not already running
        sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, baseJointHandle, target_az, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, mountJointHandle, alt_rad, sim.simx_opmode_oneshot)

        # Wait for joints to reach target positions
        base_reached = wait_for_joint_position(baseJointHandle, target_az)
        mount_reached = wait_for_joint_position(mountJointHandle, alt_rad)

        if base_reached and mount_reached:
            FH.write_log("system", "Telescope Movement", "success", f"Moved telescope to Alt: {alt}, Az: {az}", current_user)
            print("Telescope moved successfully.")
        else:
            FH.write_log("system", "Telescope Movement", "warning", f"Timeout moving telescope to Alt: {alt}, Az: {az}", current_user)
            print("Warning: Telescope movement timed out.")
    except Exception as e:
        FH.write_log("system", "Telescope Movement", "error", f"Failed to move telescope to Alt: {alt}, Az: {az} -> Error: {e}", current_user)
        print(f"Error moving telescope: {e}")
        # Don't re-raise the exception - let the menu handler deal with it

def telescope_rest(username: str, current_user: str = None):
    """
    Move the telescope to its rest (default) position (Alt=90, Az=0 - straight up).
    Always returns to 0° azimuth via anticlockwise rotation.
    """
    global clientID, is_first_movement
    try:
        print("DEBUG: Testing connection...")
        if not test_con():
            raise RuntimeError("Connection failed")
        print("DEBUG: Getting joint handles...")
        baseJointHandle = sim.simxGetObjectHandle(clientID, BASE_JOINT_NAME, sim.simx_opmode_blocking)[1]
        mountJointHandle = sim.simxGetObjectHandle(clientID, MOUNT_JOINT_NAME, sim.simx_opmode_blocking)[1]
        print("DEBUG: Joint handles obtained successfully")
        current_az = get_current_joint_position(baseJointHandle)
        current_az_degrees = -math.degrees(current_az) % 360
        # Compute safe rest targets within configured limits
        alt_limits = _get_altitude_limits()
        az_limits = _get_azimuth_limits()
        safe_alt = min(max(90.0, alt_limits[0]), alt_limits[1])
        # Park at the nearest limit boundary to minimize travel
        az_candidates = [az_limits[0], az_limits[1]]
        safe_az = min(az_candidates, key=lambda a: min((a - current_az_degrees) % 360, (current_az_degrees - a) % 360))
        print(f"DEBUG REST: Current Az: {current_az_degrees:.2f}°, Safe Rest Alt: {safe_alt:.2f}°, Safe Rest Az: {safe_az:.2f}°")
        # Apply same coordinate mapping as move_tel
        if INVERT_ELEVATION_AXIS:
            alt_rad = math.radians(90 - safe_alt)
        else:
            alt_rad = math.radians(safe_alt)
        target_az = -math.radians(safe_az)
        sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, baseJointHandle, target_az, sim.simx_opmode_oneshot)
        sim.simxSetJointTargetPosition(clientID, mountJointHandle, alt_rad, sim.simx_opmode_oneshot)
        base_reached = wait_for_joint_position(baseJointHandle, target_az)
        mount_reached = wait_for_joint_position(mountJointHandle, alt_rad)
        if base_reached and mount_reached:
            print("Rest mode entered (safe within configured limits).")
            FH.write_log(username, "Rest Mode", "success", f"Telescope parked safely (Alt: {safe_alt}, Az: {safe_az}).", current_user)
        else:
            print("Warning: Rest mode movement timed out.")
            FH.write_log(username, "Rest Mode", "warning", "Timeout entering rest mode.", current_user)
        # Note: Connection remains open for further telescope operations
    except Exception as e:
        FH.write_log(username, "Rest Mode", "error", f"Failed to enter rest mode: {e}", current_user)
        print(f"Error entering rest mode: {e}")

def _is_stop_requested() -> bool:
    if HEADLESS_TRACKING:
        return False
    try:
        if _KEYBOARD_AVAILABLE and (keyboard.is_pressed('q') or keyboard.is_pressed('Q')):
            return True
    except Exception:
        pass
    if _MSVCRT_AVAILABLE:
        try:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b'q', b'Q'):
                    return True
        except Exception:
            pass
    return False

def _tracking_loop(code: str):
    try:
        while not _tracking_stop_event.is_set():
            start_time = time.time()
            # Wait for the configured ping interval or until stop requested
            while time.time() - start_time < PING_RA_DEC:
                if _tracking_stop_event.is_set() or _is_stop_requested():
                    print("Stopping tracking...")
                    telescope_rest("system", current_user)
                    FH.write_log("system", "Tracking", "success", "Stopped tracking celestial object.", current_user)
                    _tracking_stop_event.set()
                    return
                time.sleep(0.1)
            # Get celestial object details and convert to Alt/Az
            _, name, ra, dec = C.get_celestial_object_details(code)
            alt, az = C.convert_radec_to_altaz(ra, dec)
            if check_limits(alt, az):
                print(f"Tracking Celestial Object -> NAME: {name}, CODE: {code}, RA: {ra:.3f} hours, Dec: {dec:.3f}°")
                print(f"Telescope tracking Alt: {alt:.2f}°, Az: {az:.2f}°\nPress q to stop tracking.\n")
                if test_con():
                    move_tel(alt, az, current_user)
                    FH.write_log("system", "Track Celestial Object", "success", f"Started tracking celestial object -> NAME: {name}, CODE: {code}", current_user)
                else:
                    FH.write_log("system", "Telescope Movement", "error", f"Failed to move telescope for object {name} (RA: {ra}, Dec: {dec})", current_user)
                    break
            else:
                print(f"Target coordinates (RA: {ra:.3f} hours, Dec: {dec:.3f}°) -> Out of bounds!")
                print(f"Coordinates (Alt: {alt:.2f}°, Az: {az:.2f}°) -> Stopping movement.")
                FH.write_log("system", "Tracking", "warning", f"Celestial object out of bounds: Alt: {alt}, Az: {az}.", current_user)
                if test_con():
                    telescope_rest("system", current_user)
                break
    except KeyboardInterrupt:
        FH.write_log("system", "Tracking", "warning", "Tracking interrupted by user.", current_user)
        if test_con():
            telescope_rest("system", current_user)
        print("Tracking stopped by user.")
    except Exception as e:
        FH.write_log("system", "Tracking", "error", f"Error occurred during tracking: {e}", current_user)
        print(f"Error occurred during tracking: {e}")

def track_celestial_object(code: str, current_user: str = None):
    """
    Continuously track a celestial object by code. Optional background thread.
    """
    if TRACKING_IN_BACKGROUND:
        global _tracking_thread
        if _tracking_thread and _tracking_thread.is_alive():
            print("Tracking already in progress.")
            return
        _tracking_stop_event.clear()
        _tracking_thread = threading.Thread(target=_tracking_loop, args=(code,), daemon=True)
        _tracking_thread.start()
        print("Tracking started in background.")
        return
    else:
        _tracking_stop_event.clear()
        _tracking_loop(code)

def stop_tracking():
    _tracking_stop_event.set()
    if _tracking_thread and _tracking_thread.is_alive():
        _tracking_thread.join(timeout=2)

def close():
    """
    Close the CoppeliaSim connection (call on program exit).
    """
    global clientID, is_first_movement
    if clientID is not None and clientID != -1:
        sim.simxStopSimulation(clientID, sim.simx_opmode_oneshot)
        sim.simxFinish(clientID)
        clientID = None
        is_first_movement = True  # Reset for next connection
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