import os, requests

from astropy import coordinates as coord
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS
from astropy.time import Time
import astropy.units as u
from astroquery.simbad import Simbad
from astroquery.vizier import Vizier
from astroquery.ned import Ned
from astropy.utils.data import download_file

import geocoder
from geopy.geocoders import Nominatim

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

def get_celestial_object_details(code):
    # Query NED for the celestial object
    result = Ned.query_object(code)
    
    # Check if the result is not empty
    if result is not None and len(result) > 0:
        # Get the first result (assuming the first result is the desired one)
        obj = result[0]
        code = code  
        name = obj['Object Name']
        ra = obj['RA']
        dec = obj['DEC']
        
        return code, name, ra, dec
    else:
        return None, None, None, None
    
def convert_altaz_to_radec(alt, az):
    now = Time.now() # Get current time
    latitude, longitude, elevation = get_location_and_elevation()
    
    observer_location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m) # Define the observer's location
    
    altaz_frame = AltAz(obstime=now, location=observer_location) # Define the AltAz frame
    
    altaz_coords = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame=altaz_frame) # Create an AltAz coordinate object
    icrs_coords = altaz_coords.transform_to(ICRS) # Convert to ICRS (RA and Dec)
    
    return icrs_coords.ra, icrs_coords.dec

def convert_radec_to_altaz(ra, dec):
    time = Time.now()
    latitude, longitude, elevation = get_location_and_elevation()
    ra = ra*u.hourangle
    dec = dec*u.deg

    sky_coord = SkyCoord(ra, dec, frame = 'icrs')
    location = EarthLocation(latitude, longitude, elevation)

    altaz_frame = AltAz(obstime = time, location = location) # Create an AltAz frame at the specified location and time
    altaz_coord = sky_coord.transform_to(altaz_frame) # Transform the celestial coordinate to the AltAz frame

    return altaz_coord.alt.degree, altaz_coord.az.degree

def __main__():
    latitude, longitude, elevation = get_location_and_elevation()
    object_code, object_name, ra, dec = get_celestial_object_details("M31") # Andromeda Galaxy
    alt_converted, az_converted = convert_radec_to_altaz(ra, dec)
    ra_converted, dec_converted = convert_altaz_to_radec(alt_converted, az_converted)

    print(f"Current Location:  Latitude: {latitude}  Longitude: {longitude}  Elevation: {elevation}")
    print(f"Celestial Object Details:  Code: {object_code}  Name: {object_name}  RA: {ra}  DEC: {dec}")
    print(f"Altaz converted to ra and dec:  RA: {ra_converted}  DEC: {dec_converted}")
    print(f"radec converted to alt and az:  ALT: {alt_converted}  AZ: {az_converted}")

if __name__ == '__main__':
    __main__()
