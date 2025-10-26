# Telescope Simulator – Pseudocode Documentation

This document summarises the core modules, key functions, and control flow of the Telescope Simulator in clear pseudocode, with references to the concrete implementation files and line numbers. Use it as a map to navigate the codebase and understand how the system pieces work together.

Note: File references are clickable and use 1-based line numbers.

## System Overview

- Main entry: `main.py` handles authentication, menu navigation, and orchestration of actions (move telescope, configure system, conversions, display, user/object management).
- Core services:
  - Configuration: `core/system_config.py` (JSON-backed config service)
  - Telescope control: `core/telescope_control.py` (CoppeliaSim remote API control)
  - Calculations: `core/calculations.py` (coordinate conversions, location, NED queries)
  - Logging: `core/file_handling.py`, `core/enhanced_logging.py` (MongoDB + file/console)
  - Display/Reporting: `core/data_display.py`, `core/display_menu.py`
  - Access control: `core/access_control.py`
  - System checks: `core/system_checks.py`
- Simulation interface: `simulation/sim_interface.py` (ctypes wrapper around CoppeliaSim remote API)
- Persistence (MongoDB): users, logs, and astronomical objects via `api/user_api.py`, `simulation/track_objects.py`.
- Auth/JWT: `users/middleware/auth.py` (token generation, verification, username/password check).

---

## main.py – Application Flow and Menus

Key data structures and roles

- Command descriptions map: `main.py:31`
- Menu options: `main.py:58`
- Menu enum: `main.py:108`

Authentication flow

File: `main.py:125`

Pseudocode:

```
def authenticate() -> Optional[dict]:
  define get_user_by_username(username) -> user from MongoDB (users_collection)
  for attempt in 1..3:
    prompt username, password (password via getpass)
    if user not found: inform and continue
    token, error = authenticate_user(username, password, get_user_by_username)
    if token:
      user = get_user_by_username(username)
      attach token to user and return
    else:
      show error; loop if attempts remain
  return None on failure
```

Menu dispatch – navigation and actions

File: `main.py:175`

Pseudocode:

```
def handle_menu_choice(current_menu, choice, user) -> Optional[Menu]:
  derive username, role from user
  if in MAIN:
    if choice maps to a submenu permitted for role -> return that Menu
    else if Exit -> return None
  elif in TELESCOPE:
    1 -> read alt, az (get_valid_alt_az), TM.move_tel, log
    2 -> read ra, dec (get_valid_ra_dec), convert to alt/az, TM.move_tel, log
    3 -> read celestial code, TM.track_celestial_object, log
    4 -> TM.telescope_rest, log
    5 -> go to OBJECTS submenu
    6 -> back to MAIN
    return TELESCOPE (stay)
  elif in CONFIG:
    dispatch to change_* and view_all_settings functions; stay in CONFIG unless Back
  elif in COORDS:
    conversions between Alt/Az and RA/Dec; stay unless Back
  elif in USER_MANAGEMENT:
    CRUD via api.user_api helpers; stay unless Back
  elif in DISPLAY:
    display menu manager (enhanced viewer), location/log listing, commands, objects, internet check; stay unless Back
  elif in OBJECT_MANAGEMENT:
    CRUD for celestial objects (simulation/track_objects); stay unless Back
  elif in OBJECTS:
    render objects, prompt selection, convert RA/Dec to Alt/Az, move telescope
  return current or next menu
```

Input validation helpers

- `get_valid_alt_az`, `alt_az_input_validation`: `main.py:420` → clamp and ensure ranges vs config
- `get_valid_ra_dec`, `ra_dec_input_validation`: `main.py:508`
- `get_valid_celestial_code`, `celestial_code_input_validation`: `main.py:520`

Configuration editing flows

- Change location: `main.py:510`
  - Prompt lat/lon/elev with range checks → set keys on `config` → `config.save()` → log
- Change movement settings: `main.py:560`
  - timeout, tolerance, clamp/invert/clockwise flags → save → log
- Change safety settings: `main.py:640`
  - prevent_below_horizon, safety margins → save → log
- Change simulation settings: `main.py:682`
  - joint names, forces, ping, background/headless flags → save → log
- View all settings: `main.py:720`
  - Render grouped sections from `config` and log
- Change telescope limits: `main.py:756`
  - Read/validate alt/az min/max; store to config; log

Display functions (quick)

- Location: `main.py:851`
- Telescope logs (file tail): `main.py:894`
- All commands list: `main.py:910`
- Available celestial objects (NED region query): `main.py:916`

Object management wrappers

- create/list/update/delete object (interactive): `main.py:927`, `main.py:960`, `main.py:980`, `main.py:1025`
  - Delegate to `simulation.track_objects` service functions and log

Main loop and bootstrap

File: `main.py:1065`

Pseudocode:

```
def main():
  initialize required default config keys if missing; config.save()
  user = authenticate(); if not user: exit
  current_menu = Menu.MAIN
  while current_menu is not None:
    render menu for role; prompt numeric choice
    next_menu = handle_menu_choice(current_menu, choice, user)
    current_menu = next_menu
  TM.close()  # close sim connection
```

---

## core/system_config.py – Configuration Service

File: `core/system_config.py:8`

Pseudocode:

```
class AppConfig:
  on init: set config_file (Resources/config.json), load JSON as _data
  get(key, default): return _data.get(key, default)
  has(key): key in _data
  set(key, value): _data[key] = value; _save_config()
  save(): _save_config()
  reload(): _data = _load_config()
  update(key, value): alias of set
  _load_config(): read JSON; return {} on missing/invalid
  _save_config(): ensure dir; write JSON with indent
  validate(): ensure required keys present

config = AppConfig()  # global singleton
```

---

## core/file_handling.py – Basic Logging + FS Helpers

Functions: `init_mongodb` `write_log` `display_logs`

- MongoDB bootstrap: `core/file_handling.py:21`
  - Create client, test `ismaster`, select DB/collection `Logs`, index on `timestamp`.
  - Degrade gracefully by leaving collection `None` if unavailable.
- Write log: `core/file_handling.py:80`
  - Validate `level` in {success,error,warning}
  - If MongoDB unavailable → print to console for admin only; else insert document
- Display logs: `core/file_handling.py:110`
  - Fetch recent 100, group by level, render in table via `tabulate`

---

## core/enhanced_logging.py – Advanced Logger

File: `core/enhanced_logging.py:1`

Pseudocode:

```
class EnhancedLogger:
  _init_mongodb(): connect, set collection 'enhanced_logs', add indexes
  _init_file_logging(): rotating file handler logs/telescope.log
  _init_console_logging(): console handler for warn+ levels
  log(level, category, message, user=None, command=None, extra=None, exc=None):
    build structured log_entry; write to MongoDB, file, and console (per level)
  convenience methods: log_auth, log_telescope, log_user_mgmt, log_security, log_system

logger = EnhancedLogger()

# Backward-compatible functions map to EnhancedLogger
write_log(user, command, level, description)
...
```

---

## core/telescope_control.py – Telescope Motion + Tracking

Key constants read from `config` at import time. Limits are dynamically retrieved via helpers.

Connection management

- `test_con()`: `core/telescope_control.py:62`
  - Ensure remote API library loaded; connect to CoppeliaSim via `sim.simxStart`; set global `clientID` and reset first-movement flag.

Limits and safety

- `check_limits(alt, az)`: `core/telescope_control.py:90` → compare with configured altitude/azimuth bounds.
- `_effective_limits`, `_clamp_to_limits`: compute margins with safety offsets and horizon prevention.

Read joint position (ctypes)

- `get_current_joint_position(handle)`: `core/telescope_control.py:123`
- `wait_for_joint_position(handle, target)`: `core/telescope_control.py:144` waits until within `POSITION_TOLERANCE` or timeout.

Move telescope

File: `core/telescope_control.py:161`

Pseudocode:

```
def move_tel(alt, az, current_user=None):
  if outside limits or alt < 0: print warning; write warning log; return
  ensure connection (test_con)
  get joint handles for base/elevation
  enable motors/controllers; set max forces (boost at low altitude)
  if INVERT_ELEVATION_AXIS: map user alt → CoppeliaSim angle (90-alt), else use alt
  compute azimuth move:
    - on first move (and FORCE_FIRST_CLOCKWISE): force clockwise direction
    - else compute shortest path sign/direction, convert to Coppelia coords
  start simulation; send target positions; wait until reached
  log success or timeout
```

Rest mode

- `telescope_rest(username, current_user)`: `core/telescope_control.py:287`
  - Compute safe Alt/Az nearest bounds; map to sim coordinates; set targets; wait; log.

Tracking loop

- `track_celestial_object(code, current_user)`: `core/telescope_control.py:392`
  - Foreground or background thread (config) that periodically:
    - Pull RA/Dec via `core.calculations.get_celestial_object_details`
    - Convert to Alt/Az; check limits; move
    - Stop on key press `q` (if interactive) or event; park at rest

Shutdown

- `close()`: `core/telescope_control.py:415` → stop simulation and finish connection.

---

## simulation/sim_interface.py – CoppeliaSim Remote API Wrapper

Highlights:

- Library loader: `_load_libsimx()` attempts to load `remoteApi.(dll|so|dylib)` from `simulation/` directory; prints guidance on failure.
- Exposes ctypes-bound functions used by control module, e.g.:
  - `simxGetJointPosition`: `simulation/sim_interface.py:286`
  - `simxSetJointTargetPosition`: `simulation/sim_interface.py:327`
  - `simxGetObjectHandle`: `simulation/sim_interface.py:416`
  - `simxStart`: `simulation/sim_interface.py:1359`
  - `simxFinish`: `simulation/sim_interface.py:1368`
  - `simxGetConnectionId`: `simulation/sim_interface.py:1424`

---

## core/calculations.py – Coordinates, Location, NED Queries

Location retrieval

- `get_location_and_elevation(method='stored')`: `core/calculations.py:14`
  - If `ip`: geolocate via `geocoder.ip('me')` and fetch elevation via open-elevation API with retries; else use `config` values.

NED lookup

- `get_celestial_object_details(code)`: `core/calculations.py:61` → returns `(code, name, ra, dec)` using `astroquery.ipac.ned.Ned`.
- `list_available_celestial_objects(ra, dec, radius)`: `core/calculations.py:82` → prints names within radius of given RA/Dec.

Conversions

- `convert_altaz_to_radec(alt, az)`: `core/calculations.py:100`
  - Build `AltAz` frame for current time and location; transform to ICRS; return RA (hours), Dec (deg).
- `convert_radec_to_degrees(ra, dec)`: `core/calculations.py:122` → normalize multiple formats to degrees.
- `convert_radec_to_altaz(ra, dec)`: `core/calculations.py:144`
  - Build ICRS, transform to `AltAz` frame for current time and location; return Alt/Az degrees.

---

## core/display_menu.py – Enhanced Display Navigation

Class: `DisplayMenuManager` `core/display_menu.py:14`

Pseudocode for main menu:

```
def show_display_options_menu(user):
  loop:
    render options (telescope data, logs, user activity, objects, status, config, filters, export, quick reports)
    read choice → dispatch to _view_* or _configure_* or _set_data_filters
    allow back to main
```

Each `_view_*` gets a format choice, pulls data via `core.data_display.DataDisplayManager`, prints, optionally saves exports.

---

## core/data_display.py – Data Retrieval and Formatting

Class: `DataDisplayManager` `core/data_display.py:39`

Key responsibilities:

- `_init_mongodb`: connect to MongoDB and store DB handle.
- `_load_display_config`/`save_display_config`: manage `Resources/display_config.json` with defaults.
- Retrieval methods (apply filters and permissions via `core.access_control`):
  - `display_telescope_data`: `core/data_display.py:128` → from Mongo logs.
  - `display_system_logs`: `core/data_display.py:171`
  - `display_user_activity`: `core/data_display.py:217` → aggregation pipeline summary.
  - `display_celestial_objects`: `core/data_display.py:277`
  - `display_system_status`: `core/data_display.py:323` → derived system metrics.
- `_format_data`: `core/data_display.py:366` → table/JSON/CSV/etc.
- `export_data`: `core/data_display.py:477` → write formatted output to file with permission checks.

---

## core/access_control.py – Role-Based Access and Filters

Class: `AccessControlManager`

Highlights:

- Loads/merges `Resources/access_control.json` defaults on init.
- Permission checks: `check_permission(user, data_type, action)` `core/access_control.py:145` → validate role allowed_data/actions, log attempt.
- Export size limits: `check_export_permission` `core/access_control.py:189`
- Timeframe limits: `check_timeframe_permission` `core/access_control.py:213`
- Data redaction: `filter_data_by_permissions` `core/access_control.py:229` → redact user/config fields for operators.

---

## users/middleware/auth.py – JWT + Password Verification

Auth helpers:

- `generate_jwt(user_id)`: `users/middleware/auth.py:25` → HS256, expiry from env.
- `verify_jwt(token)`: `users/middleware/auth.py:38`
- `token_required(f)`: `users/middleware/auth.py:52` → Flask decorator.
- `authenticate_user(username, password, getUsername)`: `users/middleware/auth.py:78`
  - Fetch user; verify Werkzeug password hash with legacy plaintext fallback; produce JWT on success.

---

## api/user_api.py – User CRUD (Service + Interactive)

Mongo bootstrap to `users` collection.

Service methods (non-interactive):

- `create_user_service`: `api/user_api.py:27` → validate role, unique username, hash password.
- `list_users_service`: `api/user_api.py:48`
- `update_user_service`: `api/user_api.py:53`
- `delete_user_service`: `api/user_api.py:75`

Interactive wrappers (used by `main.py`):

- `create_user`: `api/user_api.py:85`
- `list_users`: `api/user_api.py:116`
- `update_user`: `api/user_api.py:133`
- `delete_user`: `api/user_api.py:168`

---

## simulation/track_objects.py – Celestial Object Storage

Collection: `astronomical_objects`.

Functions:

- `create_object(user_id, name, description, ra_dec, ned_code)`: `simulation/track_objects.py:32`
- `list_objects(user_id=None, role='operator', show_all=False)`: `simulation/track_objects.py:56`
- `update_object(name, description=None, ra_dec=None, ned_code=None, user_id=None, role='operator')`: `simulation/track_objects.py:78`
- `delete_object(name, user_id=None, role='operator')`: `simulation/track_objects.py:105`
- `track_object(user_id, object_id)`: `simulation/track_objects.py:121`

Pseudocode for update/delete filtering:

```
filter_query = { name }
if role != 'admin' and user_id provided:
  filter_query.user_id = user_id
perform update/delete accordingly
```

---

## core/system_checks.py – Network Check

- `check_internet_connection(host, port, timeout)`: `core/system_checks.py:8` → socket connect to 8.8.8.8:53; return status dataclass.

---

## Data Flow Summary

- User starts app → `main.main()` initializes config defaults, calls `authenticate()`.
- Menus in `main.py` route to:
  - Telescope moves/tracking → `core.telescope_control` which talks to CoppeliaSim via `simulation.sim_interface`.
  - Conversions/lookups → `core.calculations` which may call external services (`astroquery`, `open-elevation`).
  - Logging → `core.file_handling` and/or `core.enhanced_logging` to MongoDB/console/file.
  - Display/reporting → `core.display_menu` → `core.data_display` with `core.access_control` enforcing permissions.
  - Users/Objects → `api.user_api` / `simulation.track_objects` backed by MongoDB.

---

## Operational Notes

- Env vars in `.env` are required for DB and JWT: see `docs/README.md`.
- If MongoDB is down, most modules degrade gracefully (print-only or access denied messages).
- CoppeliaSim remote API binary must be present in `simulation/` (`remoteApi.dll/.so/.dylib`).

---

## Quick Pseudocode Snippets for Common Tasks

Move telescope to RA/Dec (from main menu)

```
user picks RA/Dec → C.convert_radec_to_altaz(ra, dec) → TM.move_tel(alt, az)
```

Track object by code

```
loop every PING: (code → name, ra, dec) → alt, az → if within limits: move; else rest and stop
```

Update telescope limits

```
read alt_min, alt_max, az_min, az_max → validate ranges and ordering → config.set and save
```

