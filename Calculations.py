import time
import requests
import geocoder
import logging
from astropy import units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS
from astropy.time import Time
from astroquery.ipac.ned import Ned
from System_Config import config

logging.basicConfig(level=logging.INFO)

def get_location_and_elevation(method='stored'):
    """
    Returns (latitude, longitude, elevation) using either stored config or IP-based lookup.
    """
    latitude, longitude, elevation = None, None, None
    retries = 3
    delay = 3

    if method == 'ip':
        g = geocoder.ip('me')
        if g.ok:
            latitude, longitude = g.latlng
            for attempt in range(retries):
                try:
                    response = requests.get(
                        f'https://api.open-elevation.com/api/v1/lookup?locations={latitude},{longitude}'
                    )
                    response.raise_for_status()
                    elevation_data = response.json()
                    if 'results' in elevation_data and elevation_data['results']:
                        elevation = elevation_data['results'][0]['elevation']
                        break
                    else:
                        logging.warning("No elevation data found in the response.")
                except requests.RequestException as e:
                    logging.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < retries - 1:
                        time.sleep(delay)
            else:
                logging.error("Failed to fetch elevation data after retries.")
        else:
            logging.error("Error retrieving IP-based location.")
    else:
        latitude = config.get('latitude')
        longitude = config.get('longitude')
        elevation = config.get('elevation')

    return latitude, longitude, elevation

def get_celestial_object_details(code):
    """
    Returns (code, name, ra, dec) for a celestial object code using NED.
    """
    if not isinstance(code, str) or not code.strip():
        raise ValueError("The 'code' must be a non-empty string.")

    try:
        result = Ned.query_object(code)
    except Exception as e:
        raise RuntimeError(f"Failed to query NED: {e}")

    if result is not None and len(result) > 0:
        obj = result[0]
        name = obj['Object Name']
        ra = obj['RA']
        dec = obj['DEC']
        return code, name, ra, dec
    else:
        return None, None, None, None

def list_available_celestial_objects(ra, dec, radius=0.1):
    """
    Prints celestial objects within a radius (deg) of given RA/Dec.
    """
    try:
        ra_deg, dec_deg = convert_radec_to_degrees(ra, dec)
        icrs_coords = SkyCoord(ra_deg, dec_deg, frame='icrs', unit='deg')
        result = Ned.query_region(icrs_coords, radius=radius * u.deg)
        if result is not None and len(result) > 0:
            logging.info("Available columns: %s", result.colnames)
            for obj in result:
                name = obj.get('Object Name', 'Unknown')
                print(f"Name: {name}")
        else:
            print("No celestial objects found in the specified region.")
    except Exception as e:
        logging.error(f"Error querying region: {e}")

def convert_altaz_to_radec(alt, az):
    """
    Converts Alt/Az to RA/Dec for the current location and time.
    """
    if not (isinstance(alt, (int, float)) and isinstance(az, (int, float))):
        raise ValueError("Both 'alt' and 'az' must be numeric values (int or float).")
    if not (-90 <= alt <= 90):
        raise ValueError("Altitude 'alt' must be between -90 and 90 degrees.")
    if not (0 <= az <= 360):
        raise ValueError("Azimuth 'az' must be between 0 and 360 degrees.")

    now = Time.now()
    latitude, longitude, elevation = get_location_and_elevation()
    if None in (latitude, longitude, elevation):
        raise ValueError("Could not retrieve location or elevation data.")

    observer_location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m)
    altaz_frame = AltAz(obstime=now, location=observer_location)
    altaz_coords = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame=altaz_frame)
    icrs_coords = altaz_coords.transform_to(ICRS)
    return icrs_coords.ra.hourangle, icrs_coords.dec.degree

def convert_radec_to_degrees(ra, dec=None, frame='icrs'):
    """
    Converts RA/Dec in various formats to degrees.
    """
    if isinstance(ra, (float, int)) and isinstance(dec, (float, int)):
        icrs_coords = SkyCoord(ra, dec, frame=frame, unit='deg')
    elif isinstance(ra, str) and isinstance(dec, str):
        if "h" in ra or "d" in dec:
            icrs_coords = SkyCoord(ra, dec, frame=frame)
        else:
            icrs_coords = SkyCoord(ra, dec, frame=frame, unit=(u.hourangle, u.deg))
    elif isinstance(ra, str) and dec is None:
        icrs_coords = SkyCoord(ra, frame=frame, unit=(u.hourangle, u.deg))
    else:
        raise ValueError("Unsupported RA/Dec format. Please provide RA and Dec in a supported format.")

    return icrs_coords.ra.degree, icrs_coords.dec.degree

def convert_radec_to_altaz(ra, dec):
    """
    Converts RA/Dec to Alt/Az for the current location and time.
    """
    if not (isinstance(ra, (int, float, str)) and isinstance(dec, (int, float, str))):
        raise ValueError("Both 'ra' and 'dec' must be numeric values (int, float) or strings.")

    try:
        ra_deg, dec_deg = convert_radec_to_degrees(ra, dec)
    except ValueError as ve:
        raise ValueError(f"RA/Dec conversion error: {ve}")

    now = Time.now()
    latitude, longitude, elevation = get_location_and_elevation()
    if None in (latitude, longitude, elevation):
        raise ValueError("Could not retrieve location or elevation data.")

    observer_location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m)
    icrs_coords = SkyCoord(ra_deg, dec_deg, frame='icrs', unit='deg')
    altaz_frame = AltAz(obstime=now, location=observer_location)
    altaz_coords = icrs_coords.transform_to(altaz_frame)
    return altaz_coords.alt.degree, altaz_coords.az.degree

def main():
    latitude, longitude, elevation = get_location_and_elevation()
    object_code, object_name, ra, dec = get_celestial_object_details("M31")
    alt_converted, az_converted = convert_radec_to_altaz(ra, dec)
    ra_converted, dec_converted = convert_altaz_to_radec(alt_converted, az_converted)

    print(f"Current Location:  Latitude: {latitude}  Longitude: {longitude}  Elevation: {elevation}")
    print(f"Celestial Object Details:  Code: {object_code}  Name: {object_name}  RA: {ra}  DEC: {dec}")
    print(f"radec converted to alt and az:  ALT: {alt_converted}  AZ: {az_converted}")
    print(f"Altaz converted to ra and dec:  RA: {ra_converted}  DEC: {dec_converted}")
    print("\n")
    list_available_celestial_objects(ra, dec)

if __name__ == '__main__':
    main()