import Telescope_Movement as TM, time, requests, geocoder, astropy.units as u

from astropy.coordinates import SkyCoord, EarthLocation, AltAz, ICRS
from astropy.time import Time
from astroquery.ipac.ned import Ned

def get_location_and_elevation(method = 'stored'):
    latitude, longitude, elevation = None, None, None
    retries = 3
    delay = 3
    
    if method == 'ip':
        g = geocoder.ip('me')
        
        if g.ok:
            latitude, longitude = g.latlng
            
            # Retry mechanism for elevation API
            for attempt in range(retries):
                try:
                    response = requests.get(f'https://api.open-elevation.com/api/v1/lookup?locations={latitude},{longitude}')
                    response.raise_for_status()
                    
                    elevation_data = response.json()
                    if 'results' in elevation_data and len(elevation_data['results']) > 0:
                        elevation = elevation_data['results'][0]['elevation']
                        break
                    else:
                        print("No elevation data found in the response.")
                except requests.RequestException as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < retries - 1:
                        time.sleep(delay)  # Wait before retrying
            else:
                print("Failed to fetch elevation data after retries.")
        else:
            print("Error retrieving IP-based location.")
    else: # Stored values
        latitude, longitude, elevation = -26.7167, 27.1, 1100
    
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

# Display list of celestial object within a certain radius of a ra, dec coordinate
def list_available_celestial_objects(ra, dec, radius = 0.1):
    frame = 'icrs'

    try:
        ra_deg, dec_deg = convert_radec_to_degrees(ra, dec)
        icrs_coords = SkyCoord(ra_deg, dec_deg, frame=frame, unit='deg') 
        
        # Query NED for objects within the specified region
        result = Ned.query_region(icrs_coords, radius=radius * u.deg)
        
        # Check if results are found
        if result is not None and len(result) > 0:
            # Display the column names to understand the structure
            print("Available columns:", result.colnames)
            
            # Loop through the results and print relevant details
            for obj in result:
                # Use available columns from result
                name = obj.get('Object Name', 'Unknown')
                print(f"Name: {name}")
        else:
            print("No celestial objects found in the specified region.")
    except Exception as e:
        print(f"Error querying region: {e}")

# def list_available_celestial_objects(ra, dec, radius = 0.1):
#     frame = 'icrs'

#     try:
#         # Determine format and unit for RA/Dec
#         if isinstance(ra, (float, int)) and isinstance(dec, (float, int)): # Degree format
#             icrs_coords = SkyCoord(ra, dec, frame=frame, unit='deg') 
#         elif isinstance(ra, str) and isinstance(dec, str):
#             if "h" in ra or "d" in dec: # Sexagesimal format
#                 icrs_coords = SkyCoord(ra, dec, frame=frame) # Format like '00h42m30s' and '+41d12m00s'
#             else:
#                 icrs_coords = SkyCoord(ra, dec, frame=frame, unit=(u.hourangle, u.deg)) # Format like '00 42 30' and '+41 12 00', specify units explicitly
#         elif isinstance(ra, str) and dec is None:
#             icrs_coords = SkyCoord(ra, frame=frame, unit=(u.hourangle, u.deg)) # Single string input, e.g., '00:42.5 +41:12'
#         else:
#             raise ValueError("Unsupported RA/Dec format. Please provide RA and Dec in a supported format.")
        
#         # Query NED for objects within the specified region
#         result = Ned.query_region(icrs_coords, radius=radius * u.deg)
        
#         # Check if results are found
#         if result is not None and len(result) > 0:
#             # Display the column names to understand the structure
#             print("Available columns:", result.colnames)
            
#             # Loop through the results and print relevant details
#             for obj in result:
#                 # Use available columns from result
#                 name = obj.get('Object Name', 'Unknown')
#                 print(f"Name: {name}")
#         else:
#             print("No celestial objects found in the specified region.")
#     except Exception as e:
#         print(f"Error querying region: {e}")

def convert_altaz_to_radec(alt, az):
    now = Time.now()  # Get current time
    latitude, longitude, elevation = get_location_and_elevation()

    if latitude is None or longitude is None or elevation is None:
        raise ValueError("Could not retrieve location or elevation data.")

    observer_location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m)  # Define the observer's location
    altaz_frame = AltAz(obstime=now, location=observer_location)  # Define the AltAz frame

    altaz_coords = SkyCoord(alt=alt * u.deg, az=az * u.deg, frame=altaz_frame)  # Create an AltAz coordinate object
    icrs_coords = altaz_coords.transform_to(ICRS)  # Convert to ICRS (RA and Dec)

    return icrs_coords.ra.hourangle, icrs_coords.dec.degree

def convert_radec_to_degrees(ra, dec=None, frame='icrs'):
    # Determine format and unit for RA/Dec
    if isinstance(ra, (float, int)) and isinstance(dec, (float, int)): # Degree format
        icrs_coords = SkyCoord(ra, dec, frame=frame, unit='deg') 
    elif isinstance(ra, str) and isinstance(dec, str):
        if "h" in ra or "d" in dec: # Sexagesimal format
            icrs_coords = SkyCoord(ra, dec, frame=frame) # Format like '00h42m30s' and '+41d12m00s'
        else:
            icrs_coords = SkyCoord(ra, dec, frame=frame, unit=(u.hourangle, u.deg)) # Format like '00 42 30' and '+41 12 00', specify units explicitly
    elif isinstance(ra, str) and dec is None:
        icrs_coords = SkyCoord(ra, frame=frame, unit=(u.hourangle, u.deg)) # Single string input, e.g., '00:42.5 +41:12'
    else:
        raise ValueError("Unsupported RA/Dec format. Please provide RA and Dec in a supported format.")
    
    return icrs_coords.ra.degree, icrs_coords.dec.degree

def convert_radec_to_altaz(ra, dec):
    ra_deg, dec_deg = convert_radec_to_degrees(ra, dec)

    now = Time.now()  # Get current time
    latitude, longitude, elevation = get_location_and_elevation()

    if latitude is None or longitude is None or elevation is None:
        raise ValueError("Could not retrieve location or elevation data.")

    observer_location = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m)  # Define the observer's location
    icrs_coords = SkyCoord(ra_deg, dec_deg, frame='icrs', unit='deg')

    altaz_frame = AltAz(obstime=now, location=observer_location)  # Define the AltAz frame
    altaz_coords = icrs_coords.transform_to(altaz_frame)  # Convert to AltAz

    return altaz_coords.alt.degree, altaz_coords.az.degree

def __main__():
    latitude, longitude, elevation = get_location_and_elevation()
    object_code, object_name, ra, dec = get_celestial_object_details("M31") # Andromeda Galaxy
    alt_converted, az_converted = convert_radec_to_altaz(ra, dec)
    ra_converted, dec_converted = convert_altaz_to_radec(alt_converted, az_converted)

    print(f"Current Location:  Latitude: {latitude}  Longitude: {longitude}  Elevation: {elevation}")
    print(f"Celestial Object Details:  Code: {object_code}  Name: {object_name}  RA: {ra}  DEC: {dec}")
    print(f"radec converted to alt and az:  ALT: {alt_converted}  AZ: {az_converted}")
    print(f"Altaz converted to ra and dec:  RA: {ra_converted}  DEC: {dec_converted}")
    print("\n")
    list_available_celestial_objects(ra, dec)

if __name__ == '__main__':
    __main__()
