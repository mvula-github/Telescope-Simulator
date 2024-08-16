import time, keyboard, Calculations as C

# Telescope limit degrees
ALTITUDE_LIMITS = (-75, 75) 
AZIMUTH_LIMITS = (-340, 340)

# Configuration variables
PING_RA_DEC = 3 # Ping ra and dec values every # seconds

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






# import RPi.GPIO as GPIO
# from RpiMotorLib import RpiMotorLib
# import time

# direction= 22 # Direction (DIR) GPIO Pin
# step = 23 # Step GPIO Pin
# EN_pin = 24 # enable pin (LOW to enable)

# mymotortest = RpiMotorLib.A4988Nema(direction, step, (21,21,21), "DRV8825")
# GPIO.setup(EN_pin,GPIO.OUT) # set enable pin as output

# dir_array = [False,True]
# GPIO.output(EN_pin,GPIO.LOW) # pull enable to low to enable motor
# for ii in range(10):
#     mymotortest.motor_go(dir_array[ii%2], # False=Clockwise, True=Counterclockwise
#                         "Full" , # Step type (Full,Half,1/4,1/8,1/16,1/32)
#                         200, # number of steps
#                         .0005, # step delay [sec]
#                         False, # True = print verbose output 
#                         .05) # initial delay [sec]
#     time.sleep(1)

# GPIO.cleanup() # clear GPIO allocations after run