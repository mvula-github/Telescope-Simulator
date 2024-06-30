import os, sys
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

def __main__():
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