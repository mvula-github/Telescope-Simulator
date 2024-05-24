import os, sys

# Gui libraries
import tkinter as tk 
from tkinter import filedialog 

# Astrophysics libraries
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS
from astropy.time import Time
import astropy.units as u

# Convert a celestial coordinate to altitude and azimuth in degrees
def celestial_to_altaz(sky_coord, location, time):
    altaz_frame = AltAz(obstime = time, location = location) # Create an AltAz frame at the specified location and time
    altaz_coord = sky_coord.transform_to(altaz_frame) # Transform the celestial coordinate to the AltAz frame

    # Extract and return the altitude and azimuth in degrees
    altitude = altaz_coord.alt.degree
    azimuth = altaz_coord.az.degree

    return altitude, azimuth

# Converts alt/az degrees to a celestial reference frame
def altaz_to_celestial(alt_deg, az_deg, location, time):
    icrs = ICRS()
    alt_az_coords = AltAz(alt = alt_deg * u.deg, az = az_deg * u.deg, location = location, obstime = time) # Create AltAz frame with given parameters
    icrs_coords = alt_az_coords.transform_to(icrs) # Transform to ICRS (International Celestial Reference System) frame 
    
    return icrs_coords

# Get current working directory
def get_working_directory():
    script_directory = os.path.dirname(os.path.abspath(__file__))

    return script_directory

# Create a 'Data' folder if it does not yet exist
def create_folder(name, location):
    data_directory = os.path.join(location, name)
    os.makedirs(data_directory, exist_ok = True)

    return data_directory

# Select a save location
def get_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window

    # Ask if the user wants to browse or enter manually
    choice = input("Choose how to provide the directory path:\n1. Browse\n2. Enter manually\nYour choice (1 or 2): ")

    if choice == '1':
        directory = filedialog.askdirectory(title = "Select a directory")
    elif choice == '2':
        directory = input("Enter the directory path: ")
    else:
        print("Invalid choice!")
        return None

    # Basic validation to ensure it's a valid path
    if not os.path.isdir(directory):
        print("Invalid directory!")
        return None

    return directory

def __main__():
    # Select save location
    save_location = get_directory()
    print(save_location)

    # Get current working directory
    script_directory = get_working_directory()
    print("Working directory: ", script_directory)

    # Create a 'Data' folder to store observed data into text files
    data_directory = create_folder('Data', script_directory)

    # Convert celestial reference frame to alt/az degrees
    observing_location = EarthLocation(lat = '-26.111111deg', lon = '27.944444deg', height = 1500*u.m) 
    observing_time = Time.now()
    ra = 16*u.hourangle  # Right Ascension in hours
    dec = -23*u.deg      # Declination in degrees
    sky_coord = SkyCoord(ra = ra, dec = dec, frame = 'icrs')  # 'icrs' is the International Celestial Reference System
    alt_deg, az_deg = celestial_to_altaz(sky_coord, observing_location, observing_time)

    print(f"Altitude: {alt_deg:.2f} degrees")
    print(f"Azimuth: {az_deg:.2f} degrees")

    # Convert alt/az degrees to a celestial frame
    latitude = -26.1561
    longitude = 27.8719
    elevation = 1735 # meters
    location = EarthLocation(lat = latitude*u.deg, lon = longitude*u.deg, height = elevation*u.m) 
    observation_time = Time.now() 
    celestial_coords = altaz_to_celestial(alt_deg, az_deg, location, observation_time) # Convert to celestial coordinates

    print(celestial_coords)

if __name__ == '__main__':
    __main__()