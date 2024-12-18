# Telescope-Simulator Project

## Table of Contents
- [Project Description](#project-description)
- [Features](#features)
- [Simulation Setup](#simulation-setup)
  - [CoppeliaSim Installation](#coppeliasim-installation)
  - [Python Dependencies](#python-dependencies)
  - [CoppeliaSim Scene Setup](#coppeliasim-scene-setup)
- [Limitations](#limitations)
- [License](#license)

## Project Description
The Telescope-Simulator project is a Python-based software designed for use at the Nooitgedacht farm by the NWU. The software aims to simulate telescope operations and assist in celestial observations. With four telescopes and a central control building, the Nooitgedacht farm lacks dedicated software, making this project critical. It serves as a hands-on tool for computer science and physics students, allowing them to work with telescope simulation software and conduct research.

The program can convert altitude and azimuth degrees to right ascension (RA) and declination (Dec) values. It features customizable settings and automatic tracking of celestial objects using an online database. The software is designed to be scalable and modular, making it adaptable to future expansions and improvements.

## Features
- **RA/Dec Conversion**: Converts altitude and azimuth (alt/az) degrees to right ascension (RA) and declination (Dec) values.
- **Celestial Object Tracking**: Tracks celestial objects automatically using an online database of RA and Dec values.
- **Object Listing**: Lists available celestial objects within a specified radius of a given RA and Dec coordinate.
- **Modular and Scalable**: The software is designed to be easily expanded and adapted to future needs.
- **CLI-Based**: A command-line interface (CLI) provides control over telescope operations and simulations.
- **Built-In Simulation**: Integrates with CoppeliaSim for simulating telescope movement and celestial observations.

## Simulation Setup

### CoppeliaSim Installation
1. Download CoppeliaSim Edu from the official website: [CoppeliaSim](https://www.coppeliarobotics.com/).
2. Start CoppeliaSim by running the `coppeliaSim.sh` file (for Ubuntu 20.04).

### Python Dependencies
To set up the environment, install the required Python dependencies:
```bash
pip install pyzmq cbor2
### CoppeliaSim Scene Setup
1. In CoppeliaSim Edu, navigate to **File → Open scene...**.
2. Open the `Radio Telescope Scene.ttt` file located in the `Virtual-Prototype-Scene-and-Documentation` folder of the GitHub repository.
3. Press the play button in CoppeliaSim Edu to begin the simulation.
4. Run the radio telescope orientation software and watch the virtual telescope prototype move during celestial observations.

*Note*: You may need to run `sudo su` in the terminal before launching the radio telescope orientation software.

For setting up communication between Python and CoppeliaSim, refer to this [YouTube video](https://www.youtube.com/watch?v=SQont-mTnfM&t=588s) for detailed instructions. The required files are located in the `programming > legacyRemoteApi > remoteApiBindings` directory. For Ubuntu 20.04, the necessary file is `remoteApi.so`.

### Limitations
- **Simulation Environment**: The simulation is limited to the scope of the virtual prototype and may not represent real-world telescope behavior in all scenarios.
- **Dependency Issues**: Some dependencies might not be fully documented, and users may need to troubleshoot setup issues.

### License
This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
