import os, sys, time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS
from astropy.time import Time
import astropy.units as u
import geocoder
from geopy.geocoders import Nominatim
import requests

# Get current location (latitude, longitude, and elevation)
def get_location_and_elevation():
    # Get the geolocation data based on the IP address
    g = geocoder.ip('me')
    
    if not g.ok:
        return None, None, None
    
    latitude, longitude = g.latlng
    
    # Get the elevation data
    response = requests.get(f'https://api.open-elevation.com/api/v1/lookup?locations={latitude},{longitude}')
    if response.status_code == 200:
        elevation_data = response.json()
        if 'results' in elevation_data and len(elevation_data['results']) > 0:
            elevation = elevation_data['results'][0]['elevation']
        else:
            elevation = None
    else:
        elevation = None

    return latitude, longitude, elevation

# Convert a celestial coordinate to altitude and azimuth in degrees
def celestial_to_altaz(ra, dec):
    # Variables
    time = Time.now()
    lat, lon, elev = get_location_and_elevation()
    ra = ra*u.hourangle
    dec = dec*u.deg

    sky_coord = SkyCoord(ra, dec, frame = 'icrs')
    location = EarthLocation(lat, lon, elev)

    altaz_frame = AltAz(obstime = time, location = location) # Create an AltAz frame at the specified location and time
    altaz_coord = sky_coord.transform_to(altaz_frame) # Transform the celestial coordinate to the AltAz frame

    # Extract and return the altitude and azimuth in degrees
    altitude = altaz_coord.alt.degree
    azimuth = altaz_coord.az.degree

    return altitude, azimuth

def altaz_to_celestial(alt_deg, az_deg):
    # Variables
    time = Time.now()
    lat, lon, elev = get_location_and_elevation()
    location = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=elev*u.m)

    alt_az_coords = AltAz(alt=alt_deg * u.deg, az=az_deg * u.deg, location=location, obstime=time) # Create AltAz frame with given parameters
    icrs_coords = alt_az_coords.transform_to(ICRS()) # Transform to ICRS (International Celestial Reference System) frame 

    # Extract RA and Dec
    ra = icrs_coords.ra.deg
    dec = icrs_coords.dec.deg

    return ra, dec

def __main__():
    alt_deg, az_deg = celestial_to_altaz(ra = 16*u.hourangle, dec = -23*u.deg) # Convert celestial reference frame to alt/az degrees
    ra, dec = altaz_to_celestial(alt_deg, az_deg) # Convert alt/az degrees to a celestial frame 

    print(f"Current Location: {get_location_and_elevation()}")
    print(f"Altitude: {alt_deg:.2f} degrees, Azimuth: {az_deg:.2f} degrees")
    print(f"Celestial Coordinates (ra, dec): ({ra}, {dec})")

if __name__ == '__main__':
    __main__()