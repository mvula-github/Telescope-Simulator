import time, keyboard, Calculations as C, System_Config
from System_Config import config

# Telescope limit degrees
ALTITUDE_LIMITS = config.get('altitude_limits')
AZIMUTH_LIMITS = config.get('azimuth_limits')

# Configuration variables
PING_RA_DEC = config.get('time_to_wait') # Ping ra and dec values every # seconds

def check_limits(alt, az):
    if ALTITUDE_LIMITS[0] <= alt <= ALTITUDE_LIMITS[1] and AZIMUTH_LIMITS[0] <= az <= AZIMUTH_LIMITS[1]:
        return True
    
    return False

def telescope_rest():
    print("Now entering rest mode. ")

def track_celestial_object(code):
    try:
        while True:
            start_time = time.time()

            # Check for 'q' press every 0.1 seconds without blocking the main loop
            while time.time() - start_time < PING_RA_DEC:
                if (keyboard.is_pressed('q')) or (keyboard.is_pressed('Q')):
                    print("Stopping tracking...")
                    telescope_rest() 
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
                # ADD CODE HERE
            else:
                print(f"Target coordinates (RA: {ra:.3f} hours, Dec: {dec:.3f}°) -> Out of bounds!")
                print(f"Coordinates (Alt: {alt:.2f}°, Az: {az:.2f}°) -> Stopping movement.")
                telescope_rest()
                break

    except KeyboardInterrupt:
        telescope_rest()
        print("Tracking stopped by user.")

def __main__():
    track_celestial_object("M31")

if __name__ == '__main__':
    __main__()