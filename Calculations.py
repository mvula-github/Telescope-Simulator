import requests, geocoder, astropy.units as u

from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS
from astropy.time import Time
from astroquery.ipac.ned import Ned

# Get current location (latitude, longitude, and elevation)
def ip_get_location_and_elevation():
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
    now = Time.now()  # Get current time
    latitude, longitude, elevation = ip_get_location_and_elevation()

    if latitude is None or longitude is None or elevation is None:
        raise ValueError("Could not retrieve location or elevation data.")

    observer_location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m)  # Define the observer's location
    altaz_frame = AltAz(obstime=now, location=observer_location)  # Define the AltAz frame

    altaz_coords = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame=altaz_frame)  # Create an AltAz coordinate object
    icrs_coords = altaz_coords.transform_to(ICRS)  # Convert to ICRS (RA and Dec)

    return icrs_coords.ra.hourangle, icrs_coords.dec.degree

def convert_radec_to_altaz(ra, dec):
    now = Time.now()  # Get current time
    latitude, longitude, elevation = ip_get_location_and_elevation()

    if latitude is None or longitude is None or elevation is None:
        raise ValueError("Could not retrieve location or elevation data.")

    observer_location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m)  # Define the observer's location
    icrs_coords = SkyCoord(ra=ra * u.hourangle, dec=dec * u.deg, frame=ICRS)  # Define the RA/Dec coordinates in ICRS frame

    altaz_frame = AltAz(obstime=now, location=observer_location)  # Define the AltAz frame
    altaz_coords = icrs_coords.transform_to(altaz_frame)  # Convert to AltAz

    return altaz_coords.alt.degree, altaz_coords.az.degree

def __main__():
    latitude, longitude, elevation = ip_get_location_and_elevation()
    object_code, object_name, ra, dec = get_celestial_object_details("M31") # Andromeda Galaxy
    alt_converted, az_converted = convert_radec_to_altaz(ra, dec)
    ra_converted, dec_converted = convert_altaz_to_radec(alt_converted, az_converted)

    print(f"Current Location:  Latitude: {latitude}  Longitude: {longitude}  Elevation: {elevation}")
    print(f"Celestial Object Details:  Code: {object_code}  Name: {object_name}  RA: {ra}  DEC: {dec}")
    print(f"radec converted to alt and az:  ALT: {alt_converted}  AZ: {az_converted}")
    print(f"Altaz converted to ra and dec:  RA: {ra_converted}  DEC: {dec_converted}")

if __name__ == '__main__':
    __main__()
