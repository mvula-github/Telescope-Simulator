import time, keyboard, Calculations as C, System_Config, File_Handling as FH
from System_Config import config

# Imports for CoppeliaSim simulation:
import sim
import time
import math

# Telescope limit degrees
ALTITUDE_LIMITS = config.get('altitude_limits')
AZIMUTH_LIMITS = config.get('azimuth_limits')

# Configuration variables
PING_RA_DEC = config.get('celestial_ping_time') # Ping ra and dec values every # seconds

# Global variable for keeping track of telescope connection
clientID = None

# Function for testing connection to CoppeliaSim radio telescope
def test_con():
    global clientID

    try:

     # If clientID is None or the connection is inactive, attempt to connect
     if clientID is None or sim.simxGetConnectionId(clientID) == -1:
        print("Connecting to telescope. ")
        
        sim.simxFinish(-1) # Just in case, close all opened connections
        clientID = sim.simxStart('127.0.0.1', 19999, True, True, 5000, 5) # Attempt to establish a connection
        
        if clientID != -1:
            return True
        else:
            print("Failed to connect to telescope. ")
            FH.write_log("admin","Telescope Connection", False, "Failed to connect to telescope.")
            return False
     else:
        return True
    except Exception as e:
        FH.write_log("admin","Telescope connection", False, f"Connection error: {e}")

# Function for pointing the simulated telescope straight up (rest mode / default starting position) in CoppeliaSim
def telescope_rest():
 try:
    # Get handles for the joints
    baseJointHandle = sim.simxGetObjectHandle(clientID, 'Base_joint', sim.simx_opmode_blocking)[1]
    mountJointHandle = sim.simxGetObjectHandle(clientID, 'Mount_joint', sim.simx_opmode_blocking)[1]

    # Ensure the simulation is running
    sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)

    # Define the target angles (in radians)
    baseTargetAngle = math.radians(0)  # degrees for the base
    mountTargetAngle = math.radians(0)  # degrees for the mount

    # Set the target positions for the joints
    sim.simxSetJointTargetPosition(clientID, baseJointHandle, baseTargetAngle, sim.simx_opmode_oneshot)
    sim.simxSetJointTargetPosition(clientID, mountJointHandle, mountTargetAngle, sim.simx_opmode_oneshot)

    # Wait a bit to see the movement
    time.sleep(3)

    # Optionally, stop the simulation
    sim.simxStopSimulation(clientID, sim.simx_opmode_oneshot)

    # Close the connection
    sim.simxFinish(clientID)

    print("Rest mode entered. ")
    FH.write_log("admin", "Rest Mode", True, "Telescope entered rest mode.")
 except Exception as e:
    FH.write_log("admin", "Rest Mode", False, f"Failed to enter rest mode: {e}")
    print(f"Error entering rest mode: {e}") 
     
# Function for moving the simulated telescope in CoppeliaSim
def move_tel(alt, az):
 try:
    # Get handles for the joints
    baseJointHandle = sim.simxGetObjectHandle(clientID, 'Base_joint', sim.simx_opmode_blocking)[1]
    mountJointHandle = sim.simxGetObjectHandle(clientID, 'Mount_joint', sim.simx_opmode_blocking)[1]

    # Ensure the simulation is running
    sim.simxStartSimulation(clientID, sim.simx_opmode_oneshot)

    # Define the target angles (in radians)
    baseTargetAngle = math.radians(az)  # degrees for the base
    mountTargetAngle = math.radians(alt)  # degrees for the mount

    # Set the target positions for the joints
    sim.simxSetJointTargetPosition(clientID, baseJointHandle, baseTargetAngle, sim.simx_opmode_oneshot)
    sim.simxSetJointTargetPosition(clientID, mountJointHandle, mountTargetAngle, sim.simx_opmode_oneshot)

    # Wait a bit to see the movement
    time.sleep(3)

    FH.write_log("admin", "Telescope Movement", True, f"Moved telescope to Alt: {alt}, Az: {az}")
 except Exception as e:
        FH.write_log("admin", "Telescope Movement", False, f"Failed to move telescope to Alt: {alt}, Az: {az} -> Error: {e}")
        print(f"Error moving telescope: {e}")
def check_limits(alt, az):
    if ALTITUDE_LIMITS[0] <= alt <= ALTITUDE_LIMITS[1] and AZIMUTH_LIMITS[0] <= az <= AZIMUTH_LIMITS[1]:
        return True
    
    return False

def track_celestial_object(code):
    try:
        while True:
            start_time = time.time()

            # Check for 'q' press every 0.1 seconds without blocking the main loop
            while time.time() - start_time < PING_RA_DEC:
                if (keyboard.is_pressed('q')) or (keyboard.is_pressed('Q')):
                    print("Stopping tracking...")
                    telescope_rest() 
                    FH.write_log("admin", "Tracking", True, "Stopped tracking celestial object.")
                    return  # Exit the function

                time.sleep(0.1)  # Short sleep to prevent CPU overload

            # Fetch celestial object details and convert coordinates
            code, name, ra, dec = C.get_celestial_object_details(code)
            alt, az = C.convert_radec_to_altaz(ra, dec)

            # Check if the object is within the telescope's movement limits
            if check_limits(alt, az):
                print(f"Tracking Celestial Object -> NAME: {name}, CODE: {code}, RA: {ra:.3f} hours, Dec: {dec:.3f}°")
                print(f"Telescope tracking Alt: {alt:.2f}°, Az: {az:.2f}°\nPress q to stop tracking.\n")

                # Move telescope
                if test_con(): # If test_con() returns True
                    move_tel(alt, az)
                    FH.write_log("admin", "Track Celestial Object", True, f"Started tracking celestial object -> NAME: {name}, CODE: {code}")
                else:
                    FH.write_log("admin", "Telescope Movement", False, f"Failed to move telescope for object {name} (RA: {ra}, Dec: {dec}")
                    break
            else:
                print(f"Target coordinates (RA: {ra:.3f} hours, Dec: {dec:.3f}°) -> Out of bounds!")
                print(f"Coordinates (Alt: {alt:.2f}°, Az: {az:.2f}°) -> Stopping movement.")
                FH.write_log("admin", "Tracking", False, f"Celestial object out of bounds: Alt: {alt}, Az: {az}.")
                if test_con(): # If test_con() returns True
                    telescope_rest()
                # Not executing a break statement if test_con() returns False since the code will execute a break statement in the following line either way
                break

    except KeyboardInterrupt:
        FH.write_log("admin", "Tracking", True, "Tracking interrupted by user.")
        if test_con(): # If test_con() returns True
            telescope_rest()
        print("Tracking stopped by user.")
    except Exception as e:
        FH.write_log("admin", "Tracking", False, f"Error occurred during tracking: {e}")
        print(f"Error occurred during tracking: {e}")
def __main__():
    track_celestial_object("M31")

if __name__ == '__main__':
    __main__()